"""
Unit tests for FAISS Vector Store implementation
Tests conformidade C calculation and ISO similarity matching
"""

import pytest
import asyncio
from src.backend.services.FAISSVectorStore import FAISSVectorStore


@pytest.fixture
def faiss_store():
    """Create FAISS store instance for testing"""
    return FAISSVectorStore()


@pytest.fixture
def sample_documents():
    """Sample corporate policy documents"""
    return [
        {
            "content": "Crisis response protocol requires immediate notification of executive team within 15 minutes of incident detection.",
            "title": "Crisis Response Protocol",
            "doc_id": "policy_001",
            "type": "corporate_policy",
            "conformance_weight": 0.9
        },
        {
            "content": "Information security policy mandates encryption of all sensitive data and regular security audits.",
            "title": "Information Security Policy",
            "doc_id": "policy_002",
            "type": "corporate_policy",
            "conformance_weight": 0.85
        },
        {
            "content": "Continuity and recovery planning ensures business operations resume within acceptable timeframes.",
            "title": "Business Continuity Plan",
            "doc_id": "policy_003",
            "type": "corporate_policy",
            "conformance_weight": 0.8
        }
    ]


@pytest.mark.asyncio
async def test_index_documents(faiss_store, sample_documents):
    """Test indexing documents into FAISS"""
    count = await faiss_store.index_document(
        content=sample_documents[0]["content"],
        title=sample_documents[0]["title"],
        doc_id=sample_documents[0]["doc_id"],
        doc_type=sample_documents[0]["type"],
        conformance_weight=sample_documents[0]["conformance_weight"]
    )
    
    assert count >= 0
    assert faiss_store.index.ntotal == 1


@pytest.mark.asyncio
async def test_search_similar_documents(faiss_store, sample_documents):
    """Test semantic search functionality"""
    # Index documents first
    for doc in sample_documents:
        await faiss_store.index_document(**doc)
    
    # Search for similar documents
    query = "What should we do when there is a security incident?"
    results = await faiss_store.search_similar_documents(query, top_k=3)
    
    assert len(results) <= 3
    assert all(hasattr(r, 'similarity_score') for r in results)
    assert all(0 <= r.similarity_score <= 1 for r in results)


@pytest.mark.asyncio
async def test_conformity_factor_calculation(faiss_store):
    """Test conformidade C calculation"""
    # Index sample corporate documents
    corporate_docs = [
        "We have crisis management procedures in place",
        "All employees receive security training quarterly",
        "Incident response is activated within 30 minutes"
    ]
    
    transcript = "We detected unauthorized database access that lasted 2 hours before discovery."
    
    conformity_factor, details = await faiss_store.calculate_conformity_factor(
        transcript=transcript,
        corporate_documents=corporate_docs
    )
    
    assert 0 <= conformity_factor <= 1
    assert "corporate_policy_alignment" in details
    assert "iso_alignment" in details
    assert "risk_language_score" in details
    assert "final_conformity_factor" in details


@pytest.mark.asyncio
async def test_conformity_factor_with_iso_weights(faiss_store):
    """Test conformidade C with custom ISO weights"""
    transcript = "Crisis management incident occurred"
    
    iso_weights = {
        "ISO-22324": 1.0,
        "ISO-27001": 0.9,
        "ISO-31000": 0.8
    }
    
    conformity_factor, details = await faiss_store.calculate_conformity_factor(
        transcript=transcript,
        iso_weights=iso_weights
    )
    
    assert 0 <= conformity_factor <= 1
    assert len(details["matched_standards"]) >= 0


@pytest.mark.asyncio
async def test_iso_search(faiss_store, sample_documents):
    """Test ISO-specific search functionality"""
    # Index documents
    for doc in sample_documents:
        await faiss_store.index_document(**doc)
    
    query = "crisis and incident management"
    
    # Search with ISO-22324 filter
    results = await faiss_store.search_iso_similar_documents(
        query=query,
        iso_standard="ISO-22324",
        top_k=3
    )
    
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_conformity_report(faiss_store, sample_documents):
    """Test comprehensive conformity report generation"""
    # Index documents
    for doc in sample_documents:
        await faiss_store.index_document(**doc)
    
    transcript = "Our data was breached and we need to respond to the crisis"
    
    report = await faiss_store.get_conformity_report(transcript, top_k=5)
    
    assert "conformity_factor" in report
    assert "conformity_details" in report
    assert "similar_documents" in report
    assert "iso_alignment" in report
    assert "timestamp" in report


@pytest.mark.asyncio
async def test_high_conformity_score(faiss_store):
    """Test high conformity score (conforming to policies)"""
    corporate_docs = [
        "Incident response activated immediately upon detection",
        "Executive team notified within 15 minutes",
        "All security protocols followed correctly"
    ]
    
    transcript = "We detected an incident and immediately activated our incident response team as per protocol."
    
    conformity_factor, _ = await faiss_store.calculate_conformity_factor(
        transcript=transcript,
        corporate_documents=corporate_docs
    )
    
    # High alignment means low conformity factor (good conformance)
    assert conformity_factor < 0.5


@pytest.mark.asyncio
async def test_low_conformity_score(faiss_store):
    """Test low conformity score (not conforming)"""
    corporate_docs = [
        "Always follow incident response procedures",
        "Encryption is mandatory for all data",
        "Executive notification required immediately"
    ]
    
    transcript = "We ignored the incident for 3 days, didn't encrypt the data, and didn't tell anyone."
    
    conformity_factor, _ = await faiss_store.calculate_conformity_factor(
        transcript=transcript,
        corporate_documents=corporate_docs
    )
    
    # Low alignment means high conformity factor (poor conformance)
    assert conformity_factor > 0.5


@pytest.mark.asyncio
async def test_iso_keyword_matching():
    """Test ISO standard keyword matching"""
    store = FAISSVectorStore()
    
    # Test that ISO standards are loaded
    assert "ISO-22324" in store.iso_standards
    assert "ISO-22361" in store.iso_standards
    assert "ISO-31000" in store.iso_standards
    assert "ISO-27001" in store.iso_standards
    
    # Test keywords exist
    iso_data = store.iso_standards["ISO-22324"]
    assert "keywords" in iso_data
    assert len(iso_data["keywords"]) > 0
    assert "crisis management" in iso_data["keywords"]


@pytest.mark.asyncio
async def test_empty_index_search(faiss_store):
    """Test search on empty index"""
    query = "test query"
    results = await faiss_store.search_similar_documents(query)
    
    assert len(results) == 0


@pytest.mark.asyncio
async def test_embedding_dimension(faiss_store):
    """Test that embeddings are 512-dimensional"""
    assert faiss_store.embedding_dim == 512
    assert faiss_store.index.d == 512


def test_iso_standards_weights(faiss_store):
    """Test ISO standards have proper conformance weights"""
    for iso_id, iso_data in faiss_store.iso_standards.items():
        assert "conformance_weight" in iso_data
        assert 0 <= iso_data["conformance_weight"] <= 1.0
        assert iso_data["conformance_weight"] > 0


@pytest.mark.asyncio
async def test_conformity_factors_weights():
    """Test that conformity calculation uses correct weights"""
    store = FAISSVectorStore()
    
    transcript = "Security incident test"
    conformity, details = await store.calculate_conformity_factor(transcript)
    
    # Check that all components are present
    assert "corporate_policy_alignment" in details
    assert "iso_alignment" in details
    assert "risk_language_score" in details
    assert "final_conformity_factor" in details
    
    # Verify components sum correctly with weights
    corporate_weight = 0.4
    iso_weight = 0.4
    risk_weight = 0.2
    
    expected = (
        corporate_weight * details["corporate_policy_alignment"] +
        iso_weight * details["iso_alignment"] +
        risk_weight * (1.0 - details["risk_language_score"])
    )
    
    assert abs(expected - conformity) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
