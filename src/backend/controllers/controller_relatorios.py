from src.backend.services.service_relatorios import ver_todos_os_relatorios, upload_relatorio
from fastapi.responses import JSONResponse

def get_relatorios():
    try:

        resultado = ver_todos_os_relatorios()

        if not resultado:

            return False

        return JSONResponse(content={"status":200, "message": "OK" ,"resultado":resultado})

    except Exception as e:

        return JSONResponse(content={"status": 500, "message": e})

def salva_os_relatorios(data:dict) -> JSONResponse:
    documento_id = data.get("documento_id")
    conteudo = data.get("conteudo")

    if not isinstance(documento_id, int) or not isinstance(conteudo, str):
        return JSONResponse(content={"status": "error",
                "message": "ID do documento e conteúdo do relatório são obrigatórios e devem ser do tipo correto."})

    resultado = upload_relatorio(documento_id, conteudo)
    if resultado["success"]:
        return JSONResponse(content={"status": "success", "message": resultado["message"], "report_id": resultado.get("report_id")})
    else:
        return JSONResponse(content={"status": "error", "message": resultado["message"]})