import pytest
from land_discover.db import init_db

@pytest.fixture(autouse=True, params=['sqlite', 'libsql'])
def isolated_db(tmp_path,monkeypatch,request):
    monkeypatch.delenv('TURSO_DATABASE_URL', raising=False)
    monkeypatch.delenv('TURSO_AUTH_TOKEN', raising=False)
    monkeypatch.setenv('LAND_REQUIRE_PERSISTENT_DB', 'false')
    monkeypatch.setenv('LAND_DATABASE_DRIVER', request.param)
    monkeypatch.setenv('LAND_DB',str(tmp_path/'test.sqlite3'))
    monkeypatch.setenv('LAND_AUTO_SCRAPE','false')
    init_db()

@pytest.fixture
def raw():
    return dict(source='fixture',source_url='https://example.org/property/1',title='Land for sale in Baneshwor',address='Baneshwor, Ward 10, Kathmandu',price_raw='NPR 25 lakh per aana',size='0-4-0-0',property_type='land',transaction_type='sale',listing_date_raw='2026-01-10')
