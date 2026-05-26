from typing import Optional
from src.backend.repository.GenericsRepository import saveReport, getAllReports


def reportUpload(documentId: Optional[int], documentContent: str) -> dict:
    """
    Persiste um relatório no banco a partir de conteúdo textual.
    documentId pode ser None para relatórios não vinculados a documentos.
    """
    if not isinstance(documentContent, str) or not documentContent.strip():
        return {"success": False, "message": "Conteúdo do relatório não pode ser vazio."}

    report_bytes = documentContent.encode("utf-8")
    report_id = saveReport(documentId, report_bytes)
    return {"success": True, "report_id": report_id}


def viewAllReports() -> dict:
    """
    Retorna todos os relatórios do banco prontos para serialização JSON.
    A decodificação do BLOB é feita em getAllReports().
    """
    reports = getAllReports()

    if reports is None:
        return {"success": False, "reports": [], "message": "Erro ao recuperar relatórios."}

    return {"success": True, "reports": reports, "message": "OK"}
