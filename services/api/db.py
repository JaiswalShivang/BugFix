import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from packages.contracts.models import InvestigationStatus

DB_PATH = os.path.abspath("artifacts/bugproof.sqlite3")

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    coupon_code TEXT,
                    worktree TEXT,
                    baseline_report TEXT,
                    patch_summary TEXT,
                    verification_report TEXT,
                    decision TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investigation_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    switch_message_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def create_investigation(
        self,
        investigation_id: str,
        target_url: str,
        scenario: str,
        coupon_code: str = "EXPIRED10",
    ) -> Dict[str, Any]:
        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO investigations (id, status, target_url, scenario, coupon_code)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    InvestigationStatus.CREATED.value,
                    target_url,
                    scenario,
                    coupon_code,
                ),
            )
            conn.execute(
                """
                INSERT INTO events (investigation_id, event_type, actor, payload)
                VALUES (?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    "CREATED",
                    "system",
                    json.dumps({"target_url": target_url, "scenario": scenario}),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return self.get_investigation(investigation_id)

    def update_status(
        self,
        investigation_id: str,
        status: InvestigationStatus,
        actor: str,
        payload: Dict[str, Any],
        switch_message_id: Optional[str] = None,
    ):
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE investigations
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status.value, investigation_id),
            )
            conn.execute(
                """
                INSERT INTO events (investigation_id, event_type, actor, payload, switch_message_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    status.value,
                    actor,
                    json.dumps(payload),
                    switch_message_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def update_baseline_report(self, investigation_id: str, report: Dict[str, Any]):
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE investigations
                SET baseline_report = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (json.dumps(report), investigation_id),
            )
            conn.commit()
        finally:
            conn.close()

    def update_patch_summary(self, investigation_id: str, summary: Dict[str, Any]):
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE investigations
                SET patch_summary = ?, worktree = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    json.dumps(summary),
                    summary.get("worktree_path"),
                    investigation_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def update_verification_report(self, investigation_id: str, report: Dict[str, Any]):
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE investigations
                SET verification_report = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (json.dumps(report), investigation_id),
            )
            conn.commit()
        finally:
            conn.close()

    def update_decision(self, investigation_id: str, decision: Dict[str, Any]):
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE investigations
                SET decision = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (json.dumps(decision), investigation_id),
            )
            conn.commit()
        finally:
            conn.close()

    def get_investigation(self, investigation_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM investigations WHERE id = ?",
                (investigation_id,),
            ).fetchone()
            if not row:
                return None
            data = dict(row)
            if data["baseline_report"]:
                data["baseline_report"] = json.loads(data["baseline_report"])
            if data["patch_summary"]:
                data["patch_summary"] = json.loads(data["patch_summary"])
            if data["verification_report"]:
                data["verification_report"] = json.loads(data["verification_report"])
            if data["decision"]:
                data["decision"] = json.loads(data["decision"])

            events = conn.execute(
                "SELECT * FROM events WHERE investigation_id = ? ORDER BY id ASC",
                (investigation_id,),
            ).fetchall()
            data["events"] = [
                {
                    "id": ev["id"],
                    "event_type": ev["event_type"],
                    "actor": ev["actor"],
                    "payload": json.loads(ev["payload"]),
                    "switch_message_id": ev["switch_message_id"],
                    "created_at": ev["created_at"],
                }
                for ev in events
            ]
            return data
        finally:
            conn.close()

    def list_investigations(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT id, status, target_url, scenario, coupon_code, updated_at FROM investigations ORDER BY updated_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
