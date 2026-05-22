"""
Vector Search Service - C2M
Implementa busca semântica usando sentence-transformers (SBERT)

Responsabilidades:
- Gerar embeddings de documentos corporativos
- Calcular similaridade semântica (cosseno)
- Recuperar documentos similares (K-NN)
- Calcular fator de conformidade
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("sentence-transformers is required. Install with: pip install sentence-transformers")

from sklearn.metrics.pairwise import cosine_similarity
from src.backend.repository.GenericsRepository import get_all_documentos, get_documentos_by_id

log = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Resultado de uma busca vetorial"""
    document_id: int
    filename: str
    similarity_score: float
    content_preview: str
    is_match: bool  # True se similarity >= threshold


@dataclass
class ConformityAnalysisResult:
    """Resultado da análise de conformidade"""
    conformity_factor: float  # 0 a 1 (0 = em conformidade, 1 = divergente)
    similarity_score: float
    top_matches: List[VectorSearchResult]
    reasoning: str


class VectorSearchEngine:
    """
    Motor de busca vetorial usando sentence-transformers
    
    Modelo padrão: "distiluse-base-multilingual-case-sensitive-v2"
    - Suporta português
    - Rápido (distilled)
    - 512 dimensões
    """
    
    def __init__(self, model_name: str = "distiluse-base-multilingual-case-sensitive-v2"):
        """
        Inicializa o motor de busca
        
        Args:
            model_name: Nome do modelo sentence-transformer a usar
        """
        self.model_name = model_name
        try:
            self.model = SentenceTransformer(model_name)
            log.info(f"Modelo carregado: {model_name}")
        except Exception as e:
            log.error(f"Erro ao carregar modelo {model_name}: {e}")
            raise
        
        # Cache de embeddings (em produção, usar Redis/FAISS)
        self._embedding_cache: Dict[int, np.ndarray] = {}
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Gera embedding para um texto
        
        Args:
            text: Texto a codificar
        
        Returns:
            Vector embedding (numpy array)
        """
        if not text or not isinstance(text, str):
            log.warning(f"Texto inválido para encode: {text}")
            return np.zeros(self.model.get_sentence_embedding_dimension())
        
        try:
            embedding = self.model.encode(text.strip(), convert_to_numpy=True)
            return embedding
        except Exception as e:
            log.error(f"Erro ao encodar texto: {e}")
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calcula similaridade de cosseno entre dois embeddings
        
        Fórmula:
        sim = (A · B) / (||A|| × ||B||)
        
        Range: [0, 1] onde 1 = idêntico, 0 = ortogonal
        
        Args:
            embedding1, embedding2: Vetores numpy
        
        Returns:
            Score de similaridade [0, 1]
        """
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        try:
            # cosine_similarity retorna matriz 1x1
            similarity = cosine_similarity([embedding1], [embedding2])[0, 0]
            return float(np.clip(similarity, 0.0, 1.0))
        except Exception as e:
            log.error(f"Erro ao calcular similaridade: {e}")
            return 0.0
    
    async def search_similar_documents(
        self,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[VectorSearchResult]:
        """
        Busca os K documentos mais similares a um texto
        
        Args:
            query_text: Texto de consulta
            top_k: Número de resultados (padrão: 5)
            similarity_threshold: Mínimo de similaridade (padrão: 0.3)
        
        Returns:
            Lista de VectorSearchResult ordenada por similaridade (DESC)
        """
        log.info(f"Buscando {top_k} documentos similares a: '{query_text[:100]}...'")
        
        # Gerar embedding da query
        query_embedding = self.encode_text(query_text)
        
        # Buscar todos os documentos
        try:
            documentos = await get_all_documentos()
        except Exception as e:
            log.error(f"Erro ao buscar documentos: {e}")
            return []
        
        if not documentos:
            log.warning("Nenhum documento disponível no repositório")
            return []
        
        # Calcular similaridade para cada documento
        results = []
        for doc in documentos:
            doc_id = doc.get('id')
            filename = doc.get('filename', 'unknown')
            content = doc.get('content', '')
            
            # Usar cache ou gerar embedding
            if doc_id in self._embedding_cache:
                doc_embedding = self._embedding_cache[doc_id]
            else:
                doc_embedding = self.encode_text(content)
                self._embedding_cache[doc_id] = doc_embedding
            
            # Calcular similaridade
            similarity = self.cosine_similarity(query_embedding, doc_embedding)
            
            # Filtrar por threshold
            if similarity >= similarity_threshold:
                preview = content[:200] + "..." if len(content) > 200 else content
                result = VectorSearchResult(
                    document_id=doc_id,
                    filename=filename,
                    similarity_score=similarity,
                    content_preview=preview,
                    is_match=True
                )
                results.append(result)
        
        # Ordenar por similaridade (descendente)
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Retornar top_k
        top_results = results[:top_k]
        
        log.info(f"Encontrados {len(top_results)} documentos similares")
        for i, result in enumerate(top_results, 1):
            log.debug(f"  {i}. {result.filename} (score: {result.similarity_score:.3f})")
        
        return top_results
    
    def calculate_conformity_factor(
        self,
        transcript_text: str,
        corporate_documents: List[str] = None,
        top_k: int = 5
    ) -> float:
        """
        Calcula o fator de conformidade C (0 a 1)
        
        Conforme context.md seção 5.2:
        C = 1 - (similaridade média com K documentos mais similares)
        
        C ≈ 0: Totalmente em conformidade com políticas
        C ≈ 1: Totalmente divergente
        
        Args:
            transcript_text: Transcrição/texto do evento
            corporate_documents: Lista de documentos corporativos (se None, busca DB)
            top_k: Número de documentos para média (padrão: 5)
        
        Returns:
            Fator de conformidade [0, 1]
        """
        log.info("Calculando fator de conformidade...")
        
        transcript_embedding = self.encode_text(transcript_text)
        
        if corporate_documents is None:
            # Buscar documentos do repositório
            try:
                docs = get_all_documentos()
                if isinstance(docs, dict):  # async future
                    import asyncio
                    docs = asyncio.run(docs)
                corporate_documents = [doc.get('content', '') for doc in docs]
            except Exception as e:
                log.warning(f"Erro ao buscar documentos corporativos: {e}")
                return 0.5  # Retornar valor neutro
        
        if not corporate_documents:
            log.warning("Nenhum documento corporativo disponível")
            return 0.5
        
        # Calcular similaridade com cada documento
        similarities = []
        for doc_text in corporate_documents:
            doc_embedding = self.encode_text(doc_text)
            similarity = self.cosine_similarity(transcript_embedding, doc_embedding)
            similarities.append(similarity)
        
        # Média dos top_k mais similares
        top_similarities = sorted(similarities, reverse=True)[:top_k]
        average_similarity = np.mean(top_similarities) if top_similarities else 0.0
        
        # C = 1 - similaridade_média
        conformity_factor = 1.0 - average_similarity
        conformity_factor = float(np.clip(conformity_factor, 0.0, 1.0))
        
        log.info(f"Fator de conformidade calculado: {conformity_factor:.3f}")
        log.debug(f"  Similaridade média top-{top_k}: {average_similarity:.3f}")
        
        return conformity_factor
    
    async def analyze_conformity_detailed(
        self,
        transcript_text: str,
        top_k: int = 5
    ) -> ConformityAnalysisResult:
        """
        Análise detalhada de conformidade com múltiplas dimensões
        
        Args:
            transcript_text: Texto a analisar
            top_k: Número de documentos para busca
        
        Returns:
            ConformityAnalysisResult com detalhes
        """
        # Buscar documentos similares
        similar_docs = await self.search_similar_documents(
            query_text=transcript_text,
            top_k=top_k,
            similarity_threshold=0.0  # Trazer todos para análise
        )
        
        # Calcular similaridade média
        if similar_docs:
            avg_similarity = np.mean([d.similarity_score for d in similar_docs])
        else:
            avg_similarity = 0.0
        
        # Fator de conformidade
        conformity_factor = 1.0 - avg_similarity
        
        # Reasoning
        if conformity_factor < 0.2:
            reasoning = "Evento ALTAMENTE conformante com políticas internas"
        elif conformity_factor < 0.4:
            reasoning = "Evento conformante com algumas discrepâncias menores"
        elif conformity_factor < 0.6:
            reasoning = "Evento parcialmente divergente das políticas"
        elif conformity_factor < 0.8:
            reasoning = "Evento SIGNIFICATIVAMENTE divergente"
        else:
            reasoning = "Evento COMPLETAMENTE divergente das políticas"
        
        return ConformityAnalysisResult(
            conformity_factor=conformity_factor,
            similarity_score=avg_similarity,
            top_matches=similar_docs[:top_k],
            reasoning=reasoning
        )
    
    def clear_cache(self) -> None:
        """Limpa o cache de embeddings (para libertar memória)"""
        self._embedding_cache.clear()
        log.info("Cache de embeddings limpo")
    
    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        return {
            "cached_documents": len(self._embedding_cache),
            "model": self.model_name,
            "embedding_dimension": self.model.get_sentence_embedding_dimension()
        }


# Instância global (singleton)
_vector_engine: Optional[VectorSearchEngine] = None


def get_vector_engine() -> VectorSearchEngine:
    """Retorna instância singleton do motor de busca"""
    global _vector_engine
    if _vector_engine is None:
        _vector_engine = VectorSearchEngine()
    return _vector_engine


async def search_documents(
    query: str,
    top_k: int = 5,
    threshold: float = 0.3
) -> List[VectorSearchResult]:
    """
    Helper function para buscar documentos
    """
    engine = get_vector_engine()
    return await engine.search_similar_documents(query, top_k, threshold)


def calculate_conformity(transcript: str, top_k: int = 5) -> float:
    """
    Helper function para calcular conformidade
    """
    engine = get_vector_engine()
    return engine.calculate_conformity_factor(transcript, top_k=top_k)
