from src.backend.services.service_relatorios import ver_todos_os_relatorios

def get_relatorios():
    try:

        resultado = ver_todos_os_relatorios()

        if not resultado:

            return False

        return resultado

    except Exception as e:

        return e