"""Database-backed accounts and opaque, revocable HttpOnly sessions."""
import hashlib
import hmac
import ipaddress
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

class LocalResetRequest(EmailRequest):
    password: str = Field(min_length=8,max_length=128)

class ResetRequest(BaseModel):
    token: str = Field(min_length=20,max_length=200)
    password: str = Field(min_length=8,max_length=128)

class TokenRequest(BaseModel):
    token: str = Field(min_length=20,max_length=200)

class ProfileUpdate(BaseModel):
    display_name: str = Field(default='',max_length=120)
    phone_number: str = Field(default='',max_length=32)
    alternate_phone: str = Field(default='',max_length=32)

    @field_validator('display_name')
    @classmethod
    def clean_name(cls,value): return value.strip()

    @field_validator('phone_number','alternate_phone')
    @classmethod
    def phone_format(cls,value):
        value=value.strip()
        if value and not re.fullmatch(r'[+\d().\-\s]{5,32}',value): raise ValueError('Enter a valid phone number')
        return value

class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1,max_length=128)
    new_password: str = Field(min_length=8,max_length=128)

class EmailChangeRequest(BaseModel):
    email: str = Field(min_length=3,max_length=254)
    current_password: str = Field(min_length=1,max_length=128)

    @field_validator('email')
    @classmethod
    def email_address(cls,value):
        value=value.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value): raise ValueError('Enter a valid email address')
        return value

def check_origin(request):
    from .hosting import trusted_proxy
    allowed={v.strip().rstrip('/') for v in os.getenv('LAND_AUTH_ORIGINS','http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000').split(',')}
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
    return {key:row[key] for key in ('id','email','display_name','phone_number','alternate_phone','created_at','last_login_at')}

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

@router.patch('/me')
def update_profile(body:ProfileUpdate,request:Request,user=Depends(require_user)):
    check_origin(request)
    with connect() as con:
        con.execute('UPDATE users SET display_name=?,phone_number=?,alternate_phone=? WHERE id=?',
                    (body.display_name,body.phone_number,body.alternate_phone,user['id']))
        updated=con.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone()
    return {'user':public_user(updated),'message':'Profile updated.'}

@router.post('/change-password')
def change_password(body:PasswordChange,request:Request,user=Depends(require_user)):
    check_origin(request); throttle(request,user['email'])
    with connect() as con:
        current=con.execute('SELECT password_hash FROM users WHERE id=?',(user['id'],)).fetchone()
    if not current or not verify_password(body.current_password,current['password_hash']):
        raise HTTPException(401,'Your current password is incorrect.')
    encoded=hash_password(body.new_password)
    token=request.cookies.get(COOKIE,'')
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        con.execute('UPDATE users SET password_hash=? WHERE id=?',(encoded,user['id']))
        con.execute('DELETE FROM user_sessions WHERE user_id=? AND token_hash<>?',(user['id'],digest(token)))
        con.execute('DELETE FROM password_resets WHERE user_id=?',(user['id'],))
        con.execute('DELETE FROM email_changes WHERE user_id=?',(user['id'],))
    return {'message':'Password changed. Other signed-in sessions have been ended.'}

def send_email(to_address,subject,body):
    message=EmailMessage()
    message['Subject']=subject
    message['From']=os.environ['LAND_MAIL_FROM']; message['To']=to_address
    message.set_content(body)
    with smtplib.SMTP(os.environ['LAND_SMTP_HOST'],int(os.getenv('LAND_SMTP_PORT','587')),timeout=15) as smtp:
        smtp.starttls()
        if os.getenv('LAND_SMTP_USER'): smtp.login(os.environ['LAND_SMTP_USER'],os.getenv('LAND_SMTP_PASSWORD',''))
        smtp.send_message(message)

@router.post('/request-email-change')
def request_email_change(body:EmailChangeRequest,request:Request,user=Depends(require_user)):
    check_origin(request); throttle(request,body.email)
    if not reset_available(): raise HTTPException(503,'Email verification is not configured yet')
    with connect() as con:
        row=con.execute('SELECT password_hash,email FROM users WHERE id=?',(user['id'],)).fetchone()
        if not verify_password(body.current_password,row['password_hash']):
            raise HTTPException(401,'Your current password is incorrect.')
        if body.email==row['email']:
            raise HTTPException(400,'That is already the email address on your account.')
        if con.execute('SELECT 1 FROM users WHERE email=?',(body.email,)).fetchone():
            raise HTTPException(409,'An account with that email already exists.')
        token=secrets.token_urlsafe(32)
        con.execute('DELETE FROM email_changes WHERE user_id=? OR expires_at<=?',(user['id'],time.time()))
        con.execute('INSERT INTO email_changes VALUES (?,?,?,?)',(digest(token),user['id'],body.email,time.time()+1800))
    origin=os.getenv('LAND_PUBLIC_URL','http://127.0.0.1:3000').rstrip('/')
    try:
        send_email(body.email,'Confirm your Land Discover email address',
                   f'Confirm this email address for your Land Discover account within 30 minutes:\n{origin}/dashboard?verify_email={token}\n\nIf you did not request this, ignore this email.')
    except (OSError,smtplib.SMTPException):
        with connect() as con: con.execute('DELETE FROM email_changes WHERE token_hash=?',(digest(token),))
        raise HTTPException(503,'We could not send the verification email. Please try again later.')
    return {'message':'A verification link has been sent to your new email address.'}

@router.post('/confirm-email')
def confirm_email(body:TokenRequest,request:Request):
    check_origin(request); throttle(request)
    try:
        with connect() as con:
            con.execute('BEGIN IMMEDIATE')
            pending=con.execute('SELECT user_id,new_email FROM email_changes WHERE token_hash=? AND expires_at>?',(digest(body.token),time.time())).fetchone()
            if not pending: raise HTTPException(400,'This verification link is invalid or expired. Request a new one.')
            con.execute('UPDATE users SET email=? WHERE id=?',(pending['new_email'],pending['user_id']))
            con.execute('DELETE FROM email_changes WHERE user_id=?',(pending['user_id'],))
            updated=con.execute('SELECT * FROM users WHERE id=?',(pending['user_id'],)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(409,'An account with that email already exists.')
    return {'user':public_user(updated),'message':'Email address updated.'}

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

def local_password_reset_available(request):
    if os.getenv('LAND_LOCAL_PASSWORD_RESET','false').lower()!='true': return False
    if os.getenv('LAND_REQUIRE_PROXY','false').lower()=='true': return False
    if os.getenv('TURSO_DATABASE_URL') or os.getenv('TURSO_AUTH_TOKEN'): return False
    try:
        return bool(request.client and ipaddress.ip_address(request.client.host).is_loopback)
    except ValueError:
        return False

@router.get('/config')
def config(request:Request):
    return {'password_reset_available':reset_available(),
            'local_password_reset_available':local_password_reset_available(request)}

@router.post('/local-reset-password')
def local_reset_password(body:LocalResetRequest,request:Request):
    if not local_password_reset_available(request): raise HTTPException(404,'Not found')
    check_origin(request); throttle(request)
    encoded=hash_password(body.password)
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        user=con.execute('SELECT id FROM users WHERE email=?',(body.email,)).fetchone()
        if not user: raise HTTPException(404,'No account was found for that email address.')
        con.execute('UPDATE users SET password_hash=? WHERE id=?',(encoded,user['id']))
        con.execute('DELETE FROM user_sessions WHERE user_id=?',(user['id'],))
        con.execute('DELETE FROM password_resets WHERE user_id=?',(user['id'],))
        con.execute('DELETE FROM email_changes WHERE user_id=?',(user['id'],))
    return {'message':'Password changed. You can now sign in.'}

def send_reset(email,token):
    origin=os.getenv('LAND_PUBLIC_URL','http://127.0.0.1:3000').rstrip('/')
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
