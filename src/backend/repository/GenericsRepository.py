import sqlite3
import json
import datetime
import os
from typing import Optional
import logging

from src.backend.database.ConnectionWithDatabase import connect_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Exception raised for database operation errors"""
    pass


class DocumentNotFoundError(DatabaseError):
    """Exception raised when document is not found"""
    pass


class ReportNotFoundError(DatabaseError):
    """Exception raised when report is not found"""
    pass

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
    if not system_name or not isinstance(system_name, str):
        logger.warning(f"Invalid system_name parameter: {system_name}")
        return "desconhecido"
    
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM sistemas WHERE nome = ?", (system_name,))
            result = cursor.fetchone()
            return result['status'] if result else "desconhecido"
    except sqlite3.Error as e:
        logger.error(f"Database error in get_system_status: {e}")
        raise DatabaseError(f"Failed to get status for system {system_name}") from e
    except Exception as e:
        logger.error(f"Unexpected error in get_system_status: {e}")
        raise DatabaseError(f"Unexpected error getting system status") from e
    
def update_system_status(system_name: str, status: str):
    if not system_name or not isinstance(system_name, str):
        logger.warning(f"Invalid system_name parameter: {system_name}")
        raise ValueError("system_name must be a non-empty string")
    
    if not status or not isinstance(status, str):
        logger.warning(f"Invalid status parameter: {status}")
        raise ValueError("status must be a non-empty string")
    
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO sistemas (nome, status) VALUES (?,?)", (system_name, status))
            conn.commit()
            logger.info(f"System status updated: {system_name} -> {status}")
    except sqlite3.Error as e:
        logger.error(f"Database error in update_system_status: {e}")
        raise DatabaseError(f"Failed to update status for system {system_name}") from e
    except Exception as e:
        logger.error(f"Unexpected error in update_system_status: {e}")
        raise DatabaseError(f"Unexpected error updating system status") from e

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
    if not filename or not isinstance(filename, str):
        logger.warning(f"Invalid filename: {filename}")
        raise ValueError("filename must be a non-empty string")
    
    if not caminho_do_arquivo or not isinstance(caminho_do_arquivo, str):
        logger.warning(f"Invalid file path: {caminho_do_arquivo}")
        raise ValueError("caminho_do_arquivo must be a non-empty string")
    
    try:
        if not os.path.exists(caminho_do_arquivo):
            logger.error(f"File not found: {caminho_do_arquivo}")
            raise FileNotFoundError(f"O arquivo {filename} não foi encontrado em {caminho_do_arquivo}")
        
        timestamp = datetime.datetime.now().isoformat()

        with open(caminho_do_arquivo, 'rb') as f:
            pdf_binario = f.read()

        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO documentos (filename, origem, conteudo, timestamp) VALUES (?,?,?,?)", 
                         (filename, caminho_do_arquivo, sqlite3.Binary(pdf_binario), timestamp))
            conn.commit()
            doc_id = cursor.lastrowid
            logger.info(f"Document inserted successfully: {filename} (ID: {doc_id})")
            return doc_id
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        raise
    except IOError as e:
        logger.error(f"IO error while reading file {filename}: {e}")
        raise DatabaseError(f"Erro ao ler arquivo {filename}") from e
    except sqlite3.Error as e:
        logger.error(f"Database error while inserting document: {e}")
        raise DatabaseError(f"Erro ao inserir documento {filename} no banco") from e
    except Exception as e:
        logger.error(f"Unexpected error in add_documentos: {e}")
        raise DatabaseError(f"Erro inesperado ao adicionar documento") from e

async def get_documentos_by_id(doc_id: int):
    if not isinstance(doc_id, int) or doc_id <= 0:
        logger.warning(f"Invalid doc_id: {doc_id}")
        raise ValueError("doc_id must be a positive integer")
    
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT filename, conteudo FROM documentos WHERE id = ?", (doc_id,))
            resultQuery = cursor.fetchone()

        if resultQuery:
            filename = resultQuery[0]
            binary_content = resultQuery[1]
            logger.info(f"Document retrieved: {filename} (ID: {doc_id})")
            return filename, binary_content
        else:
            logger.warning(f"Document not found with ID: {doc_id}")
            raise DocumentNotFoundError(f"Documento com ID {doc_id} não encontrado")

    except DocumentNotFoundError:
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in get_documentos_by_id (ID: {doc_id}): {e}")
        raise DatabaseError(f"Erro ao recuperar documento") from e
    except Exception as e:
        logger.error(f"Unexpected error in get_documentos_by_id (ID: {doc_id}): {e}")
        raise DatabaseError(f"Erro inesperado ao recuperar documento") from e

async def get_all_documentos():
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, filename FROM documentos")

            resultQuery = cursor.fetchall()
            if not resultQuery:
                logger.info("No documents found in database")
                return []
            
            logger.info(f"Retrieved {len(resultQuery)} documents from database")
            return resultQuery
    
    except sqlite3.Error as e:
        logger.error(f"Database error in get_all_documentos: {e}")
        raise DatabaseError(f"Erro ao recuperar documentos do banco") from e
    except Exception as e:
        logger.error(f"Unexpected error in get_all_documentos: {e}")
        raise DatabaseError(f"Erro inesperado ao recuperar documentos") from e

def getAllReports():
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, documento_id, relatorio, timestamp "
                "FROM analise_de_documentos ORDER BY timestamp DESC"
            )
            rows = cursor.fetchall()

            if not rows:
                logger.info("No reports found in database")
                return []

            reports = []
            for row in rows:
                record = dict(row)
                # BLOB → string legível / base64 para serialização JSON
                raw = record.get("relatorio")
                if isinstance(raw, (bytes, bytearray)):
                    try:
                        record["relatorio"] = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        # PDF binário puro: expor como indicação e tamanho
                        record["relatorio"] = f"[PDF binário — {len(raw)} bytes]"
                        record["relatorio_size_bytes"] = len(raw)
                reports.append(record)

            logger.info("Retrieved %d reports from database", len(reports))
            return reports

    except sqlite3.Error as e:
        logger.error("Database error in getAllReports: %s", e)
        raise ReportNotFoundError("Erro ao recuperar relatórios do banco") from e
    except Exception as e:
        logger.error("Unexpected error in getAllReports: %s", e)
        raise ReportNotFoundError("Erro inesperado ao recuperar relatórios") from e

def delete_document_by_id(doc_id: int) -> bool:
    if not isinstance(doc_id, int) or doc_id <= 0:
        logger.warning(f"Invalid doc_id: {doc_id}")
        raise ValueError("doc_id must be a positive integer")
    
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT origem FROM documentos WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Document not found for deletion: ID={doc_id}")
                raise DocumentNotFoundError(f"Documento com ID {doc_id} não encontrado para exclusão")
            
            cursor.execute("DELETE FROM documentos WHERE id = ?", (doc_id,))
            conn.commit()
            
            if result and result[0]:
                file_path = result[0]
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"File deleted from disk: {file_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete file from disk {file_path}: {e}")
            
            deletion_successful = cursor.rowcount > 0
            if deletion_successful:
                logger.info(f"Document deleted from database: ID={doc_id}")
            return deletion_successful
            
    except (DocumentNotFoundError, ValueError):
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in delete_document_by_id (ID: {doc_id}): {e}")
        raise DatabaseError(f"Erro ao deletar documento do banco") from e
    except Exception as e:
        logger.error(f"Unexpected error in delete_document_by_id (ID: {doc_id}): {e}")
        raise DatabaseError(f"Erro inesperado ao deletar documento") from e


def saveReport(documento_id: Optional[int], report_content: bytes) -> int:
    """
    Persiste um relatório de crise no banco de dados.

    documento_id pode ser None para relatórios gerados a partir de áudio ou
    eventos de texto — nesses casos o relatório não está vinculado a um
    documento corporativo específico.
    """
    if not isinstance(report_content, bytes) or len(report_content) == 0:
        logger.warning("Invalid report_content: empty or not bytes")
        raise ValueError("report_content must be non-empty bytes")

    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO analise_de_documentos (documento_id, relatorio, timestamp) VALUES (?, ?, ?)",
                (documento_id, sqlite3.Binary(report_content), timestamp)
            )
            conn.commit()
            report_id = cursor.lastrowid
            logger.info(f"Report saved successfully: documento_id={documento_id}, report_id={report_id}")
            return report_id

    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error: documento_id={documento_id} might not exist: {e}")
        raise DatabaseError(f"Erro: documento com ID {documento_id} não existe") from e
    except sqlite3.Error as e:
        logger.error(f"Database error in saveReport: {e}")
        raise DatabaseError(f"Erro ao salvar relatório no banco") from e
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in saveReport: {e}")
        raise DatabaseError(f"Erro inesperado ao salvar relatório") from e


def update_document_by_id(doc_id: int, filename: str = None, content: bytes = None) -> bool:
    """
    Atualiza um documento corporativo existente.
    
    Parâmetros:
        doc_id: ID do documento a atualizar
        filename: Novo nome do arquivo (opcional)
        content: Novo conteúdo (bytes) - opcional
    
    Retorna:
        True se atualizado com sucesso
    """
    if not isinstance(doc_id, int) or doc_id <= 0:
        logger.warning(f"Invalid doc_id: {doc_id}")
        raise ValueError("doc_id must be a positive integer")
    
    if filename is None and content is None:
        raise ValueError("Pelo menos filename ou content deve ser fornecido para atualizar")
    
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Verificar se documento existe
            cursor.execute("SELECT id FROM documentos WHERE id = ?", (doc_id,))
            if not cursor.fetchone():
                logger.warning(f"Document not found for update: ID={doc_id}")
                raise DocumentNotFoundError(f"Documento com ID {doc_id} não encontrado")
            
            # Construir query de update dinamicamente
            update_fields = []
            params = []
            
            if filename is not None:
                update_fields.append("filename = ?")
                params.append(filename)
            
            if content is not None:
                update_fields.append("conteudo = ?")
                params.append(sqlite3.Binary(content))
            
            update_fields.append("timestamp = ?")
            params.append(datetime.datetime.now().isoformat())
            params.append(doc_id)
            
            query = f"UPDATE documentos SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Document updated successfully: ID={doc_id}")
            return success
            
    except (DocumentNotFoundError, ValueError):
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in update_document_by_id (ID: {doc_id}): {e}")
        raise DatabaseError(f"Erro ao atualizar documento") from e
    except Exception as e:
        logger.error(f"Unexpected error in update_document_by_id (ID: {doc_id}): {e}")
        raise DatabaseError(f"Erro inesperado ao atualizar documento") from e


def delete_report_by_id(report_id: int) -> bool:
    """
    Deleta um relatório gerado do banco de dados.
    
    Parâmetros:
        report_id: ID do relatório a deletar
    
    Retorna:
        True se deletado com sucesso
    """
    if not isinstance(report_id, int) or report_id <= 0:
        logger.warning(f"Invalid report_id: {report_id}")
        raise ValueError("report_id must be a positive integer")
    
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM analise_de_documentos WHERE id = ?", (report_id,))
            
            if not cursor.fetchone():
                logger.warning(f"Report not found for deletion: ID={report_id}")
                raise ReportNotFoundError(f"Relatório com ID {report_id} não encontrado")
            
            cursor.execute("DELETE FROM analise_de_documentos WHERE id = ?", (report_id,))
            conn.commit()
            
            deletion_successful = cursor.rowcount > 0
            if deletion_successful:
                logger.info(f"Report deleted from database: ID={report_id}")
            return deletion_successful
            
    except (ReportNotFoundError, ValueError):
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in delete_report_by_id (ID: {report_id}): {e}")
        raise DatabaseError(f"Erro ao deletar relatório do banco") from e
    except Exception as e:
        logger.error(f"Unexpected error in delete_report_by_id (ID: {report_id}): {e}")
        raise DatabaseError(f"Erro inesperado ao deletar relatório") from e


def update_report_by_id(report_id: int, new_content: bytes) -> bool:
    """
    Atualiza o conteúdo de um relatório existente.
    
    Parâmetros:
        report_id: ID do relatório a atualizar
        new_content: Novo conteúdo do relatório (bytes)
    
    Retorna:
        True se atualizado com sucesso
    """
    if not isinstance(report_id, int) or report_id <= 0:
        logger.warning(f"Invalid report_id: {report_id}")
        raise ValueError("report_id must be a positive integer")
    
    if not isinstance(new_content, bytes) or len(new_content) == 0:
        logger.warning("Invalid new_content: empty or not bytes")
        raise ValueError("new_content must be non-empty bytes")
    
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Verificar se relatório existe
            cursor.execute("SELECT id FROM analise_de_documentos WHERE id = ?", (report_id,))
            if not cursor.fetchone():
                logger.warning(f"Report not found for update: ID={report_id}")
                raise ReportNotFoundError(f"Relatório com ID {report_id} não encontrado")
            
            timestamp = datetime.datetime.now().isoformat()
            cursor.execute(
                "UPDATE analise_de_documentos SET relatorio = ?, timestamp = ? WHERE id = ?",
                (sqlite3.Binary(new_content), timestamp, report_id)
            )
            conn.commit()
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Report updated successfully: ID={report_id}")
            return success
            
    except (ReportNotFoundError, ValueError):
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error in update_report_by_id (ID: {report_id}): {e}")
        raise DatabaseError(f"Erro ao atualizar relatório") from e
    except Exception as e:
        logger.error(f"Unexpected error in update_report_by_id (ID: {report_id}): {e}")
        raise DatabaseError(f"Erro inesperado ao atualizar relatório") from e


def get_report_statistics() -> dict:
    """
    Retorna estatísticas dos relatórios para gráficos e dashboard.
    
    Retorna:
        dict contendo:
            - total_reports: Total de relatórios
            - reports_by_date: Relatórios agrupados por data
            - total_documents: Total de documentos
            - average_report_size: Tamanho médio dos relatórios (bytes)
    """
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Total de relatórios
            cursor.execute("SELECT COUNT(*) as count FROM analise_de_documentos")
            total_reports = cursor.fetchone()["count"]
            
            # Total de documentos
            cursor.execute("SELECT COUNT(*) as count FROM documentos")
            total_documents = cursor.fetchone()["count"]
            
            # Relatórios por data (últimos 30 dias)
            cursor.execute("""
                SELECT DATE(timestamp) as data, COUNT(*) as total
                FROM analise_de_documentos
                WHERE timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY data DESC
            """)
            reports_by_date = [
                {"data": row["data"], "total": row["total"]}
                for row in cursor.fetchall()
            ]
            
            # Tamanho médio dos relatórios
            cursor.execute("""
                SELECT AVG(LENGTH(relatorio)) as avg_size FROM analise_de_documentos
            """)
            avg_size_result = cursor.fetchone()
            average_report_size = avg_size_result["avg_size"] if avg_size_result["avg_size"] else 0
            
            logger.info(f"Report statistics retrieved: {total_reports} reports, {total_documents} documents")
            
            return {
                "total_reports": total_reports,
                "total_documents": total_documents,
                "reports_by_date": reports_by_date,
                "average_report_size_bytes": int(average_report_size),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
    except sqlite3.Error as e:
        logger.error(f"Database error in get_report_statistics: {e}")
        raise DatabaseError(f"Erro ao obter estatísticas dos relatórios") from e
    except Exception as e:
        logger.error(f"Unexpected error in get_report_statistics: {e}")
        raise DatabaseError(f"Erro inesperado ao obter estatísticas") from e
