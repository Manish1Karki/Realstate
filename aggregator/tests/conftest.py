import pytest
from land_discover.db import init_db

@pytest.fixture(autouse=True)
def isolated_db(tmp_path,monkeypatch):
    monkeypatch.setenv('LAND_DB',str(tmp_path/'test.sqlite3'))
    init_db()

@pytest.fixture
def raw():
    return dict(source='fixture',source_url='https://example.org/property/1',title='Land for sale in Baneshwor',address='Baneshwor, Ward 10, Kathmandu',price_raw='NPR 25 lakh per aana',size='0-4-0-0',property_type='land',transaction_type='sale',listing_date_raw='2026-01-10')
