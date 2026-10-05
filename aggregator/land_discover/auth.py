"""Database-backed accounts and opaque, revocable HttpOnly sessions."""
import hashlib
import hmac
import os
import re
import secrets
import smtplib
import sqlite3
import time
import threading
from email.message import EmailMessage
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from .db import connect, now

router=APIRouter(prefix='/api/auth',tags=['Authentication'])
COOKIE='land_discover_session'
N=2**17
_password_slots=threading.BoundedSemaphore(2)

def password_key(password,salt):
    # Each scrypt operation uses about 128 MiB. Bound concurrent hashing on
    # the prototype backend so several sign-ins cannot exhaust its memory.
    with _password_slots:
        return hashlib.scrypt(password.encode(),salt=salt,n=N,r=8,p=1,dklen=32,maxmem=256*1024*1024)

def digest(value): return hashlib.sha256(value.encode()).hexdigest()

def hash_password(password):
    salt=secrets.token_bytes(16)
    key=password_key(password,salt)
    return 'scrypt$'+salt.hex()+'$'+key.hex()

def verify_password(password,encoded):
    try:
        scheme,salt,key=encoded.split('$')
        if scheme!='scrypt': return False
        actual=password_key(password,bytes.fromhex(salt))
        return hmac.compare_digest(actual,bytes.fromhex(key))
    except (ValueError,TypeError): return False

class Credentials(BaseModel):
    email: str = Field(min_length=3,max_length=254)
    password: str = Field(min_length=1,max_length=128)
    remember: bool = False

    @field_validator('email')
    @classmethod
    def email_address(cls,value):
        value=value.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value): raise ValueError('Enter a valid email address')
        return value

class Registration(Credentials):
    password: str = Field(min_length=8,max_length=128)
    display_name: str = Field(default='',max_length=120)

class EmailRequest(BaseModel):
    email: str = Field(min_length=3,max_length=254)
    _normalize=field_validator('email')(Credentials.email_address.__func__)

class ResetRequest(BaseModel):
    token: str = Field(min_length=20,max_length=200)
    password: str = Field(min_length=8,max_length=128)

def check_origin(request):
    from .hosting import trusted_proxy
    allowed={v.strip().rstrip('/') for v in os.getenv('LAND_AUTH_ORIGINS','http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000').split(',')}
    origin=request.headers.get('origin')
    if trusted_proxy(request):
        frontend=request.headers.get('x-land-frontend-origin','')
        if frontend.startswith('https://') and origin==frontend: allowed.add(frontend)
    if origin and origin.rstrip('/') not in allowed:
        raise HTTPException(403,'This sign-in request came from an untrusted website')
    if request.headers.get('sec-fetch-site')=='cross-site': raise HTTPException(403,'Cross-site authentication request refused')

def throttle(request,email=''):
    from .hosting import trusted_proxy
    stamp=time.time()
    client=request.client.host if request.client else 'unknown'
    if trusted_proxy(request) and request.headers.get('x-land-client-ip'):
        client=request.headers['x-land-client-ip'].split(',')[0].strip()
    keys=[('ip:'+digest(client),60)]
    if email: keys.append(('email:'+digest(email),10))
    blocked=False
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        con.execute('DELETE FROM auth_attempts WHERE started_at<?',(stamp-900,))
        for key,maximum in keys:
            row=con.execute('SELECT attempts FROM auth_attempts WHERE key=?',(key,)).fetchone()
            if row and row['attempts']>=maximum: blocked=True
        if not blocked:
            for key,_ in keys:
                con.execute('INSERT INTO auth_attempts VALUES (?,?,1) ON CONFLICT(key) DO UPDATE SET attempts=attempts+1',(key,stamp))
    if blocked: raise HTTPException(429,'Too many attempts. Try again in 15 minutes.',headers={'Retry-After':'900'})

def public_user(row):
    return {key:row[key] for key in ('id','email','display_name','created_at','last_login_at')}

def require_user(request:Request):
    token=request.cookies.get(COOKIE,'')
    if not token or len(token)>200: raise HTTPException(401,'Please sign in to continue')
    with connect() as con:
        row=con.execute('SELECT u.* FROM user_sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?',(digest(token),time.time())).fetchone()
    if not row: raise HTTPException(401,'Your session has expired. Please sign in again')
    return public_user(row)

def session(request,response,user_id,remember):
    token=secrets.token_urlsafe(32)
    lifetime=30*86400 if remember else 12*3600
    with connect() as con:
        con.execute('DELETE FROM user_sessions WHERE expires_at<=?',(time.time(),))
        old=request.cookies.get(COOKIE)
        if old: con.execute('DELETE FROM user_sessions WHERE token_hash=?',(digest(old),))
        con.execute('INSERT INTO user_sessions VALUES (?,?,?,?)',(digest(token),user_id,now(),time.time()+lifetime))
        con.execute('UPDATE users SET last_login_at=? WHERE id=?',(now(),user_id))
        user=con.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
    secure=os.getenv('LAND_AUTH_SECURE_COOKIE','false').lower()=='true' or request.url.scheme=='https'
    response.set_cookie(COOKIE,token,max_age=lifetime if remember else None,httponly=True,secure=secure,samesite='lax',path='/')
    response.headers['Cache-Control']='no-store'
    return {'user':public_user(user)}

@router.post('/register',status_code=201)
def register(body:Registration,request:Request,response:Response):
    check_origin(request); throttle(request,body.email)
    encoded=hash_password(body.password)
    try:
        with connect() as con:
            user_id=con.execute('INSERT INTO users(email,display_name,password_hash,created_at) VALUES (?,?,?,?)',(body.email,body.display_name.strip(),encoded,now())).lastrowid
    except sqlite3.IntegrityError: raise HTTPException(409,'An account with this email already exists. Please sign in.')
    return session(request,response,user_id,body.remember)

@router.post('/login')
def login(body:Credentials,request:Request,response:Response):
    check_origin(request); throttle(request,body.email)
    with connect() as con: user=con.execute('SELECT * FROM users WHERE email=?',(body.email,)).fetchone()
    # Run the same KDF for unknown accounts to avoid a fast timing oracle.
    encoded=user['password_hash'] if user else 'scrypt$'+'00'*16+'$'+'00'*32
    valid=verify_password(body.password,encoded)
    if not user or not valid: raise HTTPException(401,'Your email or password is incorrect. Please try again.')
    return session(request,response,user['id'],body.remember)

@router.get('/me')
def me(response:Response,user=Depends(require_user)):
    response.headers['Cache-Control']='no-store'
    return {'user':user}

@router.post('/logout',status_code=204)
def logout(request:Request,response:Response):
    check_origin(request)
    token=request.cookies.get(COOKIE)
    if token:
        with connect() as con: con.execute('DELETE FROM user_sessions WHERE token_hash=?',(digest(token),))
    response.delete_cookie(COOKIE,path='/',httponly=True,samesite='lax')
    response.headers['Cache-Control']='no-store'

def reset_available():
    return bool(os.getenv('LAND_SMTP_HOST') and os.getenv('LAND_MAIL_FROM'))

@router.get('/config')
def config(): return {'password_reset_available':reset_available()}

def send_reset(email,token):
    origin=os.getenv('LAND_PUBLIC_URL','http://127.0.0.1:5173').rstrip('/')
    message=EmailMessage()
    message['Subject']='Reset your Land Discover password'
    message['From']=os.environ['LAND_MAIL_FROM']; message['To']=email
    message.set_content(f'Reset your password using this link within 15 minutes:\n{origin}/login?reset_token={token}\n\nIf you did not request this, ignore this email.')
    with smtplib.SMTP(os.environ['LAND_SMTP_HOST'],int(os.getenv('LAND_SMTP_PORT','587')),timeout=15) as smtp:
        smtp.starttls()
        if os.getenv('LAND_SMTP_USER'): smtp.login(os.environ['LAND_SMTP_USER'],os.getenv('LAND_SMTP_PASSWORD',''))
        smtp.send_message(message)

@router.post('/forgot-password')
def forgot_password(body:EmailRequest,request:Request):
    check_origin(request); throttle(request,body.email)
    if not reset_available(): raise HTTPException(503,'Password reset email is not configured yet')
    with connect() as con:
        user=con.execute('SELECT id FROM users WHERE email=?',(body.email,)).fetchone()
        if user:
            token=secrets.token_urlsafe(32)
            con.execute('DELETE FROM password_resets WHERE user_id=? OR expires_at<=?',(user['id'],time.time()))
            con.execute('INSERT INTO password_resets VALUES (?,?,?)',(digest(token),user['id'],time.time()+900))
    if user:
        try: send_reset(body.email,token)
        except (OSError,smtplib.SMTPException):
            with connect() as con: con.execute('DELETE FROM password_resets WHERE token_hash=?',(digest(token),))
            # Match the unknown-account response; do not expose mail failures
            # as an account enumeration channel.
    return {'message':'If an account exists with this email, you will receive a password reset link.'}

@router.post('/reset-password')
def reset_password(body:ResetRequest,request:Request):
    check_origin(request); throttle(request)
    encoded=hash_password(body.password)
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        reset=con.execute('SELECT user_id FROM password_resets WHERE token_hash=? AND expires_at>?',(digest(body.token),time.time())).fetchone()
        if not reset: raise HTTPException(400,'This reset link is invalid or expired. Request a new link.')
        con.execute('UPDATE users SET password_hash=? WHERE id=?',(encoded,reset['user_id']))
        con.execute('DELETE FROM password_resets WHERE user_id=?',(reset['user_id'],))
        con.execute('DELETE FROM user_sessions WHERE user_id=?',(reset['user_id'],))
    return {'message':'Password updated. You can now sign in.'}
