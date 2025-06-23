from src.backend.db.db import get_all_relatorios

def ver_todos_os_relatorios():
    documentos = get_all_relatorios()

    try:

        if not documentos:

            return False

        return documentos

    except Exception as e:

        return e