import sqlite3
import json
import os
import datetime

def connect_db():

    conn = sqlite3.connect(os.getenv('DATABASE_NAME'))
    conn.row_factory = sqlite3.Row

    return conn

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
                CREATE TABLE IF NOT EXISTS relatorios (
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
            (timestamp, event_data['tipo'], event_data['origem'], json.dumps(event_data['detalhes']))
        )

        conn.commit()

        return cursor.lastrowid

def get_event_history():

    with connect_db() as conn:

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

        sistemas = {row['nome']: row['status'] for row in cursor.fetchall()}
        historico = get_event_history()
        
        return {"sistemas": sistemas, "historico_eventos": historico}
    
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

def get_documentos_by_id(doc_id: int):
    """
    Retrieves the filename and binary content of a document from the database.

    Args:
        doc_id: The ID of the document to retrieve.

    Returns:
        A tuple (filename, binary_content) if found, otherwise (None, None).
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT filename, conteudo FROM documentos WHERE id = ?", (doc_id,))
            resultado = cursor.fetchone()

        if resultado:
            filename = resultado[0]
            binary_content = resultado[1]
            return filename, binary_content
        else:
            return None, None
    except Exception as e:
        print(f"Erro ao buscar documento no banco de dados (ID: {doc_id}): {e}")
        return None, None

def get_all_documentos():

    try:

        with connect_db() as conn:

            cursor = conn.cursor()

            cursor.execute("SELECT id, filename FROM documentos") 

            resultado = cursor.fetchall()

            if not resultado:

                return False
            
            for id, nome in resultado:

                print(f"ID: {id}, Nome: {nome}")
                print("------------------------------")

            return resultado
    
    except Exception as e:

        return e

def get_all_relatorios():

    try:
        with connect_db() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, documento_id, relatorio , timestamp FROM relatorios ORDER BY timestamp DESC")

            rows = cursor.fetchall()

            if not rows:
                return []

            relatorios = []
            for row in rows:
                relatorios.append(dict(row))

            return relatorios

    except Exception as e:
        print(f"Erro ao buscar todos os relatórios: {e}")
        raise

def delete_document_by_id(doc_id: int) -> bool:
    """
    Deletes a document record from the database by its ID.

    Args:
        doc_id: The ID of the document to delete.

    Returns:
        True if the document was successfully deleted, False otherwise.
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documentos WHERE id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erro ao deletar documento no banco de dados (ID: {doc_id}): {e}")
        return False


def save_report(documento_id: int, report_content: bytes) -> int:
    """
    Saves a new report to the 'relatorios' table.

    Args:
        documento_id: The ID of the document associated with this report.
        report_content: The binary content of the report (e.g., a generated PDF or text).

    Returns:
        The ID of the newly inserted report, or -1 if an error occurred.
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO relatorios (documento_id, relatorio, timestamp) VALUES (?, ?, ?)",
                (documento_id, sqlite3.Binary(report_content), timestamp)
            )
            conn.commit()
            return cursor.lastrowid  
    except Exception as e:
        print(f"Erro ao salvar relatório: {e}")
        return -1
