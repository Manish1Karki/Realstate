import time
import pytest
from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.auth import COOKIE, digest, hash_password, verify_password
from land_discover.db import connect

ACCOUNT={'email':'Person@Example.org','password':'a secure test password','display_name':'Test Person'}

def test_signup_persists_hash_and_session_and_logout_revokes():
    with TestClient(app) as client:
        assert client.get('/api/auth/me').status_code==401
        response=client.post('/api/auth/register',json=ACCOUNT)
        assert response.status_code==201
        assert response.json()['user']['email']=='person@example.org'
        assert response.json()['user']['display_name']=='Test Person'
        assert 'password_hash' not in response.text
        assert 'HttpOnly' in response.headers['set-cookie'] and 'SameSite=lax' in response.headers['set-cookie']
        assert 'Max-Age' not in response.headers['set-cookie']
        token=client.cookies.get(COOKIE)
        with connect() as con:
            user=con.execute('SELECT * FROM users').fetchone()
            assert user['password_hash']!=ACCOUNT['password']
            assert verify_password(ACCOUNT['password'],user['password_hash'])
            stored=con.execute('SELECT token_hash FROM user_sessions').fetchone()[0]
            assert stored==digest(token) and stored!=token
        assert client.get('/api/auth/me').status_code==200
    # Session remains usable across backend lifespans (no in-memory secret).
    with TestClient(app) as client:
        client.cookies.set(COOKIE,token)
        assert client.get('/api/auth/me').status_code==200
        assert client.post('/api/auth/logout').status_code==204
        client.cookies.set(COOKIE,token)
        assert client.get('/api/auth/me').status_code==401

def test_login_wrong_password_unknown_account_and_remember():
    with TestClient(app) as client:
        client.post('/api/auth/register',json=ACCOUNT)
        assert client.post('/api/auth/login',json={**ACCOUNT,'password':'incorrect'}).status_code==401
        assert client.post('/api/auth/login',json={**ACCOUNT,'email':'unknown@example.org'}).status_code==401
        response=client.post('/api/auth/login',json={**ACCOUNT,'remember':True})
        assert response.status_code==200 and 'Max-Age=2592000' in response.headers['set-cookie']
        assert response.json()['user']['last_login_at']

def test_duplicate_email_and_password_validation():
    with TestClient(app) as client:
        assert client.post('/api/auth/register',json={**ACCOUNT,'password':'short'}).status_code==422
        assert client.post('/api/auth/register',json={**ACCOUNT,'email':'invalid-email'}).status_code==422
        assert client.post('/api/auth/register',json=ACCOUNT).status_code==201
        assert client.post('/api/auth/register',json={**ACCOUNT,'email':' PERSON@example.org '}).status_code==409
    with connect() as con: assert con.execute('SELECT COUNT(*) FROM users').fetchone()[0]==1

def test_expired_and_forged_sessions():
    with TestClient(app) as client:
        client.post('/api/auth/register',json=ACCOUNT)
        with connect() as con: con.execute('UPDATE user_sessions SET expires_at=?',(time.time()-1,))
        assert client.get('/api/auth/me').status_code==401
        client.cookies.clear();client.cookies.set(COOKIE,'forged-token')
        assert client.get('/api/auth/me').status_code==401

def test_cross_origin_authentication_blocked():
    with TestClient(app) as client:
        assert client.post('/api/auth/register',json=ACCOUNT,headers={'Origin':'https://evil.example.org'}).status_code==403
        assert client.post('/api/auth/register',json=ACCOUNT,headers={'Origin':'http://127.0.0.1:5173'}).status_code==201
        assert client.post('/api/auth/logout',headers={'Origin':'https://evil.example.org'}).status_code==403
        assert client.get('/api/auth/me').status_code==200

def test_login_rate_limit():
    with connect() as con:
        con.execute('INSERT INTO auth_attempts VALUES (?,?,?)',('email:'+digest('person@example.org'),time.time(),10))
    with TestClient(app) as client:
        response=client.post('/api/auth/login',json=ACCOUNT)
        assert response.status_code==429 and response.headers['retry-after']=='900'

def test_password_reset_is_single_use_and_revokes_sessions(monkeypatch):
    sent=[]
    monkeypatch.setenv('LAND_SMTP_HOST','smtp.example.org')
    monkeypatch.setenv('LAND_MAIL_FROM','noreply@example.org')
    monkeypatch.setattr('land_discover.auth.send_reset',lambda email,token: sent.append((email,token)))
    with TestClient(app) as client:
        client.post('/api/auth/register',json=ACCOUNT)
        assert client.get('/api/auth/config').json()['password_reset_available']
        known=client.post('/api/auth/forgot-password',json={'email':ACCOUNT['email']})
        unknown=client.post('/api/auth/forgot-password',json={'email':'missing@example.org'})
        assert known.json()==unknown.json() and len(sent)==1
        token=sent[0][1]
        with connect() as con: assert con.execute('SELECT token_hash FROM password_resets').fetchone()[0]!=token
        body={'token':token,'password':'new secure password'}
        assert client.post('/api/auth/reset-password',json=body).status_code==200
        assert client.get('/api/auth/me').status_code==401
        assert client.post('/api/auth/reset-password',json=body).status_code==400
        assert client.post('/api/auth/login',json=ACCOUNT).status_code==401
        assert client.post('/api/auth/login',json={**ACCOUNT,'password':body['password']}).status_code==200

def test_passwords_are_individually_salted():
    first=hash_password(ACCOUNT['password']);second=hash_password(ACCOUNT['password'])
    assert first!=second and verify_password(ACCOUNT['password'],first)
    assert not verify_password('wrong',second)

def test_https_secure_cookie(monkeypatch):
    monkeypatch.setenv('LAND_AUTH_SECURE_COOKIE','true')
    with TestClient(app) as client:
        response=client.post('/api/auth/register',json=ACCOUNT)
        assert 'Secure' in response.headers['set-cookie']
