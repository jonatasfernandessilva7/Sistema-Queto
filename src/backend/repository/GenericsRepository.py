import sqlite3
import json
import datetime
import os

from src.backend.database.ConnectionWithDatabase import connect_db

def create_tables():

    with connect_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            '''
                CREATE TABLE IF NOT EXISTS sistemas (
                    nome TEXT PRIMARY KEY,
                    status TEXT
                )
            '''
        )

        cursor.execute(
            '''
                CREATE TABLE IF NOT EXISTS historico_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    tipo TEXT,
                    origem TEXT,
                    detalhes TEXT
                )
            '''
        )

        cursor.execute(
            '''
                 CREATE TABLE IF NOT EXISTS feedback_humano (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    timestamp TEXT,
                    llm_classification TEXT,
                    llm_priority TEXT,
                    human_classification TEXT,
                    human_priority TEXT,
                    comment TEXT,
                    FOREIGN KEY (event_id) REFERENCES historico_eventos(id)
                )
            '''
        )

        cursor.execute (
            '''
                CREATE TABLE IF NOT EXISTS documentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    origem TEXT,
                    conteudo BLOB NOT NULL,
                    timestamp TEXT
                )
            '''
        )

        cursor.execute (
            '''
                CREATE TABLE IF NOT EXISTS analise_de_documentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento_id INTEGER,
                    relatorio BLOB NOT NULL,
                    timestamp TEXT,
                    FOREIGN KEY (documento_id) REFERENCES documentos(id)
                )
            '''
        )

        cursor.execute("INSERT OR IGNORE INTO sistemas (nome, status) VALUES (?,?)", ('servidor_auth', 'operacional'))
        cursor.execute("INSERT OR IGNORE INTO sistemas (nome, status) VALUES (?,?)", ('banco_dados', 'operacional'))
        conn.commit()

def get_system_status(system_name: str) -> str:

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM sistemas WHERE nome = ?", (system_name))
        result = cursor.fetchone()
        return['status'] if result else "desconhecido"
    
def update_system_status(system_name: str, status: str):

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT TO REPLACE INTO sistemas (nome, status) VALUES (?,?)", (system_name, status))
        conn.commit()

def add_event_history(event_data: dict, timestamp: str):

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO historico_eventos (timestamp, tipo, origem, detalhes) VALUES (?, ?, ?, ?)",
            (timestamp, event_data['type'], event_data['origin'], json.dumps(event_data['details']))
        )
        conn.commit()
        return cursor.lastrowid

def get_event_history():

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, tipo, origem, detalhes FROM historico_eventos ORDER BY timestamp ASC")

            rows = cursor.fetchall()
            history = []

            for row in rows:
                event_dict = dict(row)
                event_dict['detalhes'] = json.loads(event_dict['detalhes'])
                history.append({"id": event_dict['id'], "evento": event_dict, "timestamp": event_dict['timestamp']})
            return history
    
def get_memory_state():

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, status FROM sistemas")
        systems = {row['nome']: row['status'] for row in cursor.fetchall()}
        history = get_event_history()
        return {"sistemas": systems, "historico_eventos": history}
    
def save_human_feedback(
    event_id: int,
    llm_classification: str,
    llm_priority: str, 
    human_classification: str,
    human_priority: str,
    comment: str = None
):
    with connect_db() as conn:

        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO feedback_humano (
                event_id, timestamp, llm_classification, llm_priority,
                human_classification, human_priority, comment
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id, timestamp, llm_classification, llm_priority,
                human_classification, human_priority, comment
            )
        )

        conn.commit()

def get_feedback_for_event_type(llm_classification: str, limit: int = 10):
     
     with connect_db() as conn:
         cursor = conn.cursor()
         cursor.execute("SELECT * FROM feedback_humano WHERE llm_classification = ? ORDER BY timestamp DESC LIMIT ?", (llm_classification, limit))
         return [dict(row) for row in cursor.fetchall()]
     
def add_documentos(filename, caminho_do_arquivo):
    
    try:
        timestamp = datetime.datetime.now().isoformat()

        with open(caminho_do_arquivo, 'rb') as f:
            pdf_binario = f.read()

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO documentos (filename, origem, conteudo, timestamp) VALUES (?,?,?,?)", (filename, caminho_do_arquivo, sqlite3.Binary(pdf_binario), timestamp))
            return "inserido com sucesso"
        
    except FileNotFoundError:
        return f"Erro: o arquivo {filename} não foi encontrado"

    except Exception as e:
        return e

async def get_documentos_by_id(doc_id: int):

    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT filename, conteudo FROM documentos WHERE id = ?", (doc_id,))
            resultQuery = cursor.fetchone()

        if resultQuery:
            filename = resultQuery[0]
            binary_content = resultQuery[1]
            return filename, binary_content
        else:
            return None, None

    except Exception as e:
        print(f"error in query execution (ID: {doc_id}): {e}")
        return None, None

async def get_all_documentos():

    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, filename FROM documentos") 

            resultQuery = cursor.fetchall()
            if not resultQuery:
                return False
            
            for id, nome in resultQuery:
                print(f"ID: {id}, Nome: {nome}")
                print("------------------------------")
            return resultQuery
    
    except Exception as e:
        return e

def getAllReports():

    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, documento_id, relatorio , timestamp FROM analise_de_documentos ORDER BY timestamp DESC")
            rows = cursor.fetchall()

            if not rows:
                return []

            reports = []

            for row in rows:
                reports.append(dict(row))
            return reports

    except Exception as e:
        print(f"Error find reports: {e}")
        raise

def delete_document_by_id(doc_id: int) -> bool:
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT origem FROM documentos WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            cursor.execute("DELETE FROM documentos WHERE id = ?", (doc_id,))
            conn.commit()
            if result and result[0]:
                file_path = result[0]
                if os.path.exists(file_path):
                    os.remove(file_path)
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error in deleted data (ID: {doc_id}): {e}")
        return False


def saveReport(documento_id: int, report_content: bytes) -> int:

    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO analise_de_documentos (documento_id, relatorio, timestamp) VALUES (?, ?, ?)",
                (documento_id, sqlite3.Binary(report_content), timestamp)
            )
            conn.commit()
            return cursor.lastrowid

    except Exception as e:
        print(f"Error in save report: {e}")
        return -1
