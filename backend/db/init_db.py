"""
init_db.py -- Initialize SQLite database for NyayaMitra.
Creates tables: doc_templates, generated_docs.
Seeds doc_templates from templates.json.
Run once: python db/init_db.py
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "nyayamitra.db"
TEMPLATES_PATH = Path(__file__).parent / "templates.json"

CREATE_DOC_TEMPLATES_SQL = """
CREATE TABLE IF NOT EXISTS doc_templates (
    doc_type        TEXT PRIMARY KEY,
    title_en        TEXT,
    title_hi        TEXT,
    required_fields TEXT,
    structure       TEXT,
    format_notes    TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_GENERATED_DOCS_SQL = """
CREATE TABLE IF NOT EXISTS generated_docs (
    session_id        TEXT PRIMARY KEY,
    doc_type          TEXT,
    intake_json       TEXT,
    draft_text        TEXT,
    verification_json TEXT,
    pdf_path          TEXT,
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db() -> sqlite3.Connection:
    """
    Create the database schema and seed doc_templates from templates.json.

    Returns:
        Open sqlite3.Connection (caller is responsible for closing).
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    conn.execute(CREATE_DOC_TEMPLATES_SQL)
    conn.execute(CREATE_GENERATED_DOCS_SQL)
    conn.commit()

    if TEMPLATES_PATH.exists():
        with open(TEMPLATES_PATH, encoding="utf-8") as f:
            templates: list[dict] = json.load(f)

        for tmpl in templates:
            conn.execute(
                """
                INSERT INTO doc_templates (
                    doc_type, title_en, title_hi, required_fields, structure, format_notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_type) DO UPDATE SET
                    title_en        = excluded.title_en,
                    title_hi        = excluded.title_hi,
                    required_fields = excluded.required_fields,
                    structure       = excluded.structure,
                    format_notes    = excluded.format_notes
                """,
                (
                    tmpl["doc_type"],
                    tmpl.get("title_en", ""),
                    tmpl.get("title_hi", ""),
                    json.dumps(tmpl.get("required_fields", []), ensure_ascii=False),
                    json.dumps(tmpl.get("structure", []), ensure_ascii=False),
                    tmpl.get("format_notes", ""),
                ),
            )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM doc_templates").fetchone()[0]
        print(f"DB initialised -- {count} template(s) loaded into doc_templates.")
    else:
        print(f"WARNING: templates.json not found at {TEMPLATES_PATH}")

    return conn


def get_template(doc_type: str) -> dict | None:
    """
    Fetch a single template by document type.

    Args:
        doc_type: One of fir | legal_notice | consumer_complaint |
                  cheque_bounce | tenant_eviction.

    Returns:
        Template dict with deserialized required_fields and structure, or None.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM doc_templates WHERE doc_type = ?", (doc_type,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    result = dict(row)
    # Deserialize JSON columns
    try:
        result["required_fields"] = json.loads(result.get("required_fields") or "[]")
    except (json.JSONDecodeError, TypeError):
        result["required_fields"] = []
    try:
        result["structure"] = json.loads(result.get("structure") or "[]")
    except (json.JSONDecodeError, TypeError):
        result["structure"] = []
    return result


def save_generated_doc(
    session_id: str,
    doc_type: str,
    intake_json: dict,
    draft_text: str,
    verification_json: dict,
    pdf_path: str,
) -> None:
    """
    Persist a completed pipeline result to the generated_docs table.

    Args:
        session_id:        Pipeline run identifier.
        doc_type:          Document type used.
        intake_json:       Structured case data from IntakeAgent.
        draft_text:        Plain text document from DrafterAgent.
        verification_json: Quality report from VerifierAgent.
        pdf_path:          Absolute path to the generated PDF.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        INSERT INTO generated_docs (
            session_id, doc_type, intake_json, draft_text, verification_json, pdf_path
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            doc_type          = excluded.doc_type,
            intake_json       = excluded.intake_json,
            draft_text        = excluded.draft_text,
            verification_json = excluded.verification_json,
            pdf_path          = excluded.pdf_path
        """,
        (
            session_id,
            doc_type,
            json.dumps(intake_json, ensure_ascii=False),
            draft_text,
            json.dumps(verification_json, ensure_ascii=False),
            pdf_path,
        ),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    conn = init_db()
    conn.close()
