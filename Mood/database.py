"""
Mood - SQLite database layer
Handles performers, media files, favorites, sessions.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
import config


class Database:
    def __init__(self, db_path: Path = config.DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _ensure_schema(self):
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS performers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                folder_name TEXT NOT NULL UNIQUE,
                is_favorite INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS media (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                performer_id    INTEGER NOT NULL,
                filename        TEXT NOT NULL,
                original_name   TEXT,
                media_type      TEXT NOT NULL CHECK(media_type IN ('image','video')),
                added_at        TEXT NOT NULL,
                is_favorite     INTEGER NOT NULL DEFAULT 0,
                play_count      INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (performer_id) REFERENCES performers(id) ON DELETE CASCADE,
                UNIQUE(performer_id, filename)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at      TEXT NOT NULL,
                ended_at        TEXT,
                duration_sec    INTEGER,
                switches        INTEGER NOT NULL DEFAULT 0,
                performer_ids   TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_media_performer ON media(performer_id);
            CREATE INDEX IF NOT EXISTS idx_media_fav ON media(is_favorite);
            CREATE INDEX IF NOT EXISTS idx_perf_fav ON performers(is_favorite);
        """)
        conn.commit()

        # migration: sort_order for manual list order
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(performers)").fetchall()]
            if "sort_order" not in cols:
                conn.execute("ALTER TABLE performers ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
                # seed by name
                rows = conn.execute("SELECT id FROM performers ORDER BY name COLLATE NOCASE").fetchall()
                for i, r in enumerate(rows):
                    conn.execute("UPDATE performers SET sort_order=? WHERE id=?", (i, r["id"]))
                conn.commit()
        except Exception:
            pass


    # ------------------------------------------------------------------
    # Performers
    # ------------------------------------------------------------------
    def add_performer(self, name: str, folder_name: str) -> int:
        conn = self._connect()
        now = datetime.now().isoformat(timespec="seconds")
        row_max = conn.execute("SELECT COALESCE(MAX(sort_order), -1) AS m FROM performers").fetchone()
        next_ord = int(row_max["m"]) + 1 if row_max else 0
        cur = conn.execute(
            "INSERT OR IGNORE INTO performers (name, folder_name, created_at, sort_order) VALUES (?,?,?,?)",
            (name, folder_name, now, next_ord)
        )
        conn.commit()
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute("SELECT id FROM performers WHERE name=?", (name,)).fetchone()
        return row["id"]

    
    def reorder_performers(self, ordered_ids):
        """Persist list order from UI drag-drop."""
        conn = self._connect()
        for i, pid in enumerate(ordered_ids):
            conn.execute("UPDATE performers SET sort_order=? WHERE id=?", (i, int(pid)))
        conn.commit()

    def get_all_performers(self) -> List[sqlite3.Row]:
        conn = self._connect()
        return conn.execute(
            "SELECT * FROM performers ORDER BY sort_order ASC, name COLLATE NOCASE"
        ).fetchall()

    def get_favorite_performers(self) -> List[sqlite3.Row]:
        conn = self._connect()
        return conn.execute(
            "SELECT * FROM performers WHERE is_favorite=1 ORDER BY name COLLATE NOCASE"
        ).fetchall()

    def toggle_performer_favorite(self, performer_id: int) -> bool:
        conn = self._connect()
        row = conn.execute("SELECT is_favorite FROM performers WHERE id=?", (performer_id,)).fetchone()
        if not row:
            return False
        new_val = 0 if row["is_favorite"] else 1
        conn.execute("UPDATE performers SET is_favorite=? WHERE id=?", (new_val, performer_id))
        conn.commit()
        return bool(new_val)

    def get_performer_by_name(self, name: str) -> Optional[sqlite3.Row]:
        conn = self._connect()
        return conn.execute("SELECT * FROM performers WHERE name=?", (name,)).fetchone()

    def get_performer_by_id(self, pid: int) -> Optional[sqlite3.Row]:
        conn = self._connect()
        return conn.execute("SELECT * FROM performers WHERE id=?", (pid,)).fetchone()


    def delete_performer(self, performer_id: int) -> bool:
        """Delete performer and all media rows (CASCADE)."""
        conn = self._connect()
        conn.execute("DELETE FROM media WHERE performer_id=?", (performer_id,))
        cur = conn.execute("DELETE FROM performers WHERE id=?", (performer_id,))
        conn.commit()
        return cur.rowcount > 0


    # ------------------------------------------------------------------
    # Media
    # ------------------------------------------------------------------
    def add_media(self, performer_id: int, filename: str, original_name: str,
                  media_type: str) -> int:
        conn = self._connect()
        now = datetime.now().isoformat(timespec="seconds")
        cur = conn.execute(
            """INSERT OR IGNORE INTO media
               (performer_id, filename, original_name, media_type, added_at)
               VALUES (?,?,?,?,?)""",
            (performer_id, filename, original_name, media_type, now)
        )
        conn.commit()
        return cur.lastrowid or 0

    def get_media_for_performer(self, performer_id: int,
                                only_favorites: bool = False) -> List[sqlite3.Row]:
        conn = self._connect()
        if only_favorites:
            return conn.execute(
                "SELECT * FROM media WHERE performer_id=? AND is_favorite=1 ORDER BY filename",
                (performer_id,)
            ).fetchall()
        return conn.execute(
            "SELECT * FROM media WHERE performer_id=? ORDER BY filename",
            (performer_id,)
        ).fetchall()

    def get_all_favorite_media(self) -> List[sqlite3.Row]:
        conn = self._connect()
        return conn.execute(
            "SELECT m.*, p.name as performer_name FROM media m "
            "JOIN performers p ON p.id = m.performer_id "
            "WHERE m.is_favorite=1 ORDER BY m.filename"
        ).fetchall()

    def toggle_media_favorite(self, media_id: int) -> bool:
        conn = self._connect()
        row = conn.execute("SELECT is_favorite FROM media WHERE id=?", (media_id,)).fetchone()
        if not row:
            return False
        new_val = 0 if row["is_favorite"] else 1
        conn.execute("UPDATE media SET is_favorite=? WHERE id=?", (new_val, media_id))
        conn.commit()
        return bool(new_val)

    def increment_play_count(self, media_id: int):
        conn = self._connect()
        conn.execute("UPDATE media SET play_count = play_count + 1 WHERE id=?", (media_id,))
        conn.commit()

    def media_exists(self, performer_id: int, filename: str) -> bool:
        conn = self._connect()
        row = conn.execute(
            "SELECT 1 FROM media WHERE performer_id=? AND filename=?",
            (performer_id, filename)
        ).fetchone()
        return row is not None


    def cleanup_missing_media(self, media_root) -> int:
        """Remove DB rows whose files no longer exist. Returns deleted count."""
        from pathlib import Path
        conn = self._connect()
        rows = conn.execute(
            "SELECT m.id, m.filename, p.folder_name FROM media m "
            "JOIN performers p ON p.id = m.performer_id"
        ).fetchall()
        deleted = 0
        for r in rows:
            path = Path(media_root) / r["folder_name"] / r["filename"]
            if not path.exists():
                conn.execute("DELETE FROM media WHERE id=?", (r["id"],))
                deleted += 1
        conn.commit()
        return deleted

    def count_media_for_performer(self, performer_id: int) -> int:
        conn = self._connect()
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM media WHERE performer_id=?",
            (performer_id,)
        ).fetchone()
        return int(row["c"]) if row else 0

    
    def get_performer_time_stats(self, performer_id: int) -> dict:
        """Total seconds & sessions where this performer participated."""
        conn = self._connect()
        rows = conn.execute(
            "SELECT duration_sec, switches, started_at, performer_ids FROM sessions "
            "WHERE ended_at IS NOT NULL AND performer_ids IS NOT NULL"
        ).fetchall()
        total_sec = 0
        sessions = 0
        switches = 0
        pid = str(performer_id)
        for r in rows:
            ids = [x.strip() for x in (r["performer_ids"] or "").split(",") if x.strip()]
            if pid in ids:
                # full session time counts for each listed performer
                total_sec += int(r["duration_sec"] or 0)
                sessions += 1
                switches += int(r["switches"] or 0)
        return {"seconds": total_sec, "sessions": sessions, "switches": switches}

    def get_total_mood_time(self) -> dict:
        conn = self._connect()
        row = conn.execute(
            "SELECT COALESCE(SUM(duration_sec),0) AS sec, COUNT(*) AS n, "
            "COALESCE(SUM(switches),0) AS sw FROM sessions WHERE ended_at IS NOT NULL"
        ).fetchone()
        return {"seconds": int(row["sec"]), "sessions": int(row["n"]), "switches": int(row["sw"])}

    def get_stats_summary(self) -> dict:
        conn = self._connect()
        sessions = conn.execute(
            "SELECT id, started_at, ended_at, switches, performer_ids FROM sessions "
            "ORDER BY id DESC LIMIT 200"
        ).fetchall()
        media_count = conn.execute("SELECT COUNT(*) AS c FROM media").fetchone()["c"]
        perf_count = conn.execute("SELECT COUNT(*) AS c FROM performers").fetchone()["c"]
        return {
            "sessions": sessions,
            "media_count": media_count,
            "performer_count": perf_count,
        }

    # ------------------------------------------------------------------
    # Sessions / Stats
    # ------------------------------------------------------------------
    def start_session(self) -> int:
        conn = self._connect()
        now = datetime.now().isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO sessions (started_at) VALUES (?)", (now,)
        )
        conn.commit()
        return cur.lastrowid

    def end_session(self, session_id: int, switches: int, performer_ids: List[int]):
        conn = self._connect()
        now = datetime.now().isoformat(timespec="seconds")
        row = conn.execute("SELECT started_at FROM sessions WHERE id=?", (session_id,)).fetchone()
        duration = 0
        if row:
            start = datetime.fromisoformat(row["started_at"])
            duration = int((datetime.now() - start).total_seconds())
        ids_str = ",".join(str(i) for i in performer_ids) if performer_ids else ""
        conn.execute(
            """UPDATE sessions
               SET ended_at=?, duration_sec=?, switches=?, performer_ids=?
               WHERE id=?""",
            (now, duration, switches, ids_str, session_id)
        )
        conn.commit()

    def get_recent_sessions(self, limit: int = 20) -> List[sqlite3.Row]:
        conn = self._connect()
        return conn.execute(
            "SELECT * FROM sessions WHERE ended_at IS NOT NULL "
            "ORDER BY started_at DESC LIMIT ?",
            (limit,)
        ).fetchall()

    def get_top_performers(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Return (name, total_play_count) sorted descending."""
        conn = self._connect()
        rows = conn.execute(
            """SELECT p.name, SUM(m.play_count) as total
               FROM media m
               JOIN performers p ON p.id = m.performer_id
               GROUP BY p.id
               HAVING total > 0
               ORDER BY total DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
        return [(r["name"], r["total"]) for r in rows]

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
