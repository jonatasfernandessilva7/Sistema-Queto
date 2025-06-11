import os

from pathlib import Path
from fastapi import HTTPException
from typing import List
from fastapi.responses import JSONResponse
from src.backend.services.service_analise_de_documentos import extrair_imagens, extrair_tabelas, extrair_texto, resumir_texto

PDF_FOLDER = Path("../uploads")

async def analisar_pdf_local() -> List[dict]:

    if not os.path.exists(PDF_FOLDER):
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado.")

    for arquivo in PDF_FOLDER.glob("*.pdf"):

        try:
            texto = extrair_texto(arquivo)

            if not texto:
                texto = extrair_imagens(arquivo)

            if not texto:
                raise HTTPException(status_code=422, detail="Nenhum texto encontrado, mesmo após OCR.")

            tabelas = extrair_tabelas(arquivo)

            if tabelas:
                texto += "\n\nTabelas encontradas:\n" + tabelas

            resumo = await resumir_texto(texto[:3000])

            return JSONResponse(content={"arquivo": arquivo.name, "resumo": resumo, "tabelas extraídas": bool(tabelas)})

        except Exception as e:

            raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")