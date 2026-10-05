import sqlite3
import libsql
import pytest
from land_discover.db import cloud_config, connect


def test_commit_rollback_and_foreign_keys():
    with connect() as con:
        con.execute('INSERT INTO users(email,password_hash,created_at) VALUES (?,?,?)',
                    ('persist@example.org', 'test-hash', '2026-10-05'))
    with pytest.raises(sqlite3.IntegrityError):
        with connect() as con:
            con.execute('INSERT INTO cache VALUES (?,?,?)', ('rollback', '{}', '2026-10-05'))
            con.execute('INSERT INTO user_sessions VALUES (?,?,?,?)', ('invalid', 999, '2026-10-05', 1000))
    with connect() as con:
        assert con.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 1
        assert con.execute('SELECT * FROM cache WHERE key=?', ('rollback',)).fetchone() is None


def test_schema_errors_propagate():
    with pytest.raises(sqlite3.DatabaseError):
        with connect() as con:
            con.executescript('THIS IS NOT VALID SQL;')


def test_cursor_exhaustion_and_row_mapping():
    with connect() as con:
        cursor = con.execute("SELECT 4 AS id, 'example' AS title")
        row = cursor.fetchone()
        assert row[0] == row['id'] == 4
        assert dict(row) == {'id': 4, 'title': 'example'}
        assert list(row) == [4, 'example']
        assert cursor.fetchone() is None
        assert cursor.fetchone() is None
        assert cursor.fetchall() == []


def test_hosted_database_cannot_fall_back_to_local_file(monkeypatch):
    monkeypatch.setenv('LAND_REQUIRE_PERSISTENT_DB', 'true')
    with pytest.raises(RuntimeError, match='Configure TURSO'):
        with connect():
            pytest.fail('Hosted database fell back to local storage')


@pytest.mark.parametrize('url,token', [('', 'secret'), ('libsql://database.turso.io', ''),
    ('http://database.turso.io', 'secret'), ('https://user:password@database.turso.io', 'secret'),
    ('https://database.turso.io?token=secret', 'secret')])
def test_incomplete_or_insecure_cloud_configuration_is_rejected(monkeypatch, url, token):
    monkeypatch.setenv('TURSO_DATABASE_URL', url)
    monkeypatch.setenv('TURSO_AUTH_TOKEN', token)
    with pytest.raises(RuntimeError, match='secure Turso'):
        cloud_config()


def test_cloud_connections_use_primary_and_token_without_replica(monkeypatch, tmp_path):
    # Use the real driver locally to verify connection routing and persistence;
    # actual cloud access is verified separately after account authorization.
    original = libsql.connect
    calls = []
    def connector(**kwargs):
        calls.append(kwargs)
        return original(str(tmp_path / 'cloud.sqlite3'))
    monkeypatch.setattr(libsql, 'connect', connector)
    monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://database.turso.io')
    monkeypatch.setenv('TURSO_AUTH_TOKEN', 'test-only-token')
    with connect() as con:
        con.execute('CREATE TABLE persist(value TEXT)')
        con.execute('INSERT INTO persist VALUES (?)', ('stored',))
    with connect() as con:
        assert con.execute('SELECT value FROM persist').fetchone()['value'] == 'stored'
    assert calls == [dict(database='libsql://database.turso.io', auth_token='test-only-token', timeout=30)] * 2
