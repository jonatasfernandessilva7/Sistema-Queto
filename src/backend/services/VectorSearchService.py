"""
Responsabilidades:
  - Gerar embeddings de documentos corporativos (sentence-transformers)
  - Calcular similaridade coseno entre transcrição e documentos
  - Computar fator de conformidade C ∈ [0, 1] (seção 4.3 do artigo)
  - Fornecer calculate_conformity() síncrono para uso no Orchestrator

Modelo: distiluse-base-multilingual-cased-v2
  - Suporta português nativamente
  - 512 dimensões
  - Adequado para documentos corporativos PT/EN

Fórmula (seção 4.3):
  sim(t, d_i) = (E(t) · E(d_i)) / (‖E(t)‖ · ‖E(d_i)‖)
  C = 1 − (1/k) Σᵢ₌₁ᵏ sim(t, d_i)
  C ≈ 0 → conformidade com políticas
  C ≈ 1 → divergência das políticas
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "sentence-transformers is required. "
        "Install with: pip install sentence-transformers"
    )

from src.backend.repository.GenericsRepository import get_all_documentos, get_documentos_by_id

log = logging.getLogger(__name__)

_MODEL_NAME = "distiluse-base-multilingual-cased-v2"
_DEFAULT_TOP_K = 5
_SIMILARITY_THRESHOLD = 0.0  # trazer todos para análise de conformidade

@dataclass
class VectorSearchResult:
    """Resultado de uma busca vetorial."""
    document_id: int
    filename: str
    similarity_score: float
    content_preview: str
    is_match: bool


@dataclass
class ConformityAnalysisResult:
    """Resultado completo da análise de conformidade."""
    conformity_factor: float          # C ∈ [0, 1]
    mean_similarity: float            # média dos top-k sim scores
    top_matches: List[VectorSearchResult]
    reasoning: str

class VectorSearchEngine:
    """
    Motor de busca vetorial com cache de embeddings em memória.

    Thread-safety: o cache é protegido implicitamente pelo GIL do CPython
    para operações de leitura/escrita de dict; suficiente para uso I/O-bound.
    Em ambiente multi-processo, substituir por Redis.
    """

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self._dim: int = self.model.get_sentence_embedding_dimension()

        # doc_id → embedding numpy array
        self._embedding_cache: Dict[int, np.ndarray] = {}

        log.info("VectorSearchEngine inicializado: modelo=%s dim=%d", model_name, self._dim)

    def encode(self, text: str) -> np.ndarray:
        """Codifica texto como embedding normalizado."""
        if not text or not isinstance(text, str):
            return np.zeros(self._dim)
        try:
            emb = self.model.encode(
                text.strip(),
                convert_to_numpy=True,
                normalize_embeddings=True,  # cosine = dot product
            )
            return emb
        except Exception as exc:
            log.error("Erro ao codificar texto: %s", exc)
            return np.zeros(self._dim)

    # Similaridade

    @staticmethod
    def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        """Similaridade coseno ∈ [0, 1] entre dois vetores."""
        try:
            sim = cosine_similarity([a], [b])[0, 0]
            return float(np.clip(sim, 0.0, 1.0))
        except Exception:
            return 0.0

    # Cache 

    def invalidate_cache(self, doc_id: Optional[int] = None) -> None:
        """Remove um documento (ou todos) do cache de embeddings."""
        if doc_id is None:
            self._embedding_cache.clear()
            log.info("Cache de embeddings limpo por completo")
        else:
            self._embedding_cache.pop(doc_id, None)
            log.debug("Cache invalidado para doc_id=%d", doc_id)

    def get_cache_stats(self) -> Dict:
        return {
            "cached_documents": len(self._embedding_cache),
            "model": self.model_name,
            "embedding_dimension": self._dim,
        }

    # Extração de conteúdo do documento

    async def _get_doc_embedding(self, doc_id: int) -> Tuple[str, np.ndarray]:
        """
        Retorna (filename, embedding) para um doc_id.
        Usa cache; busca conteúdo binário do DB se necessário.
        """
        if doc_id in self._embedding_cache:
            # Não temos filename em cache — retornar placeholder
            return f"doc_{doc_id}", self._embedding_cache[doc_id]

        try:
            filename, content_bytes = await get_documentos_by_id(doc_id)
            if content_bytes is None:
                return f"doc_{doc_id}", np.zeros(self._dim)

            # Tentar decodificar como texto UTF-8
            try:
                text = content_bytes.decode("utf-8", errors="replace")
            except Exception:
                text = str(content_bytes)

            emb = self.encode(text[:8000])  # limitar para performance
            self._embedding_cache[doc_id] = emb
            return filename or f"doc_{doc_id}", emb
        except Exception as exc:
            log.warning("Erro ao buscar doc_id=%d: %s", doc_id, exc)
            return f"doc_{doc_id}", np.zeros(self._dim)

    async def search_similar_documents(
        self,
        query_text: str,
        top_k: int = _DEFAULT_TOP_K,
        threshold: float = _SIMILARITY_THRESHOLD,
    ) -> List[VectorSearchResult]:
        """Busca os top_k documentos mais similares a query_text."""
        query_emb = self.encode(query_text)

        try:
            docs = await get_all_documentos()
        except Exception as exc:
            log.error("Erro ao buscar documentos: %s", exc)
            return []

        if not docs:
            log.warning("Nenhum documento no repositório")
            return []

        results: List[VectorSearchResult] = []
        for row in docs:
            # GenericsRepository.get_all_documentos() retorna sqlite3.Row ou dict
            if isinstance(row, dict):
                doc_id   = row.get("id")
                filename = row.get("filename", "unknown")
            else:
                doc_id   = row[0]
                filename = row[1] if len(row) > 1 else "unknown"

            _, doc_emb = await self._get_doc_embedding(doc_id)
            sim = self.cosine_sim(query_emb, doc_emb)

            if sim >= threshold:
                results.append(
                    VectorSearchResult(
                        document_id=doc_id,
                        filename=filename,
                        similarity_score=sim,
                        content_preview=f"<doc_id={doc_id}>",
                        is_match=sim >= 0.3,
                    )
                )

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        top = results[:top_k]

        log.info(
            "VectorSearch: %d/%d documentos acima do threshold (top-%d)",
            len(results), len(docs), top_k,
        )
        return top

    # Conformity Factor 

    def calculate_conformity_factor(
        self,
        transcript_text: str,
        doc_texts: Optional[List[str]] = None,
        top_k: int = _DEFAULT_TOP_K,
    ) -> float:
        """

        Se doc_texts for fornecido, usa-os diretamente.
        Caso contrário, executa busca assíncrona em loop de eventos.

        C = 1 − (1/k) Σᵢ₌₁ᵏ sim(t, d_i)
        """
        transcript_emb = self.encode(transcript_text)

        if doc_texts is not None:
            # Caminho direto: textos fornecidos
            sims = [
                self.cosine_sim(transcript_emb, self.encode(dt))
                for dt in doc_texts
                if dt
            ]
        else:
            # Buscar do DB de forma síncrona
            try:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Já estamos dentro de um loop — usar thread executor
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            future = ex.submit(
                                asyncio.run,
                                self._fetch_all_embeddings(transcript_emb),
                            )
                            sims = future.result(timeout=30)
                    else:
                        sims = loop.run_until_complete(
                            self._fetch_all_embeddings(transcript_emb)
                        )
                except RuntimeError:
                    sims = asyncio.run(self._fetch_all_embeddings(transcript_emb))
            except Exception as exc:
                log.warning("Fallback: sem documentos para conformidade (%s)", exc)
                return 0.5  # valor neutro — sem documentos indexados

        if not sims:
            log.warning("VectorSearch: nenhum documento disponível — C=0.5 (neutro)")
            return 0.5

        top_k_sims = sorted(sims, reverse=True)[:top_k]
        avg_sim = float(np.mean(top_k_sims))
        C = float(np.clip(1.0 - avg_sim, 0.0, 1.0))

        log.info(
            "Conformity factor: C=%.4f (avg_sim_top%d=%.4f)",
            C, top_k, avg_sim,
        )
        return C

    async def _fetch_all_embeddings(self, query_emb: np.ndarray) -> List[float]:
        """Busca todos os embeddings do DB e retorna lista de similaridades."""
        try:
            docs = await get_all_documentos()
        except Exception:
            return []

        sims: List[float] = []
        for row in docs or []:
            doc_id = row[0] if not isinstance(row, dict) else row.get("id")
            if doc_id is None:
                continue
            _, doc_emb = await self._get_doc_embedding(doc_id)
            sims.append(self.cosine_sim(query_emb, doc_emb))
        return sims

    async def analyze_conformity_detailed(
        self,
        transcript_text: str,
        top_k: int = _DEFAULT_TOP_K,
    ) -> ConformityAnalysisResult:
        """Análise detalhada de conformidade com reasoning textual."""
        top_docs = await self.search_similar_documents(transcript_text, top_k=top_k)

        if top_docs:
            avg_sim = float(np.mean([d.similarity_score for d in top_docs]))
        else:
            avg_sim = 0.0

        C = float(np.clip(1.0 - avg_sim, 0.0, 1.0))

        if C < 0.2:
            reasoning = "Evento ALTAMENTE conformante com políticas internas"
        elif C < 0.4:
            reasoning = "Evento conformante com discrepâncias menores"
        elif C < 0.6:
            reasoning = "Evento parcialmente divergente das políticas"
        elif C < 0.8:
            reasoning = "Evento SIGNIFICATIVAMENTE divergente"
        else:
            reasoning = "Evento COMPLETAMENTE divergente das políticas"

        return ConformityAnalysisResult(
            conformity_factor=C,
            mean_similarity=avg_sim,
            top_matches=top_docs,
            reasoning=reasoning,
        )

_engine: Optional[VectorSearchEngine] = None


def get_vector_engine() -> VectorSearchEngine:
    """Retorna instância singleton (carregamento lazy)."""
    global _engine
    if _engine is None:
        _engine = VectorSearchEngine()
    return _engine

# Funções de convêniencia para uso externo 

def calculate_conformity(transcript: str, top_k: int = _DEFAULT_TOP_K) -> float:
    """
    Calcula fator de conformidade C para um transcript.
    Função síncrona — usada pelo Orchestrator no pipeline principal.
    """
    return get_vector_engine().calculate_conformity_factor(transcript, top_k=top_k)


async def search_documents(
    query: str,
    top_k: int = _DEFAULT_TOP_K,
    threshold: float = _SIMILARITY_THRESHOLD,
) -> List[VectorSearchResult]:
    """Busca documentos similares (helper assíncrono)."""
    return await get_vector_engine().search_similar_documents(query, top_k, threshold)


def invalidate_document_cache(doc_id: Optional[int] = None) -> None:
    """
    Remove documento(s) do cache de embeddings.

    Chamar após upload de novos documentos via DocumentController,
    para que o próximo cálculo de conformidade use os documentos atualizados.
    """
    if _engine is not None:
        _engine.invalidate_cache(doc_id)
