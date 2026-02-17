"""
Report Services - consolidated report generation and handling.
"""

from src.AiServices.services.AiReportsService import (
    AiGeneretadReportsWithLlama,
    AiSaveReports
)
from src.backend.services.ReportsService import (
    viewAllReports,
    reportUpload
)

__all__ = [
    # AI Report generation
    'AiGeneretadReportsWithLlama',
    'AiSaveReports',
    # Report viewing/uploading
    'viewAllReports',
    'reportUpload',
]
