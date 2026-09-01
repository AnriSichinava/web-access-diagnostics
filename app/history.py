import sqlite3
from pathlib import Path

from app.models import DiagnosisReport

DB_PATH = Path(__file__).resolve().parent.parent / "diagnostics.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                correlation_id TEXT PRIMARY KEY,
                target_url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                direct_classification TEXT,
                proxy_classification TEXT,
                report_json TEXT NOT NULL
            )
            """
        )


def save_report(report: DiagnosisReport) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO reports
                (correlation_id, target_url, timestamp, direct_classification, proxy_classification, report_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                report.correlation_id,
                report.target_url,
                report.timestamp.isoformat(),
                report.direct.classification,
                report.proxy.classification if report.proxy else None,
                report.model_dump_json(),
            ),
        )


def get_report(correlation_id: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT report_json FROM reports WHERE correlation_id = ?", (correlation_id,)
        ).fetchone()
    return DiagnosisReport.model_validate_json(row[0]).model_dump() if row else None


def list_reports(limit: int = 50) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT correlation_id, target_url, timestamp, direct_classification, proxy_classification
            FROM reports ORDER BY timestamp DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    columns = ["correlation_id", "target_url", "timestamp", "direct_classification", "proxy_classification"]
    return [dict(zip(columns, row)) for row in rows]
