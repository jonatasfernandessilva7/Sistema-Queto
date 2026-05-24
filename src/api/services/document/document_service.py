"""
Document Services - consolidated document handling services.
"""

from src.backend.services.DocumentService import (
    uploadDocumento,
    listarDocumentos,
    obterDocumentoPorID
)

__all__ = [
    'uploadDocumento',
    'listarDocumentos',
    'obterDocumentoPorID',
]
