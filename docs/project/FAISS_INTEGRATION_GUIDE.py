"""
Integration instructions for FAISS VectorStore with FastAPI backend
This file shows how to integrate the new VectorSearchServiceV2 with existing endpoints
"""

# ============================================================================
# Step 1: Update src/backend/server.py to initialize FAISS
# ============================================================================

# Add this to your server.py imports section:
"""
from src.backend.services.VectorSearchServiceV2 import get_vector_service_v2
from contextlib import asynccontextmanager
"""

# Create a lifespan context manager for startup/shutdown:
"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize FAISS vector store
    print("Initializing FAISS Vector Store...")
    vector_service = get_vector_service_v2()
    
    # Load pre-existing FAISS index if available
    try:
        vector_service.load_index("data/faiss_index.bin")
        print(f"✅ FAISS index loaded. Documents indexed: {vector_service.indexed_documents}")
    except FileNotFoundError:
        print("⚠️  No existing FAISS index found. Will create on first document indexing.")
    
    yield
    
    # Shutdown: Save FAISS index
    print("Saving FAISS Vector Store...")
    vector_service.save_index("data/faiss_index.bin")
    print("✅ FAISS index saved")

# Add to FastAPI app:
app = FastAPI(
    title="Sistema-Queto C2M",
    description="Crisis Management System with AI Analysis",
    version="2.1",
    lifespan=lifespan
)
"""

# ============================================================================
# Step 2: Update api_v1_routes.py to use FAISS endpoints
# ============================================================================

# Add these new endpoints:
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from src.backend.services.VectorSearchServiceV2 import get_vector_service_v2

router = APIRouter(prefix="/api/v1", tags=["C2M"])

# -------- Vector Search Endpoints --------

class ConformityRequest(BaseModel):
    transcript: str
    corporate_documents: Optional[List[str]] = None


class ISOSearchRequest(BaseModel):
    query: str
    iso_standard: Optional[str] = None


@router.post("/vector/conformity")
async def get_conformity_analysis(request: ConformityRequest):
    '''
    Calculate conformidade C (compliance factor)
    
    Returns:
    - conformity_factor: 0-1 score
    - corporate_alignment: alignment with company policies
    - iso_alignment: alignment with ISO standards
    - matched_standards: list of applicable ISO standards
    '''
    service = get_vector_service_v2()
    
    result = await service.calculate_conformity_factor(
        transcript=request.transcript,
        corporate_documents=request.corporate_documents
    )
    
    return result


@router.post("/vector/iso-search")
async def search_iso_documents(
    request: ISOSearchRequest,
    top_k: int = Query(5, ge=1, le=20)
):
    '''
    Search for similar documents with ISO standard alignment
    
    Query parameters:
    - top_k: Number of results (1-20, default 5)
    
    Returns:
    - List of search results with ISO conformance impact
    '''
    service = get_vector_service_v2()
    
    results = await service.search_iso_standards(
        query=request.query,
        iso_standard=request.iso_standard,
        top_k=top_k
    )
    
    return results


@router.post("/vector/search")
async def search_documents(query: str, top_k: int = Query(5, ge=1, le=20)):
    '''
    General semantic search across indexed documents
    '''
    service = get_vector_service_v2()
    
    results = await service.search_similar_documents(
        query=query,
        top_k=top_k
    )
    
    return results


@router.post("/vector/report")
async def generate_conformity_report(request: ConformityRequest):
    '''
    Generate comprehensive conformity report
    
    Includes:
    - Conformity factor breakdown
    - Similar documents
    - ISO alignment analysis
    - Timestamp
    '''
    service = get_vector_service_v2()
    
    report = await service.get_conformity_report(
        transcript=request.transcript,
        top_k=5
    )
    
    return report


# -------- Document Management Endpoints --------

class DocumentIndexRequest(BaseModel):
    documents: List[dict]


@router.post("/vector/index-documents")
async def index_documents(request: DocumentIndexRequest):
    '''
    Index new documents into FAISS vector store
    
    Document format:
    {
        "content": "Document text",
        "title": "Document title",
        "doc_id": "unique_id",
        "conformance_weight": 0.5  # 0-1, optional
    }
    '''
    service = get_vector_service_v2()
    
    try:
        count = await service.index_corporate_documents(request.documents)
        
        # Save updated index
        service.save_index("data/faiss_index.bin")
        
        return {
            "status": "success",
            "documents_indexed": count,
            "message": f"Successfully indexed {count} documents"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector/index-status")
async def get_index_status():
    '''
    Get FAISS index status
    '''
    service = get_vector_service_v2()
    
    return {
        "documents_indexed": service.indexed_documents,
        "index_size": service.faiss_store.index.ntotal,
        "embedding_dimension": service.faiss_store.embedding_dim,
        "model": service.faiss_store.model.get_sentence_embedding_dimension()
    }


# -------- Integration with Existing Crisis Probability Endpoint --------

@router.post("/crisis/probability-enhanced")
async def calculate_crisis_probability_enhanced(request: CrisisProbabilityRequest):
    '''
    Enhanced crisis probability calculation with FAISS conformidade C
    
    Integrates:
    1. Decision Tree Analysis (existing)
    2. Monte Carlo Probability (existing)
    3. FAISS Conformidade C (new)
    4. ISO Standard Alignment (new)
    '''
    from src.agents.orchestrator.C2M_Orchestrator import C2MOrchestrator
    
    # Get existing C2M analysis
    orchestrator = C2MOrchestrator()
    c2m_result = await orchestrator.process_event(
        transcript=request.transcript,
        event_type=request.event_type,
        governance_level=request.governance_level
    )
    
    # Enhance with FAISS conformidade C
    vector_service = get_vector_service_v2()
    conformity_data = await vector_service.calculate_conformity_factor(
        transcript=request.transcript
    )
    
    # Combine results
    return {
        **c2m_result,
        "conformity_analysis": {
            "conformity_factor": conformity_data["conformity_factor"],
            "corporate_alignment": conformity_data.get("corporate_policy_alignment", 0),
            "iso_alignment": conformity_data.get("iso_alignment", 0),
            "matched_standards": conformity_data.get("matched_standards", [])
        }
    }
"""


# ============================================================================
# Step 3: Update requirements.txt with FAISS dependency
# ============================================================================

# Add to requirements.txt:
"""
# Vector Search (FAISS)
faiss-cpu>=1.8.0          # For CPU version (recommended)
# faiss-gpu>=1.8.0        # Uncomment for GPU version (requires CUDA)
"""

# Then install:
# pip install -r requirements.txt


# ============================================================================
# Step 4: Initialize corporate documents (startup script)
# ============================================================================

# Create src/scripts/init_faiss_index.py:

"""
import asyncio
from src.backend.services.VectorSearchServiceV2 import get_vector_service_v2


async def initialize_faiss_index():
    '''Initialize FAISS with sample corporate documents'''
    
    service = get_vector_service_v2()
    
    # Sample corporate documents
    documents = [
        {
            "content": '''
            CRISIS RESPONSE PROTOCOL v2.1
            
            Upon detection of a security incident or crisis:
            1. Activate incident response team immediately
            2. Notify executive leadership within 15 minutes
            3. Preserve evidence and logs
            4. Assess impact: confidentiality, integrity, availability
            5. Follow communication plan
            6. Document all actions taken
            ''',
            "title": "Crisis Response Protocol",
            "doc_id": "crisis_protocol_001",
            "conformance_weight": 0.95
        },
        {
            "content": '''
            INFORMATION SECURITY POLICY
            
            Security Requirements:
            - All data must be encrypted at rest and in transit
            - Regular security audits must be conducted
            - Access controls must be implemented and tested
            - Incident response procedures must be practiced quarterly
            - Employee security training mandatory annually
            - Third-party access must be monitored
            ''',
            "title": "Information Security Policy",
            "doc_id": "security_policy_001",
            "conformance_weight": 0.90
        },
        {
            "content": '''
            BUSINESS CONTINUITY AND RECOVERY PLAN
            
            Key Objectives:
            - Restore critical systems within 4 hours
            - Maintain communication with stakeholders
            - Preserve business reputation
            - Ensure legal/regulatory compliance
            - Document lessons learned
            
            Recovery Priority:
            1. Communication systems
            2. Payment processing
            3. Customer data access
            4. Reporting systems
            ''',
            "title": "Business Continuity Plan",
            "doc_id": "continuity_plan_001",
            "conformance_weight": 0.85
        }
    ]
    
    # Index documents
    count = await service.index_corporate_documents(documents)
    print(f"✅ Indexed {count} corporate documents")
    
    # Save FAISS index
    service.save_index("data/faiss_index.bin")
    print("✅ FAISS index saved to data/faiss_index.bin")


if __name__ == "__main__":
    asyncio.run(initialize_faiss_index())
"""

# Run initialization:
# python src/scripts/init_faiss_index.py


# ============================================================================
# Step 5: Test FAISS Integration
# ============================================================================

# curl test for conformity endpoint:
"""
curl -X POST http://localhost:8000/api/v1/vector/conformity \\
  -H "Content-Type: application/json" \\
  -d '{
    "transcript": "We detected unauthorized database access that lasted 2 hours without alerting management."
  }'
"""

# curl test for ISO search:
"""
curl -X POST http://localhost:8000/api/v1/vector/iso-search \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "How should we respond to a security breach?",
    "iso_standard": "ISO-22324"
  }'
"""

# curl test for index status:
"""
curl http://localhost:8000/api/v1/vector/index-status
"""


# ============================================================================
# Step 6: Production Considerations
# ============================================================================

"""
PERFORMANCE OPTIMIZATION:
- Use faiss-gpu for large indexes (>1M documents)
- Implement Redis caching for frequent queries
- Use pgvector in PostgreSQL for persistent storage
- Batch index updates for efficiency

SCALING:
- For >10M documents, use Qdrant or Elasticsearch
- Implement index sharding across multiple instances
- Use load balancing for API requests
- Consider distributed FAISS with Kubernetes

MONITORING:
- Log all conformity calculations
- Track index growth and performance metrics
- Monitor API response times
- Alert on conformity anomalies
"""
