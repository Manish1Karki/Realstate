from datetime import date, timedelta
from fastapi.testclient import TestClient
from land_discover.api import app
from land_discover.db import upsert
from land_discover.eligibility import is_recent_listing, nepal_today, six_month_cutoff
from land_discover.normalize import normalize


def test_six_calendar_month_boundary():
    today = date(2026, 10, 9)
    assert six_month_cutoff(today) == date(2026, 4, 9)
    assert six_month_cutoff(date(2026, 8, 31)) == date(2026, 2, 28)
    for value, expected in [('2026-04-09', True), ('2026-04-08', False),
                            ('2026-10-09', True), ('2026-10-10', False),
                            (None, False), ('invalid', False)]:
        assert is_recent_listing({'listing_date': value}, today) == expected


def test_recent_unmapped_listings_visible_everywhere(raw):
    item = {**normalize(raw), 'image_url': 'https://example.org/house.jpg'}
    today = nepal_today()
    cutoff = six_month_cutoff(today)
    for index, listed in enumerate([today, cutoff, cutoff-timedelta(days=1), today+timedelta(days=1), None]):
        upsert({**item, 'source_url': f'https://example.org/property/{index}',
                'listing_date': listed.isoformat() if listed else None})
    with TestClient(app) as client:
        assert client.get('/api/properties').json()['total'] == 2
        assert client.get('/api/summary').json()['total'] == 2
        assert len(client.get('/api/sitemap').json()['items']) == 2
        assert client.get('/api/options').json()['areas'] == ['Baneshwor']
        assert client.get('/api/map').json()['items'] == []
        assert len(client.get('/api/export.csv').text.splitlines()) == 3


def test_scraper_skips_old_and_unknown_dates(monkeypatch, raw):
    from land_discover import scraper
    item = {**normalize(raw), 'image_url': 'https://example.org/house.jpg'}
    monkeypatch.setattr(scraper, 'review', lambda *args: None)
    monkeypatch.setattr(scraper.Client, 'page', lambda *args: '')
    monkeypatch.setattr(scraper, 'discover', lambda *args: (['recent', 'old', 'unknown'], None))
    dates = {'recent': nepal_today().isoformat(),
             'old': (six_month_cutoff()-timedelta(days=1)).isoformat(), 'unknown': None}
    monkeypatch.setattr(scraper, 'parse_detail', lambda html, url, source: {
        **item, 'source_url': 'https://example.org/'+url, 'listing_date': dates[url]})
    report = scraper.scrape('hamrobazar')
    assert report['imported'] == 1
    assert report['skipped'] == 2
