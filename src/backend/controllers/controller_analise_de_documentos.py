import os
from pathlib import Path
from fastapi import HTTPException
from typing import List, Dict  # Importe Dict para a tipagem dos resultados
from fastapi.responses import JSONResponse
from src.backend.services.service_analise_de_documentos import extrair_imagens, extrair_tabelas, extrair_texto, \
    resumir_texto

PDF_FOLDER = Path("../uploads")


async def analisar_pdf_local() -> JSONResponse:
    if not PDF_FOLDER.exists() or not PDF_FOLDER.is_dir():
        raise HTTPException(status_code=404, detail=f"O diretório de PDFs '{PDF_FOLDER.resolve()}' não foi encontrado.")

    all_results: List[Dict] = []

    pdf_files = list(PDF_FOLDER.glob("*.pdf"))
    if not pdf_files:
        return JSONResponse(
            content={"message": "Nenhum arquivo PDF encontrado no diretório de uploads.", "results": []})

    for arquivo in pdf_files:
        try:
            texto = extrair_texto(arquivo)

            if not texto:
                # Tenta OCR se o texto inicial estiver vazio
                extracted_image_text = extrair_imagens(arquivo)
                if extracted_image_text:
                    texto = extracted_image_text
                else:
                    # Se ainda não houver texto, mesmo após OCR, levanta exceção para este arquivo
                    raise HTTPException(status_code=422,
                                        detail=f"Nenhum texto encontrado no arquivo '{arquivo.name}', mesmo após OCR.")

            tabelas_extraidas = extrair_tabelas(arquivo)  # Recebe as tabelas, não apenas um booleano
            tabelas_texto = ""
            if tabelas_extraidas:
                # Converte a lista de tabelas extraídas para uma string, se necessário
                # Dependendo do formato de retorno de extrair_tabelas, você pode precisar ajustar isso
                tabelas_texto = "\n\nTabelas encontradas:\n" + "\n".join([str(t) for t in tabelas_extraidas])

            # Combine texto e tabelas para o resumo
            full_text_to_summarize = texto
            if tabelas_texto:
                full_text_to_summarize += tabelas_texto

            # Limita o texto para o resumo para evitar sobrecarga da função
            resumo = await resumir_texto(full_text_to_summarize[:3000])

            # Adiciona o resultado da análise deste arquivo à lista
            all_results.append({
                "arquivo": arquivo.name,
                "resumo": resumo,
                "tabelas_extraidas": bool(tabelas_extraidas)
                # Retorna booleano para indicar se tabelas foram encontradas
            })

        except HTTPException as http_e:
            # Captura HTTPException lançada internamente (ex: 422) e adiciona ao resultado
            all_results.append({
                "arquivo": arquivo.name,
                "status": "erro",
                "detalhes": http_e.detail
            })
        except Exception as e:
            # Captura outras exceções e adiciona ao resultado
            all_results.append({
                "arquivo": arquivo.name,
                "status": "erro",
                "detalhes": f"Erro inesperado ao processar: {str(e)}"
            })

    # 2. Retorna a lista de todos os resultados APÓS o loop
    return JSONResponse(content={"message": "Análise de PDFs concluída.", "results": all_results})