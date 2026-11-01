"""SQLite 仓储：业务层不依赖数据库连接细节，后续可替换其他存储。"""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Repository:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    UNIQUE(profile, event_id)
                );
                CREATE INDEX IF NOT EXISTS events_profile ON events(profile, seq);
                CREATE TABLE IF NOT EXISTS materials (
                    id TEXT PRIMARY KEY, profile TEXT NOT NULL, name TEXT NOT NULL,
                    status TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def events(db, profile):
        return [json.loads(row["body"]) for row in db.execute(
            "SELECT body FROM events WHERE profile=? ORDER BY seq", (profile,))]

    def materials(self, profile):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT id,name,status,detail,created_at FROM materials WHERE profile=? ORDER BY created_at DESC", (profile,))]
