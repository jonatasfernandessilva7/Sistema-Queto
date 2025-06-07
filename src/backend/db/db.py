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
    llm_priority: str, # Adicione se você planeja armazenar a prioridade original do LLM
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