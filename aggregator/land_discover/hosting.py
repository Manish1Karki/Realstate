"""Authentication of requests from the prototype's server-side API proxy."""
import hmac
import os
from fastapi import HTTPException

def trusted_proxy(request):
    expected=os.getenv('LAND_PROXY_SECRET','')
    supplied=request.headers.get('x-land-proxy-token','')
    return bool(expected and hmac.compare_digest(expected.encode(),supplied.encode()))

def require_proxy():
    return os.getenv('LAND_REQUIRE_PROXY','false').lower()=='true'

def check_import_access(request):
    expected=os.getenv('LAND_IMPORT_TOKEN','')
    if not expected and not require_proxy(): return
    supplied=request.headers.get('x-land-import-token','')
    if not expected or not hmac.compare_digest(expected.encode(),supplied.encode()):
        raise HTTPException(403,'Importing listings requires administrator access')
