import pytest
from fastapi.testclient import TestClient
from land_discover.api import app

def test_hosted_api_requires_proxy_and_health_remains_available(monkeypatch):
    monkeypatch.setenv('LAND_REQUIRE_PROXY','true')
    monkeypatch.setenv('LAND_PROXY_SECRET','test-proxy-secret')
    with TestClient(app) as client:
        assert client.get('/api/health').status_code==200
        assert client.get('/api/properties').status_code==403
        assert client.get('/api/properties',headers={'X-Land-Proxy-Token':'test-proxy-secret'}).status_code==200

def test_trusted_proxy_allows_own_preview_origin(monkeypatch):
    monkeypatch.setenv('LAND_REQUIRE_PROXY','true')
    monkeypatch.setenv('LAND_PROXY_SECRET','test-proxy-secret')
    headers={'X-Land-Proxy-Token':'test-proxy-secret','X-Land-Frontend-Origin':'https://prototype-preview.vercel.app','Origin':'https://prototype-preview.vercel.app'}
    with TestClient(app) as client:
        body={'email':'preview@example.org','password':'a secure test password'}
        assert client.post('/api/auth/register',json=body,headers=headers).status_code==201
        headers['Origin']='https://evil.example.org'
        assert client.post('/api/auth/login',json=body,headers=headers).status_code==403

def test_manual_import_requires_admin_token_in_hosted_mode(monkeypatch):
    monkeypatch.setenv('LAND_REQUIRE_PROXY','true')
    monkeypatch.setenv('LAND_PROXY_SECRET','test-proxy-secret')
    monkeypatch.setenv('LAND_IMPORT_TOKEN','test-admin-token')
    headers={'X-Land-Proxy-Token':'test-proxy-secret'}
    monkeypatch.setattr('land_discover.importer.import_url',lambda *a: {'status':'complete','imported':1})
    with TestClient(app) as client:
        assert client.post('/api/import',json={'url':'https://example.org/property/1'},headers=headers).status_code==403
        headers['X-Land-Import-Token']='test-admin-token'
        assert client.post('/api/import',json={'url':'https://example.org/property/1'},headers=headers).status_code==200
