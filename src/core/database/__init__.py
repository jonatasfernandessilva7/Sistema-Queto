"""
Database connection and repository access layer for core functionality.
Provides centralized access to database operations.
"""

# Re-export database functions from backend repository
from src.backend.database.ConnectionWithDatabase import connect_db
from src.backend.repository.GenericsRepository import (
    create_tables,
    get_system_status,
    update_system_status,
    add_event_history,
    get_event_history,
    get_memory_state,
    save_human_feedback,
    get_feedback_for_event_type,
    add_documentos,
    get_documentos_by_id,
    get_all_documentos,
    get_all_reports,
    delete_document_by_id
)

__all__ = [
    'connect_db',
    'create_tables',
    'get_system_status',
    'update_system_status',
    'add_event_history',
    'get_event_history',
    'get_memory_state',
    'save_human_feedback',
    'get_feedback_for_event_type',
    'add_documentos',
    'get_documentos_by_id',
    'get_all_documentos',
    'get_all_reports',
    'delete_document_by_id'
]
