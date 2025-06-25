from src.backend.db.db import save_report, get_all_relatorios

def upload_relatorio(documento_id, conteudo):
    if not isinstance(documento_id, int) or documento_id <= 0:
        return {"success": False, "message": "ID do documento inválido para o relatório."}
    if not isinstance(conteudo, str) or not conteudo.strip():
        return {"success": False, "message": "O conteúdo do relatório não pode estar vazio."}

    report_bytes = conteudo.encode('utf-8')  # Codifica a string para bytes para armazenamento BLOB

    result = save_report(documento_id, report_bytes)
    return result

def ver_todos_os_relatorios():
    relatorios = get_all_relatorios()

    if relatorios is not None:
        for relatorios in relatorios:
            if isinstance(relatorios.get('relatorios'), bytes):
                try:
                    relatorios['relatorio'] = relatorios['relatorio'].decode('utf8')
                except UnicodeError:
                    relatorios['relatorio'] = "conteudo binario nao decodificavel"

        return {"success": True, "relatorios": relatorios, "message": "tudo ok"}
    else:
        return {"success": False, "relatorios": [], "message": "não encontrei relatorios"}