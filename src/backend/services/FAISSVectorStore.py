"""
FAISS Vector Store for High-Performance Semantic Search
Implements conformidade C (compliance factor) and ISO similarity matching
"""

import numpy as np
import faiss
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Metadata for indexed documents"""
    doc_id: str
    title: str
    content: str
    type: str  # "corporate_policy", "iso_standard", "compliance_doc"
    conformance_weight: float = 0.5  # 0-1: importance for compliance
    timestamp: str = None
    source: str = None


@dataclass
class SearchResult:
    """Result from semantic search"""
    doc_id: str
    title: str
    content: str
    similarity_score: float
    conformance_impact: float
    type: str


class FAISSVectorStore:
    """
    FAISS-based vector store for semantic search with conformance calculation
    """

    def __init__(self, model_name: str = "sentence-transformers/multilingual-MiniLM-L12-v2"):
        """
        Initialize FAISS vector store with sentence-transformers model

        Args:
            model_name: Name of sentence-transformers model (512D embeddings)
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 512
        
        # FAISS indexes
        self.index = faiss.IndexFlatL2(self.embedding_dim)  # L2 distance
        self.documents: Dict[int, DocumentMetadata] = {}
        self.doc_counter = 0
        
        # ISO standards corpus (expanded)
        self.iso_standards = self._load_iso_standards()
        
        logger.info(f"FAISSVectorStore initialized with {model_name}")

    def _load_iso_standards(self) -> Dict[str, Dict]:
        """Load ISO standards corpus with conformance weights"""
        return {
            "ISO-22324": {
                "title": "ISO 22324:2015 - Societal Security - Crisis Management",
                "keywords": [
                    "crisis management", "organizational response", "crisis communication",
                    "stakeholder engagement", "decision-making", "monitoring", "recovery"
                ],
                "conformance_weight": 1.0,
                "category": "crisis_management"
            },
            "ISO-22361": {
                "title": "ISO 22361:2018 - Societal Security - Emergency Management",
                "keywords": [
                    "emergency management", "incident response", "continuity planning",
                    "resource management", "coordination", "recovery operations"
                ],
                "conformance_weight": 1.0,
                "category": "emergency_management"
            },
            "ISO-31000": {
                "title": "ISO 31000:2018 - Risk Management",
                "keywords": [
                    "risk assessment", "risk management", "mitigation strategies",
                    "control measures", "risk monitoring", "governance"
                ],
                "conformance_weight": 0.8,
                "category": "risk_management"
            },
            "ISO-27001": {
                "title": "ISO 27001:2022 - Information Security Management",
                "keywords": [
                    "information security", "cybersecurity", "data protection",
                    "access control", "security incident", "asset management"
                ],
                "conformance_weight": 0.9,
                "category": "information_security"
            },
            "ISO-9001": {
                "title": "ISO 9001:2015 - Quality Management System",
                "keywords": [
                    "quality management", "process management", "customer focus",
                    "leadership", "performance evaluation", "continuous improvement"
                ],
                "conformance_weight": 0.6,
                "category": "quality_management"
            }
        }

    async def index_document(self, 
                            content: str,
                            title: str,
                            doc_id: str,
                            doc_type: str = "corporate_policy",
                            conformance_weight: float = 0.5,
                            source: str = None) -> int:
        """
        Index a document with FAISS

        Args:
            content: Document content
            title: Document title
            doc_id: Unique document identifier
            doc_type: Type of document (corporate_policy, iso_standard, compliance_doc)
            conformance_weight: Compliance importance (0-1)
            source: Document source

        Returns:
            Index position in FAISS
        """
        try:
            # Encode text to embeddings
            embedding = self.model.encode(content, convert_to_numpy=True)
            
            # Add to FAISS index
            self.index.add(np.array([embedding], dtype=np.float32))
            
            # Store metadata
            metadata = DocumentMetadata(
                doc_id=doc_id,
                title=title,
                content=content,
                type=doc_type,
                conformance_weight=conformance_weight,
                timestamp=datetime.now().isoformat(),
                source=source
            )
            self.documents[self.doc_counter] = metadata
            
            logger.info(f"Indexed document: {doc_id} at position {self.doc_counter}")
            self.doc_counter += 1
            
            return self.doc_counter - 1
            
        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {str(e)}")
            raise

    async def search_similar_documents(self,
                                      query: str,
                                      top_k: int = 5,
                                      doc_type_filter: str = None) -> List[SearchResult]:
        """
        Search for similar documents using cosine similarity

        Args:
            query: Search query text
            top_k: Number of top results to return
            doc_type_filter: Filter by document type

        Returns:
            List of SearchResult objects
        """
        if self.index.ntotal == 0:
            logger.warning("No documents indexed for search")
            return []

        try:
            # Encode query
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            
            # Search FAISS index
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32),
                min(top_k, self.index.ntotal)
            )
            
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:  # Invalid index
                    continue
                    
                metadata = self.documents.get(int(idx))
                if not metadata:
                    continue
                
                # Apply type filter
                if doc_type_filter and metadata.type != doc_type_filter:
                    continue
                
                # Convert L2 distance to similarity score (0-1)
                similarity_score = 1.0 / (1.0 + distance)
                conformance_impact = similarity_score * metadata.conformance_weight
                
                results.append(SearchResult(
                    doc_id=metadata.doc_id,
                    title=metadata.title,
                    content=metadata.content[:500],  # Truncate for response
                    similarity_score=similarity_score,
                    conformance_impact=conformance_impact,
                    type=metadata.type
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise

    async def calculate_conformity_factor(self,
                                         transcript: str,
                                         corporate_documents: List[str] = None,
                                         iso_weights: Dict[str, float] = None) -> Tuple[float, Dict]:
        """
        Calculate conformidade C (compliance factor) based on:
        1. Similarity to corporate policies
        2. Alignment with ISO standards
        3. Risk-related language analysis

        Args:
            transcript: Crisis event transcript or report
            corporate_documents: List of corporate policy texts
            iso_weights: Custom ISO standard weights

        Returns:
            Tuple of (conformity_factor: 0-1, details: dict with breakdown)
        """
        try:
            transcript_embedding = self.model.encode(transcript, convert_to_numpy=True)
            
            details = {
                "corporate_policy_alignment": 0.0,
                "iso_alignment": 0.0,
                "risk_language_score": 0.0,
                "final_conformity_factor": 0.0,
                "matched_standards": []
            }
            
            # 1. Corporate policy alignment (40% weight)
            if corporate_documents:
                policy_similarities = []
                for policy_text in corporate_documents:
                    policy_embedding = self.model.encode(policy_text, convert_to_numpy=True)
                    # Cosine similarity
                    similarity = np.dot(transcript_embedding, policy_embedding) / (
                        np.linalg.norm(transcript_embedding) * np.linalg.norm(policy_embedding)
                    )
                    policy_similarities.append(max(0, similarity))  # Clamp to [0, 1]
                
                corporate_alignment = np.mean(policy_similarities) if policy_similarities else 0.0
                details["corporate_policy_alignment"] = float(corporate_alignment)
            
            # 2. ISO standards alignment (40% weight)
            iso_alignment_scores = []
            matched_standards = []
            
            for iso_id, iso_data in self.iso_standards.items():
                iso_keywords = iso_data["keywords"]
                keyword_matches = sum(
                    1 for keyword in iso_keywords 
                    if keyword.lower() in transcript.lower()
                ) / len(iso_keywords)
                
                iso_weight = iso_weights.get(iso_id, iso_data["conformance_weight"]) if iso_weights else iso_data["conformance_weight"]
                iso_score = keyword_matches * iso_weight
                iso_alignment_scores.append(iso_score)
                
                if keyword_matches > 0.1:
                    matched_standards.append({
                        "standard": iso_id,
                        "alignment": float(keyword_matches),
                        "title": iso_data["title"]
                    })
            
            iso_alignment = np.mean(iso_alignment_scores) if iso_alignment_scores else 0.0
            details["iso_alignment"] = float(iso_alignment)
            details["matched_standards"] = matched_standards
            
            # 3. Risk language analysis (20% weight)
            risk_keywords = [
                "crisis", "emergency", "threat", "incident", "risk", "hazard",
                "disaster", "attack", "breach", "failure", "outage", "disruption"
            ]
            risk_language_score = sum(
                1 for keyword in risk_keywords 
                if keyword.lower() in transcript.lower()
            ) / len(risk_keywords)
            details["risk_language_score"] = float(risk_language_score)
            
            # Final conformity factor (weighted average, inverted: high conformance = high factor)
            corporate_weight = 0.4
            iso_weight = 0.4
            risk_weight = 0.2
            
            conformity_factor = (
                corporate_weight * details["corporate_policy_alignment"] +
                iso_weight * details["iso_alignment"] +
                risk_weight * (1.0 - risk_language_score)  # Inverted: less risk language = more conformance
            )
            
            details["final_conformity_factor"] = float(conformity_factor)
            
            logger.info(f"Conformity calculation: {conformity_factor:.2%}")
            return conformity_factor, details
            
        except Exception as e:
            logger.error(f"Error calculating conformity factor: {str(e)}")
            return 0.5, {"error": str(e)}

    async def search_iso_similar_documents(self,
                                          query: str,
                                          iso_standard: str = None,
                                          top_k: int = 5) -> List[SearchResult]:
        """
        Search documents with ISO standard alignment scoring

        Args:
            query: Search query
            iso_standard: Filter by ISO standard (ISO-22324, ISO-27001, etc.)
            top_k: Number of results

        Returns:
            List of SearchResult with ISO conformance impact
        """
        results = await self.search_similar_documents(query, top_k)
        
        if iso_standard and iso_standard in self.iso_standards:
            iso_data = self.iso_standards[iso_standard]
            iso_keywords = iso_data["keywords"]
            
            # Re-score based on ISO alignment
            for result in results:
                keyword_matches = sum(
                    1 for keyword in iso_keywords 
                    if keyword.lower() in result.content.lower()
                ) / len(iso_keywords)
                
                result.conformance_impact = result.similarity_score * keyword_matches * iso_data["conformance_weight"]
        
        return sorted(results, key=lambda r: r.conformance_impact, reverse=True)

    async def get_conformity_report(self,
                                    transcript: str,
                                    top_k: int = 5) -> Dict:
        """
        Generate comprehensive conformity report

        Args:
            transcript: Crisis transcript
            top_k: Top documents to include

        Returns:
            Detailed conformity report
        """
        # Get conformity factor
        conformity_factor, conformity_details = await self.calculate_conformity_factor(transcript)
        
        # Get similar documents
        similar_docs = await self.search_similar_documents(transcript, top_k)
        
        # Get ISO alignment
        iso_results = await self.search_iso_similar_documents(transcript, top_k=top_k)
        
        return {
            "conformity_factor": conformity_factor,
            "conformity_details": conformity_details,
            "similar_documents": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "similarity": doc.similarity_score,
                    "conformance_impact": doc.conformance_impact,
                    "type": doc.type
                }
                for doc in similar_docs
            ],
            "iso_alignment": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "iso_similarity": doc.similarity_score,
                    "iso_conformance": doc.conformance_impact
                }
                for doc in iso_results
            ],
            "timestamp": datetime.now().isoformat()
        }

    def save_index(self, path: str):
        """Save FAISS index to disk"""
        try:
            faiss.write_index(self.index, path)
            # Save metadata
            metadata_path = path.replace(".faiss", "_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    k: {
                        "doc_id": v.doc_id,
                        "title": v.title,
                        "type": v.type,
                        "conformance_weight": v.conformance_weight
                    }
                    for k, v in self.documents.items()
                }, f, ensure_ascii=False)
            logger.info(f"Index saved to {path}")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")

    def load_index(self, path: str):
        """Load FAISS index from disk"""
        try:
            self.index = faiss.read_index(path)
            # Load metadata
            metadata_path = path.replace(".faiss", "_metadata.json")
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            self.documents = {
                int(k): DocumentMetadata(
                    doc_id=v["doc_id"],
                    title=v["title"],
                    content="",  # Loaded from DB as needed
                    type=v["type"],
                    conformance_weight=v["conformance_weight"]
                )
                for k, v in metadata_dict.items()
            }
            self.doc_counter = max(int(k) for k in metadata_dict.keys()) + 1
            logger.info(f"Index loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
