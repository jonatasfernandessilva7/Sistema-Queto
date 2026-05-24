from src.api.services.reports import viewAllReports, reportUpload
from src.AiServices.services.AiReportsService import AiGenerateReportC2M
from fastapi.responses import JSONResponse

def get_reports():

    try:
        result = viewAllReports()
        if not result:
            return False
        return JSONResponse(content={"status":200, "message": "OK" ,"result":result})

    except Exception as e:
        return JSONResponse(content={"status": 500, "message": e})

def saveTheReports(data:dict) -> JSONResponse:
    document_id = data.get("documento_id")
    content_doc = data.get("conteudo")

    if not isinstance(document_id, int) or not isinstance(content_doc, str):
        return JSONResponse(content={
            "status": "error",
            "message": "Id of documents must correct."
        })

    result = reportUpload(document_id, content_doc)
    if result["success"]:
        return JSONResponse(content={"status": "success", "message": result["message"], "report_id": result.get("report_id")})
    else:
        return JSONResponse(content={"status": "error", "message": result["message"]})