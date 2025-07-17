from pathlib import Path
from fastapi import HTTPException
from typing import List, Dict
from fastapi.responses import JSONResponse
from src.backend.services.DocumentAnalysisService import (
    extract_images,
    extract_tables,
    extract_text,
    resume_text
)

COMPANY_FILE_FOLDER = Path("../uploads")

async def pdf_local_analysis() -> JSONResponse:
    if not COMPANY_FILE_FOLDER.exists() or not COMPANY_FILE_FOLDER.is_dir():
        raise HTTPException(status_code=404,
                            detail=f"The PDFs directory '{COMPANY_FILE_FOLDER.resolve()}' not found.")

    all_results: List[Dict] = []

    company_files_folder = list(COMPANY_FILE_FOLDER.glob("*.pdf"))
    if not company_files_folder:
        return JSONResponse(
            content={"message": "No PDFs found.", "results": []})

    for company_file in company_files_folder:
        try:
            text = extract_text(company_file)
            if not text:
                extracted_image_text = extract_images(company_file)
                if extracted_image_text:
                    text = extracted_image_text
                else:
                    raise HTTPException(status_code=422,
                                        detail=f"No text found in company files '{company_file.name}', same after OCR.")

            extracted_tables = extract_tables(company_file)
            text_tables = ""
            if extracted_tables:
                text_tables = "\n\nTables found:\n" + "\n".join([str(t) for t in extracted_tables])

            full_text_to_summarize = text
            if text_tables:
                full_text_to_summarize += text_tables

            resume = await resume_text(full_text_to_summarize[:3000])

            all_results.append({
                "company_file": company_file.name,
                "resume": resume,
                "extracted_tables": bool(extracted_tables)
            })

        except HTTPException as http_e:
            all_results.append({
                "company_file": company_file.name,
                "status": "error",
                "details": http_e.detail
            })
        except Exception as e:
            all_results.append({
                "company_file": company_file.name,
                "status": "error",
                "details": f"Unexpected error: {str(e)}"
            })

    return JSONResponse(
        content=
        {
            "status": 200,
            "message": "Company files analysis completed.",
            "results": all_results
        }
    )
