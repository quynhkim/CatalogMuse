"""Job board the Go backend polls.

This is separate from the LangGraph checkpoint. A running agent updates it
before the graph step finishes, so a watcher can see "running" immediately.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

AGENTS = ("segment", "art_director", "scene", "copy", "rules")

_SCHEMA = """
create table if not exists jobs (
  id text primary key,
  status text not null,
  error text not null default '',
  created_at text not null,
  marketplaces text not null default '["amazon"]'
);
create table if not exists agents (
  job_id text not null,
  name text not null,
  position integer not null,
  state text not null,
  detail text not null default '',
  output_json text,
  primary key (job_id, name)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StatusBoard:
    def __init__(self, path: str) -> None:
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(_SCHEMA)
        columns = {row["name"] for row in self._db.execute("pragma table_info(jobs)")}
        if "marketplaces" not in columns:
            self._db.execute("alter table jobs add column marketplaces text not null default '[\"amazon\"]'")
            self._db.commit()

    def create(self, job_id: str, marketplaces: list[str] | None = None) -> None:
        encoded = json.dumps(marketplaces or ["amazon"])
        with self._lock:
            self._db.execute(
                "insert into jobs (id, status, error, created_at, marketplaces) values (?, 'running', '', ?, ?)",
                (job_id, _now(), encoded),
            )
            self._db.executemany(
                "insert into agents (job_id, name, position, state, detail, output_json) values (?, ?, ?, 'pending', '', null)",
                [(job_id, name, index) for index, name in enumerate(AGENTS)],
            )
            self._db.commit()

    def mark(self, job_id: str, agent: str, state: str, detail: str = "", output: Any = None) -> None:
        with self._lock:
            if output is None:
                self._db.execute(
                    "update agents set state = ?, detail = ? where job_id = ? and name = ?",
                    (state, detail, job_id, agent),
                )
            else:
                self._db.execute(
                    "update agents set state = ?, detail = ?, output_json = ? where job_id = ? and name = ?",
                    (state, detail, json.dumps(output), job_id, agent),
                )
            self._db.commit()

    def fail(self, job_id: str, error: str) -> None:
        with self._lock:
            self._db.execute("update jobs set status = 'failed', error = ? where id = ?", (error[:500], job_id))
            self._db.commit()

    def finish(self, job_id: str) -> None:
        with self._lock:
            self._db.execute("update jobs set status = 'approved', error = '' where id = ?", (job_id,))
            self._db.commit()

    def snapshot(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._db.execute("select * from jobs where id = ?", (job_id,)).fetchone()
            if job is None:
                return None
            rows = self._db.execute(
                "select name, state, detail, output_json from agents where job_id = ? order by position",
                (job_id,),
            ).fetchall()
        agents = []
        for row in rows:
            if row["name"] not in AGENTS:
                continue
            output = json.loads(row["output_json"]) if row["output_json"] else None
            agents.append(
                {"name": row["name"], "state": row["state"], "detail": row["detail"], "output": output}
            )
        raw = job["marketplaces"] if "marketplaces" in job.keys() else '["amazon"]'
        try:
            marketplaces = json.loads(raw) if raw else ["amazon"]
        except json.JSONDecodeError:
            marketplaces = ["amazon"]
        return {
            "id": job["id"],
            "status": job["status"],
            "error": job["error"],
            "marketplaces": marketplaces,
            "agents": agents,
        }
