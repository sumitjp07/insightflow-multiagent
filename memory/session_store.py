"""
memory/session_store.py – SQLite Session & History Persistence
================================================================
InsightFlow ka Persistent Memory Store:
  - SQLite database mein analysis sessions save karta hai
  - Evaluation metrics aur execution logs track karta hai
  - Past reports retrieve karne ki capability deta hai
"""

import sqlite3
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

import config

logger = logging.getLogger(__name__)


class SessionStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables using schema.sql."""
        schema_path = config.MEMORY_DIR / "schema.sql"
        if schema_path.exists():
            schema_sql = schema_path.read_text(encoding="utf-8")
            with self._get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
            logger.info("🗄️ SQLite memory initialized.")

    def create_session(self, session_id: str, dataset_name: str, 
                       row_count: int, column_count: int, 
                       user_query: str, status: str = "running"):
        """Saves a new session entry."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions 
                (session_id, dataset_name, row_count, column_count, user_query, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, dataset_name, row_count, column_count, user_query, status)
            )
            conn.commit()

    def update_session_status(self, session_id: str, status: str):
        """Updates the status of an ongoing session."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET status = ? WHERE session_id = ?",
                (status, session_id)
            )
            conn.commit()

    def log_agent_action(self, session_id: str, agent_name: str, action_type: str, details: str):
        """Logs an agent activity step into trace log."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO execution_logs (session_id, agent_name, action_type, details)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, agent_name, action_type, details)
            )
            conn.commit()

    def record_evaluation(self, session_id: str, accuracy: float, coverage: float, retries: int, status: str):
        """Records evaluation audit scores."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_metrics 
                (session_id, calculation_accuracy, evidence_coverage, retry_count, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, accuracy, coverage, retries, status)
            )
            conn.commit()

    def save_report(self, session_id: str, report_md: str):
        """Persists generated executive report."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reports (session_id, report_markdown)
                VALUES (?, ?)
                """,
                (session_id, report_md)
            )
            conn.commit()

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves history of past analysis sessions."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT s.session_id, s.created_at, s.dataset_name, s.user_query, s.status,
                       e.calculation_accuracy, e.retry_count
                FROM sessions s
                LEFT JOIN evaluation_metrics e ON s.session_id = e.session_id
                ORDER BY s.created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_session_report(self, session_id: str) -> Optional[str]:
        """Fetches the markdown report for a specific session."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT report_markdown FROM reports WHERE session_id = ? ORDER BY report_id DESC LIMIT 1",
                (session_id,)
            )
            row = cursor.fetchone()
            return row["report_markdown"] if row else None


# ── Quick Test ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  InsightFlow – SQLite Session Store Test")
    print("="*55)
    
    store = SessionStore()
    test_id = f"test_{int(datetime.now().timestamp())}"
    
    store.create_session(test_id, "sales_data.csv", 30, 10, "Test query")
    store.log_agent_action(test_id, "planner", "decompose", "Decomposed into 5 subtasks")
    store.record_evaluation(test_id, 100.0, 100.0, 0, "approved")
    store.save_report(test_id, "# Test Report\nEverything verified.")
    store.update_session_status(test_id, "completed")
    
    recent = store.get_recent_sessions(limit=3)
    print(f"  Sessions stored: {len(recent)}")
    for s in recent:
        print(f"  - [{s['session_id']}] {s['dataset_name']} -> {s['user_query']} (Status: {s['status']})")
        
    print("\n" + "="*55)
    print("  ✅ SQLite Memory Tests Succeeded!")
    print("="*55 + "\n")
