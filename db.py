"""
SQLite schema and connection helper. No ORM — plain sqlite3, one table.
"""
import sqlite3

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS photos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path            TEXT UNIQUE NOT NULL,
    extension       TEXT NOT NULL,
    file_size       INTEGER NOT NULL,
    mtime           REAL NOT NULL,      -- file's last-modified time; used to skip unchanged files on rescan
    file_hash       TEXT,               -- sha256, for duplicate detection
    date_taken      TEXT,
    camera_make     TEXT,
    camera_model    TEXT,
    lens            TEXT,
    exposure_time   TEXT,
    aperture        TEXT,
    iso             INTEGER,
    focal_length    TEXT,
    rating          INTEGER NOT NULL DEFAULT 0,
    tags            TEXT NOT NULL DEFAULT '',   -- comma-separated free text
    viewed          INTEGER NOT NULL DEFAULT 0, -- 0/1
    thumbnail_path  TEXT
);
CREATE INDEX IF NOT EXISTS idx_photos_date_taken ON photos(date_taken);
CREATE INDEX IF NOT EXISTS idx_photos_rating ON photos(rating);
CREATE INDEX IF NOT EXISTS idx_photos_file_hash ON photos(file_hash);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"DB ready at {DB_PATH}")
