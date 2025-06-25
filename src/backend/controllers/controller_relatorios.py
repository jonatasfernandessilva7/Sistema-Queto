from src.backend.services.service_relatorios import ver_todos_os_relatorios, upload_relatorio

def get_relatorios():
    try:

        resultado = ver_todos_os_relatorios()

        if not resultado:

            return False

        return resultado

    except Exception as e:

        return e

def salva_os_relatorios(data:dict) -> dict:
    documento_id = data.get("documento_id")
    conteudo = data.get("conteudo")

    if not isinstance(documento_id, int) or not isinstance(conteudo, str):
        return {"status": "error",
                "message": "ID do documento e conteúdo do relatório são obrigatórios e devem ser do tipo correto."}

    resultado = upload_relatorio(documento_id, conteudo)
    if resultado["success"]:
        return {"status": "success", "message": resultado["message"], "report_id": resultado.get("report_id")}
    else:
        return {"status": "error", "message": resultado["message"]}