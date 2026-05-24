import os
import asyncio
import logging
import pdfplumber
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from pdf2image import convert_from_path
from PIL import Image
from sentence_transformers import SentenceTransformer, util
from src.core.utils.llama_api_utils import llama_api_call

log = logging.getLogger(__name__)

# Thread pool for blocking operations
_thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="DocumentAnalysis")

def _extract_text_sync(pdf_path):
    """Synchronous PDF text extraction (runs in thread pool)."""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    except Exception as e:
        log.error(f"Error extracting text from {pdf_path}: {e}")
        raise

async def extract_text(pdf_path):
    """
    Asynchronously extract text from PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_thread_pool, _extract_text_sync, pdf_path)
    except Exception as e:
        log.error(f"Failed to extract text: {e}")
        raise

def _extract_tables_sync(pdf_path):
    """Synchronous table extraction (runs in thread pool)."""
    try:
        extractedTables = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                findTables = page.extract_tables()
                if findTables:
                    for table in findTables:
                        extractedTables.append({"pagina": i+1, "table": table})
        return extractedTables
    except Exception as e:
        log.error(f"Error extracting tables from {pdf_path}: {e}")
        raise

async def extract_tables(pdf_path):
    """
    Asynchronously extract tables from PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of extracted tables with page numbers
    """
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_thread_pool, _extract_tables_sync, pdf_path)
    except Exception as e:
        log.error(f"Failed to extract tables: {e}")
        raise

def _extract_images_sync(pdf_path, output_dir="extracted_images"):
    """Synchronous image extraction (runs in thread pool)."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        images = convert_from_path(pdf_path)
        imagesPath = []
        for i, img in enumerate(images):
            path = os.path.join(output_dir, f"page_{i+1}.png")
            img.save(path, "PNG")
            imagesPath.append(path)
        return imagesPath
    except Exception as e:
        log.error(f"Error extracting images from {pdf_path}: {e}")
        raise

async def extract_images(pdf_path, output_dir="extracted_images"):
    """
    Asynchronously extract images from PDF.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images
        
    Returns:
        List of paths to extracted images
    """
    loop = asyncio.get_event_loop()
    try:
        extract_func = partial(_extract_images_sync, pdf_path, output_dir)
        return await loop.run_in_executor(_thread_pool, extract_func)
    except Exception as e:
        log.error(f"Failed to extract images: {e}")
        raise

def _ocr_method_sync(imagens):
    """Synchronous OCR processing (runs in thread pool)."""
    try:
        ocrText = []
        for img_path in imagens:
            try:
                text = pytesseract.image_to_string(Image.open(img_path), lang="por")
                ocrText.append((img_path, text))
            except Exception as e:
                log.warning(f"Error processing OCR for {img_path}: {e}")
                ocrText.append((img_path, f"OCR Error: {str(e)}"))
        return ocrText
    except Exception as e:
        log.error(f"Error in OCR processing: {e}")
        raise

async def ocrMethod(imagens):
    """
    Asynchronously process OCR on images.
    
    Args:
        imagens: List of image paths
        
    Returns:
        List of tuples (image_path, ocr_text)
    """
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_thread_pool, _ocr_method_sync, imagens)
    except Exception as e:
        log.error(f"Failed to process OCR: {e}")
        raise

async def resume_text(text: str) -> str:
    """
    Asynchronously summarize text using LLM.
    
    Args:
        text: Text to summarize
        
    Returns:
        Summarized text
    """
    try:
        prompt = f"Clearly, concisely and informatively summarize the following text extracted from a PDF:\n\n{text}"
        return await llama_api_call(prompt)
    except Exception as e:
        log.error(f"Error summarizing text: {e}")
        raise

def _semantic_search_sync(texto, consulta, modelo_nome="all-MiniLM-L6-v2"):
    """Synchronous semantic search (runs in thread pool)."""
    try:
        model = SentenceTransformer(modelo_nome)
        emb_texto = model.encode([texto], convert_to_tensor=True)
        emb_query = model.encode([consulta], convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(emb_texto, emb_query)
        return float(similarity.item())
    except Exception as e:
        log.error(f"Error in semantic search: {e}")
        raise

async def semanticSearch(texto, consulta, modelo_nome="all-MiniLM-L6-v2"):
    """
    Asynchronously perform semantic search.
    
    Args:
        texto: Text to search in
        consulta: Query/search phrase
        modelo_nome: Name of the sentence transformer model to use
        
    Returns:
        Similarity score (0-1)
    """
    loop = asyncio.get_event_loop()
    try:
        search_func = partial(_semantic_search_sync, texto, consulta, modelo_nome)
        return await loop.run_in_executor(_thread_pool, search_func)
    except Exception as e:
        log.error(f"Failed to perform semantic search: {e}")
        raise

def shutdown_executor():
    """Shutdown the thread pool executor. Call on application shutdown."""
    _thread_pool.shutdown(wait=True)
    log.info("DocumentAnalysis thread pool executor shut down")