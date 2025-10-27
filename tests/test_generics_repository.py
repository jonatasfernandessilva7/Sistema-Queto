import os
import sys
import sqlite3

# ensure project root is importable so `src` package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backend.repository import GenericsRepository as repo


def test_save_report_with_document(monkeypatch):
    # Override connect_db to use in-memory sqlite for tests
    def connect_db_override():
        return sqlite3.connect(':memory:')

    monkeypatch.setattr(repo, 'connect_db', connect_db_override)

    # Initialize schema in the in-memory DB
    repo.create_tables()

    # Insert a document to relate the report to
    with repo.connect_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO documentos (filename, origem, conteudo, timestamp) VALUES (?, ?, ?, ?)",
                    ("test.pdf", "local", sqlite3.Binary(b'data'), "ts"))
        conn.commit()
        doc_id = cur.lastrowid

    # Save report linked to the inserted document
    report_id = repo.saveReport(doc_id, b'report bytes')
    assert report_id > 0

    # Verify stored report
    with repo.connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT documento_id, relatorio FROM analise_de_documentos WHERE id = ?", (report_id,))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == doc_id
        assert row[1] == b'report bytes'
