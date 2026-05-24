import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import asdict
import asyncio

try:
    from src.backend.services.FAISSVectorStore import FAISSVectorStore, SearchResult
except ImportError:
    raise ImportError("FAISSVectorStore is required. Check imports.")

log = logging.getLogger(__name__)


class VectorSearchServiceV2:
    """
    Enhanced vector search using FAISS
    Provides semantic search + conformidade C + ISO similarity
    """

    def __init__(self):
        """Initialize FAISS vector store"""
        self.faiss_store = FAISSVectorStore()
        self.indexed_documents = 0
        log.info("VectorSearchServiceV2 initialized with FAISS backend")

    async def index_corporate_documents(self,
                                       documents: List[Dict]) -> int:
        """
        Index corporate policy documents

        Args:
            documents: List of dicts with keys:
                      - content (str): document content
                      - title (str): document title
                      - doc_id (str): unique identifier
                      - conformance_weight (float, optional): 0-1 importance

        Returns:
            Number of documents indexed
        """
        count = 0
        for doc in documents:
            try:
                await self.faiss_store.index_document(
                    content=doc.get("content", ""),
                    title=doc.get("title", ""),
                    doc_id=doc.get("doc_id", f"doc_{count}"),
                    doc_type="corporate_policy",
                    conformance_weight=doc.get("conformance_weight", 0.5),
                    source=doc.get("source")
                )
                count += 1
            except Exception as e:
                log.error(f"Error indexing document: {e}")
                continue
        
        self.indexed_documents = count
        log.info(f"Indexed {count} corporate documents")
        return count

    async def search_similar_documents(self,
                                      query: str,
                                      top_k: int = 5,
                                      min_similarity: float = 0.0) -> List[Dict]:
        """
        Search for similar documents using FAISS

        Args:
            query: Search query text
            top_k: Number of results
            min_similarity: Minimum similarity threshold

        Returns:
            List of search results
        """
        results = await self.faiss_store.search_similar_documents(query, top_k)
        
        # Filter by similarity threshold
        filtered = [r for r in results if r.similarity_score >= min_similarity]
        
        return [
            {
                "doc_id": r.doc_id,
                "title": r.title,
                "content": r.content,
                "similarity_score": r.similarity_score,
                "conformance_impact": r.conformance_impact,
                "type": r.type
            }
            for r in filtered
        ]

    async def calculate_conformity_factor(self,
                                         transcript: str,
                                         corporate_documents: List[str] = None,
                                         iso_weights: Dict[str, float] = None) -> Dict:
        """
        Calculate conformidade C (compliance factor)

        Returns dict with:
        - conformity_factor: float (0-1)
        - corporate_alignment: float
        - iso_alignment: float
        - risk_score: float
        - matched_standards: list
        """
        conformity_factor, details = await self.faiss_store.calculate_conformity_factor(
            transcript=transcript,
            corporate_documents=corporate_documents,
            iso_weights=iso_weights
        )
        
        return {
            "conformity_factor": conformity_factor,
            **details
        }

    async def search_iso_standards(self,
                                   query: str,
                                   iso_standard: str = None,
                                   top_k: int = 5) -> List[Dict]:
        """
        Search with ISO standard alignment scoring

        Args:
            query: Search query
            iso_standard: Filter by ISO (ISO-22324, ISO-27001, etc.)
            top_k: Number of results

        Returns:
            Search results with ISO conformance impact
        """
        results = await self.faiss_store.search_iso_similar_documents(
            query=query,
            iso_standard=iso_standard,
            top_k=top_k
        )
        
        return [
            {
                "doc_id": r.doc_id,
                "title": r.title,
                "iso_conformance": r.conformance_impact,
                "similarity": r.similarity_score,
                "type": r.type
            }
            for r in results
        ]

    async def get_conformity_report(self,
                                    transcript: str,
                                    top_k: int = 5) -> Dict:
        """
        Get comprehensive conformity report

        Returns:
            Dict with conformity_factor, similar_docs, iso_alignment
        """
        report = await self.faiss_store.get_conformity_report(transcript, top_k)
        return report

    def save_index(self, path: str):
        """Save FAISS index to disk"""
        self.faiss_store.save_index(path)
        log.info(f"FAISS index saved to {path}")

    def load_index(self, path: str):
        """Load FAISS index from disk"""
        self.faiss_store.load_index(path)
        log.info(f"FAISS index loaded from {path}")


# Global instance
_vector_service_v2: Optional[VectorSearchServiceV2] = None


def get_vector_service_v2() -> VectorSearchServiceV2:
    """Get singleton instance of VectorSearchServiceV2"""
    global _vector_service_v2
    if _vector_service_v2 is None:
        _vector_service_v2 = VectorSearchServiceV2()
    return _vector_service_v2


# Async helper functions for use in routes
async def calculate_conformity_async(transcript: str) -> Dict:
    """Helper to calculate conformity"""
    service = get_vector_service_v2()
    return await service.calculate_conformity_factor(transcript)


async def search_iso_async(query: str, iso_id: str = None) -> List[Dict]:
    """Helper to search with ISO alignment"""
    service = get_vector_service_v2()
    return await service.search_iso_standards(query, iso_id)
