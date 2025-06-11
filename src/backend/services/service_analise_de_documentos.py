import os
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
from src.backend.services.service_llama_api import llama_api_call

# 1. Extrair texto de PDF
def extrair_texto(pdf_path):
    texto = ""
    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() or ""
    return texto

# 2. Extrair tabelas
def extrair_tabelas(pdf_path):
    tabelas_extraidas = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, pagina in enumerate(pdf.pages):
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                tabelas_extraidas.append({"pagina": i+1, "tabela": tabela})
    return tabelas_extraidas

# 3. Extrair imagens
def extrair_imagens(pdf_path, output_dir="imagens_extraidas"):
    os.makedirs(output_dir, exist_ok=True)
    imagens = convert_from_path(pdf_path)
    caminhos = []
    for i, img in enumerate(imagens):
        caminho = os.path.join(output_dir, f"pagina_{i+1}.png")
        img.save(caminho, "PNG")
        caminhos.append(caminho)
    return caminhos

# 4. OCR em imagens
def aplicar_ocr(imagens):
    textos_ocr = []
    for img_path in imagens:
        texto = pytesseract.image_to_string(Image.open(img_path), lang="por")
        textos_ocr.append((img_path, texto))
    return textos_ocr

# 5. Análise semântica com LLM (resumo)
async def resumir_texto(texto: str) -> str:
    prompt = f"Resuma de forma clara, concisa e informativa o seguinte texto extraído de um PDF:\n\n{texto}"
    return await llama_api_call(prompt)

# 6. Busca semântica com embeddings
def busca_semantica(texto, consulta, modelo_nome="all-MiniLM-L6-v2"):
    modelo = SentenceTransformer(modelo_nome)
    emb_texto = modelo.encode([texto], convert_to_tensor=True)
    emb_query = modelo.encode([consulta], convert_to_tensor=True)
    similaridade = util.pytorch_cos_sim(emb_texto, emb_query)
    return similaridade.item()