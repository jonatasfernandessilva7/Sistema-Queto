from src.backend.repository.GenericsRepository import saveReport, getAllReports

def reportUpload(documentId, documentContent):
    if not isinstance(documentId, int) or documentId <= 0:
        return {"success": False, "message": "ID of document is invalid to report."}
    if not isinstance(documentContent, str) or not documentContent.strip():
        return {"success": False, "message": "Content of report can empty."}

    report_bytes = documentContent.encode('utf-8')

    result = saveReport(documentId, report_bytes)
    return result

def viewAllReports():
    reports = getAllReports()

    if reports is not None:
        for reports in reports:
            if isinstance(reports.get('relatorios'), bytes):
                try:
                    reports['relatorio'] = reports['relatorio'].decode('utf8')
                except UnicodeError:
                    reports['relatorio'] = "binary content invalid"

        return {"success": True, "reports": reports, "message": "are ok"}
    else:
        return {"success": False, "reports": [], "message": "reports not found"}