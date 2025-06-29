import os
import asyncio
from datetime import datetime
from pathlib import Path

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.backend.services.service_analise_de_documentos import extrair_texto, extrair_tabelas, extrair_imagens, aplicar_ocr, resumir_texto
from src.IA.services.service_relatorios import salvar_relatorio

UPLOAD_DIR = Path("analise_documentos")
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

class MonitorPDFsHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith(".pdf"):
            return
        asyncio.create_task(self.processar_pdf(event.src_path))

    async def processar_pdf(self, caminho_pdf):
        try:
            nome_arquivo = os.path.basename(caminho_pdf)
            print(f"Arquivo detectado: {nome_arquivo}")

            texto = extrair_texto(caminho_pdf)

            if not texto:
                imagens = extrair_imagens(caminho_pdf)
                textos_ocr = aplicar_ocr(imagens)
                texto = "\n".join([t[1] for t in textos_ocr])

            tabelas = extrair_tabelas(caminho_pdf)
            if tabelas:
                texto += "\n\nTabelas encontradas:\n" + "\n".join(str(t) for t in tabelas)

            resumo = await resumir_texto(texto[:3000])

            prioridade = "Moderada"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            salvar_relatorio(resumo, timestamp, prioridade)

            print(f"Relatório salvo com sucesso para {nome_arquivo}.")

        except Exception as e:
            print(f"Erro ao processar o arquivo: {e}")

async def monitorar_pasta():
    event_handler = MonitorPDFsHandler()
    observer = Observer()
    observer.schedule(event_handler, str(UPLOAD_DIR), recursive=False)
    observer.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    asyncio.run(monitorar_pasta())
