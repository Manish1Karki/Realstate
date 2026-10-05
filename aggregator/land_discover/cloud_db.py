"""Adapt the official libSQL driver to the rows used by the SQLite application."""
import sqlite3


def call(operation, *args):
    # libsql 0.1 exposes SQLite failures as ValueError instead of DB-API errors.
    try:
        return operation(*args)
    except ValueError as exc:
        if 'constraint failed' in str(exc).lower():
            raise sqlite3.IntegrityError(str(exc)) from exc
        raise sqlite3.DatabaseError(str(exc)) from exc


class Row(dict):
    def __iter__(self):
        # sqlite3.Row iterates values; CSV exports rely on that behavior.
        return iter(self.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)


class Cursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self.description = cursor.description
        self.lastrowid = cursor.lastrowid
        self.rowcount = cursor.rowcount
        self._finished = False

    def fetchone(self):
        if self._finished:
            return None
        values = call(self._cursor.fetchone)
        if values is None:
            self._finished = True
            return None
        return Row(zip((column[0] for column in self.description), values))

    def fetchall(self):
        return list(self)

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row


class Connection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql, parameters=()):
        return Cursor(call(self._connection.execute, sql, parameters))

    def executescript(self, sql):
        # Connection.executescript silently discards errors in libsql 0.1.11;
        # Cursor.executescript propagates them so startup cannot hide a failure.
        cursor = self._connection.cursor()
        try:
            call(cursor.executescript, sql)
        finally:
            cursor.close()

    def executemany(self, sql, parameters):
        return Cursor(call(self._connection.executemany, sql, list(parameters)))

    def commit(self):
        call(self._connection.commit)

    def rollback(self):
        call(self._connection.rollback)

    def close(self):
        self._connection.close()
