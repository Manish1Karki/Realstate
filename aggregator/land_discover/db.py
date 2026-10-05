import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

def now():
    return datetime.now(timezone.utc).isoformat()

def db_path():
    value = Path(os.getenv('LAND_DB', 'data/properties.sqlite3'))
    return value if value.is_absolute() else ROOT / value

def cloud_config():
    url = os.getenv('TURSO_DATABASE_URL', '').strip()
    token = os.getenv('TURSO_AUTH_TOKEN', '').strip()
    if not url and not token:
        if os.getenv('LAND_REQUIRE_PERSISTENT_DB', 'false').lower() == 'true':
            raise RuntimeError('Configure TURSO_DATABASE_URL and TURSO_AUTH_TOKEN before starting the hosted backend')
        return None
    parsed = urlsplit(url)
    if not token or parsed.scheme not in ('libsql', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError('Configure a secure Turso database URL and its authentication token')
    return url, token

@contextmanager
def connect():
    cloud = cloud_config()
    if cloud or os.getenv('LAND_DATABASE_DRIVER') == 'libsql':
        import libsql
        from .cloud_db import Connection
        if cloud:
            # Query the cloud primary directly: no ephemeral replica or sync lag.
            con = Connection(libsql.connect(database=cloud[0], auth_token=cloud[1], timeout=30))
        else:
            path = db_path(); path.parent.mkdir(parents=True, exist_ok=True)
            con = Connection(libsql.connect(str(path), timeout=30))
    else:
        path = db_path(); path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(path, timeout=30)
        con.row_factory = sqlite3.Row
    try:
        con.execute('PRAGMA foreign_keys=ON')
        yield con
        con.commit()
    except Exception:
        con.rollback(); raise
    finally:
        con.close()

def init_db():
    with connect() as con:
        if not cloud_config():
            con.execute('PRAGMA journal_mode=WAL')
        con.executescript('''
        CREATE TABLE IF NOT EXISTS properties (
          id INTEGER PRIMARY KEY, source TEXT NOT NULL, source_url TEXT NOT NULL UNIQUE,
          title TEXT NOT NULL, address TEXT NOT NULL, area_name TEXT NOT NULL,
          district TEXT NOT NULL, ward TEXT, lat REAL, lng REAL,
          price_npr REAL, price_basis TEXT NOT NULL DEFAULT 'unknown', price_raw TEXT,
          total_price_npr REAL, property_type TEXT NOT NULL, transaction_type TEXT DEFAULT 'sale',
          size TEXT, size_sqft REAL, listing_date TEXT, listing_date_raw TEXT,
          nearest_school TEXT, school_distance_km REAL, nearest_hospital TEXT,
          hospital_distance_km REAL, road_access_note TEXT,
          scraped_date TEXT NOT NULL, first_seen TEXT NOT NULL,
          geocode_status TEXT DEFAULT 'pending', geocode_precision TEXT,
          geocode_label TEXT, geo_error TEXT,
          enrichment_status TEXT DEFAULT 'pending', enrichment_radius_m INTEGER,
          enriched_date TEXT, amenity_count INTEGER, amenity_score REAL,
          quality_flags TEXT NOT NULL DEFAULT '[]', is_demo INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_filters ON properties(district,property_type,total_price_npr);
        CREATE TABLE IF NOT EXISTS amenities (
          id INTEGER PRIMARY KEY, property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
          osm_id TEXT NOT NULL, name TEXT NOT NULL, kind TEXT NOT NULL,
          lat REAL NOT NULL,lng REAL NOT NULL,distance_km REAL NOT NULL,
          UNIQUE(property_id,osm_id,kind)
        );
        CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, fetched_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS request_clock (host TEXT PRIMARY KEY, next_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS runs (
          id INTEGER PRIMARY KEY, source TEXT, started_at TEXT, finished_at TEXT,
          status TEXT, pages INTEGER DEFAULT 0, imported INTEGER DEFAULT 0,
          rejected INTEGER DEFAULT 0, errors TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS collection_cycles (
          id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT,
          status TEXT NOT NULL, current_source TEXT, reports TEXT NOT NULL DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
          display_name TEXT NOT NULL DEFAULT '', password_hash TEXT NOT NULL,
          created_at TEXT NOT NULL, last_login_at TEXT
        );
        CREATE TABLE IF NOT EXISTS user_sessions (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL, expires_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_session_expiry ON user_sessions(expires_at);
        CREATE TABLE IF NOT EXISTS auth_attempts (
          key TEXT PRIMARY KEY, started_at REAL NOT NULL, attempts INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS password_resets (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          expires_at REAL NOT NULL
        );
        ''')
        existing = {row['name'] for row in con.execute('PRAGMA table_info(properties)')}
        for column, kind in [('description', 'TEXT'), ('bedrooms', 'INTEGER'), ('bathrooms', 'INTEGER'), ('contact_name', 'TEXT'), ('contact_phone', 'TEXT'), ('image_url', 'TEXT'), ('image_urls', "TEXT DEFAULT '[]'")]:
            if column not in existing:
                con.execute(f'ALTER TABLE properties ADD COLUMN {column} {kind}')

def upsert(item):
    item = dict(item)
    item.setdefault('scraped_date', now()); item.setdefault('first_seen', now())
    if isinstance(item.get('quality_flags'), list): item['quality_flags'] = json.dumps(item['quality_flags'])
    if isinstance(item.get('image_urls'), list): item['image_urls'] = json.dumps(item['image_urls'])
    with connect() as con:
        old = con.execute('SELECT * FROM properties WHERE source_url=?', (item['source_url'],)).fetchone()
        if old and old['address'] != item['address']:
            con.execute('DELETE FROM amenities WHERE property_id=?',(old['id'],))
            con.execute("UPDATE properties SET lat=NULL,lng=NULL,geocode_status='pending',enrichment_status='pending',nearest_school=NULL,school_distance_km=NULL,nearest_hospital=NULL,hospital_distance_km=NULL,amenity_count=NULL,amenity_score=NULL WHERE id=?",(old['id'],))
        columns = list(item)
        updates = ','.join(f'{c}=excluded.{c}' for c in columns if c not in ('source_url','first_seen'))
        con.execute(f"INSERT INTO properties ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)}) ON CONFLICT(source_url) DO UPDATE SET {updates}", list(item.values()))
        return con.execute('SELECT id FROM properties WHERE source_url=?', (item['source_url'],)).fetchone()[0]

def cached(key, max_age_days=30):
    with connect() as con:
        row = con.execute('SELECT * FROM cache WHERE key=?',(key,)).fetchone()
    if row and (datetime.now(timezone.utc)-datetime.fromisoformat(row['fetched_at'])).total_seconds() < max_age_days*86400:
        return json.loads(row['value'])
    return None

def cache_set(key, value):
    with connect() as con:
        con.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',(key,json.dumps(value),now()))
