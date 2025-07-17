import os
import pdfplumber
import pytesseract

from pdf2image import convert_from_path
from PIL import Image
from sentence_transformers import SentenceTransformer, util
from src.backend.utils.ConnectionWithLlamaApiGroqUtils import llama_api_call

def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_tables(pdf_path):
    extractedTables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            findTables = page.extract_tables()
            for table in findTables:
                extractedTables.append({"pagina": i+1, "table": table})
    return extractedTables

def extract_images(pdf_path, output_dir="extracted_images"):
    os.makedirs(output_dir, exist_ok=True)
    images = convert_from_path(pdf_path)
    imagesPath = []
    for i, img in enumerate(images):
        path = os.path.join(output_dir, f"page_{i+1}.png")
        img.save(path, "PNG")
        imagesPath.append(path)
    return imagesPath

def ocrMethod(imagens):
    ocrText = []
    for img_path in imagens:
        text = pytesseract.image_to_string(Image.open(img_path), lang="por")
        ocrText.append((img_path, text))
    return ocrText

async def resume_text(text: str) -> str:
    prompt = f"Clearly, concisely and informatively summarize the following text extracted from a PDF:\n\n{text}"
    return await llama_api_call(prompt)

def semanticSearch(texto, consulta, modelo_nome="all-MiniLM-L6-v2"):
    model = SentenceTransformer(modelo_nome)
    emb_texto = model.encode([texto], convert_to_tensor=True)
    emb_query = model.encode([consulta], convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(emb_texto, emb_query)
    return similarity.item()