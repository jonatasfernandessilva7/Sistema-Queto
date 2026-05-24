"""
Testes para os Serviços de C2M v2.0

Cobre:
- VectorSearchService
- ISOClassifierService
- AudioProcessorService (testes básicos)
- API REST v1
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# ════════════════════════════════════════════════════════════════════════
# TESTES - VECTOR SEARCH SERVICE
# ════════════════════════════════════════════════════════════════════════

class TestVectorSearchService:
    """Testes para VectorSearchService"""
    
    @pytest.mark.asyncio
    async def test_vector_engine_initialization(self):
        """Testa inicialização do motor de busca"""
        from src.backend.services.VectorSearchService import VectorSearchEngine
        
        engine = VectorSearchEngine()
        assert engine.model is not None
        assert engine.model_name == "distiluse-base-multilingual-case-sensitive-v2"
    
    def test_cosine_similarity_calculation(self):
        """Testa cálculo de similaridade de cosseno"""
        from src.backend.services.VectorSearchService import VectorSearchEngine
        
        engine = VectorSearchEngine()
        
        # Vetores idênticos = 1.0
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        similarity = engine.cosine_similarity(v1, v2)
        assert abs(similarity - 1.0) < 0.001
        
        # Vetores ortogonais = 0.0
        v3 = np.array([1.0, 0.0, 0.0])
        v4 = np.array([0.0, 1.0, 0.0])
        similarity = engine.cosine_similarity(v3, v4)
        assert abs(similarity - 0.0) < 0.001
    
    def test_encode_text(self):
        """Testa encoding de texto"""
        from src.backend.services.VectorSearchService import VectorSearchEngine
        
        engine = VectorSearchEngine()
        text = "Sistema indisponível por ataque"
        
        embedding = engine.encode_text(text)
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == engine.model.get_sentence_embedding_dimension()
    
    def test_conformity_factor_calculation(self):
        """Testa cálculo do fator de conformidade"""
        from src.backend.services.VectorSearchService import VectorSearchEngine
        
        engine = VectorSearchEngine()
        
        transcript = "Sistema em conformidade com políticas"
        conformity = engine.calculate_conformity_factor(
            transcript,
            corporate_documents=["Política padrão", "Documento de governança"],
            top_k=2
        )
        
        assert 0.0 <= conformity <= 1.0
    
    def test_cache_operations(self):
        """Testa operações de cache"""
        from src.backend.services.VectorSearchService import VectorSearchEngine
        
        engine = VectorSearchEngine()
        
        # Inserir no cache
        embedding = np.random.randn(512)
        engine._embedding_cache[1] = embedding
        
        # Verificar
        assert 1 in engine._embedding_cache
        assert np.array_equal(engine._embedding_cache[1], embedding)
        
        # Limpar
        engine.clear_cache()
        assert len(engine._embedding_cache) == 0


# ════════════════════════════════════════════════════════════════════════
# TESTES - ISO CLASSIFIER SERVICE
# ════════════════════════════════════════════════════════════════════════

class TestISOClassifierService:
    """Testes para ISOClassifierService"""
    
    def test_classify_green(self):
        """Testa classificação verde (P < 0.20)"""
        from src.backend.services.ISOClassifierService import ISOClassifier, CrisisLevel
        
        classification = ISOClassifier.classify(probability=0.15, confidence_score=0.9)
        
        assert classification.level == CrisisLevel.GREEN
        assert classification.color == "#00AA00"
        assert classification.probability == 0.15
    
    def test_classify_yellow(self):
        """Testa classificação amarela (0.20 ≤ P < 0.40)"""
        from src.backend.services.ISOClassifierService import ISOClassifier, CrisisLevel
        
        classification = ISOClassifier.classify(probability=0.30)
        
        assert classification.level == CrisisLevel.YELLOW
        assert classification.color == "#FFFF00"
    
    def test_classify_orange(self):
        """Testa classificação laranja (0.40 ≤ P < 0.70)"""
        from src.backend.services.ISOClassifierService import ISOClassifier, CrisisLevel
        
        classification = ISOClassifier.classify(probability=0.55)
        
        assert classification.level == CrisisLevel.ORANGE
        assert classification.color == "#FF8800"
    
    def test_classify_red(self):
        """Testa classificação vermelha (P ≥ 0.70)"""
        from src.backend.services.ISOClassifierService import ISOClassifier, CrisisLevel
        
        classification = ISOClassifier.classify(probability=0.85)
        
        assert classification.level == CrisisLevel.RED
        assert classification.color == "#FF0000"
    
    def test_probability_normalization(self):
        """Testa normalização de probabilidade > 1.0"""
        from src.backend.services.ISOClassifierService import ISOClassifier
        
        # Se P > 1.0, dividir por 100
        classification = ISOClassifier.classify(probability=75.0)  # 75%
        
        assert classification.probability == 0.75
    
    def test_detailed_classification(self):
        """Testa classificação detalhada"""
        from src.backend.services.ISOClassifierService import ISOClassifier
        
        report = ISOClassifier.classify_detailed(
            probability=0.45,
            confidence_score=0.9,
            sentiment_polarity=-0.3,
            maturity_level=3.5,
            conformity_factor=0.2,
            contributing_factors=["Sentimento negativo"]
        )
        
        assert report.classification.probability == 0.45
        assert len(report.recommended_actions) > 0
        assert report.risk_score > 0
        assert len(report.next_steps) > 0
    
    def test_actions_by_level(self):
        """Testa que cada nível tem ações associadas"""
        from src.backend.services.ISOClassifierService import ISOClassifier
        
        thresholds = ISOClassifier.get_thresholds()
        assert "RED" in thresholds
        assert "ORANGE" in thresholds
        assert "YELLOW" in thresholds
        assert "GREEN" in thresholds


# ════════════════════════════════════════════════════════════════════════
# TESTES - AUDIO PROCESSOR SERVICE
# ════════════════════════════════════════════════════════════════════════

class TestAudioProcessorService:
    """Testes para AudioProcessorService"""
    
    @pytest.mark.asyncio
    async def test_audio_processor_initialization(self):
        """Testa inicialização do processador"""
        from src.backend.services.AudioProcessorService import AudioProcessor
        
        processor = AudioProcessor()
        assert processor.groq_client is not None
        assert len(processor._crisis_keywords) > 0
    
    @pytest.mark.asyncio
    async def test_keyword_loading(self):
        """Testa carregamento de palavras-chave"""
        from src.backend.services.AudioProcessorService import AudioProcessor
        
        processor = AudioProcessor()
        keywords = processor._crisis_keywords
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "ataque" in keywords or "attack" in keywords
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis(self):
        """Testa análise de sentimento"""
        from src.backend.services.AudioProcessorService import AudioProcessor
        
        processor = AudioProcessor()
        
        # Texto positivo
        sentiment_pos = await processor.analyze_sentiment("Tudo está funcionando perfeitamente!")
        assert sentiment_pos.polarity > 0
        assert sentiment_pos.interpretation == "Positivo"
        
        # Texto negativo
        sentiment_neg = await processor.analyze_sentiment("Sistema falhou completamente!")
        assert sentiment_neg.polarity < 0
        assert sentiment_neg.interpretation == "Negativo"
    
    @pytest.mark.asyncio
    async def test_keyword_detection(self):
        """Testa detecção de palavras-chave"""
        from src.backend.services.AudioProcessorService import AudioProcessor
        
        processor = AudioProcessor()
        text = "Sistema sofreu ataque ransomware. Falha total do sistema."
        
        keywords = await processor.detect_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0  # Deve encontrar "ataque" ou "falha"
    
    @pytest.mark.asyncio
    async def test_file_validation(self):
        """Testa validação de arquivo"""
        from src.backend.services.AudioProcessorService import AudioProcessor
        
        processor = AudioProcessor()
        
        # Arquivo não existente
        is_valid, error = await processor.validate_audio_file("nao_existe.wav")
        assert not is_valid
        assert "não encontrado" in error.lower()


# ════════════════════════════════════════════════════════════════════════
# TESTES - API REST v1
# ════════════════════════════════════════════════════════════════════════

class TestAPIv1:
    """Testes para API REST v1"""
    
    @pytest.fixture
    def client(self):
        """Fixture para cliente HTTP de teste"""
        from fastapi.testclient import TestClient
        from src.backend.server import app
        
        return TestClient(app)
    
    def test_health_check(self, client):
        """Testa endpoint de health check"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
    
    def test_crisis_probability_request_validation(self, client):
        """Testa validação de request"""
        # Request válido
        payload = {
            "sentiment_polarity": -0.3,
            "maturity_level": 3.5,
            "has_risk_plan": True,
            "risk_severity_scores": [0.4, 0.6]
        }
        response = client.post("/api/v1/crisis/probability", json=payload)
        assert response.status_code == 200
        
        # Polarity fora do range
        payload_invalid = {
            "sentiment_polarity": -1.5,  # < -0.5
            "maturity_level": 3.5
        }
        response = client.post("/api/v1/crisis/probability", json=payload_invalid)
        assert response.status_code == 422  # Validation error


# ════════════════════════════════════════════════════════════════════════
# TESTES - C2M INTEGRATION
# ════════════════════════════════════════════════════════════════════════

class TestC2MIntegration:
    """Testes de integração do pipeline C2M"""
    
    def test_monte_carlo_with_conformity(self):
        """Testa simulação Monte Carlo com conformidade"""
        from src.agents.orchestrator.C2M_Analysis import MonteCarloProbabilityCalculator
        from src.agents.orchestrator.C2M_Models import RiskAgentC2M, OrganizationalContextC2M
        
        # Setup
        context = OrganizationalContextC2M(
            maturity_level=3.5,
            has_risk_plan=True,
            has_crisis_plan=False,
            has_continuity_plan=True,
            has_recovery_plan=False,
            historical_similar_events=2,
            formal_governance=True
        )
        
        risk_agents = [
            RiskAgentC2M(
                name="Risco_Tecnológico",
                category="technological",
                severity=0.6,
                impact_chain=["Sistema", "Operações"],
                mitigation="Aplicar patches"
            ),
            RiskAgentC2M(
                name="Risco_Humano",
                category="human",
                severity=0.4,
                impact_chain=["Pessoal"],
                mitigation="Treinar"
            )
        ]
        
        # Executar
        probability, scenarios = MonteCarloProbabilityCalculator.run_simulation(
            risk_agents=risk_agents,
            context=context,
            sentiment_polarity=-0.3,
            num_simulations=1000  # Pequeno para teste rápido
        )
        
        # Validar
        assert 0 <= probability <= 100
        assert isinstance(scenarios, list)
    
    def test_decision_tree_evaluation(self):
        """Testa avaliação da árvore de decisão"""
        from src.agents.orchestrator.C2M_Analysis import DecisionTreeAnalyzer
        from src.agents.orchestrator.C2M_Models import (
            SentimentAnalysisC2M, OrganizationalContextC2M
        )
        
        sentiment = SentimentAnalysisC2M(
            polarity=-0.4,
            subjectivity=0.6,
            raw_text="Sistema comprometido por ataque",
            interpretation="Negativo"
        )
        
        context = OrganizationalContextC2M(
            maturity_level=2.5,
            has_risk_plan=False,
            has_crisis_plan=False,
            has_continuity_plan=False,
            has_recovery_plan=False,
            historical_similar_events=3,
            formal_governance=False
        )
        
        is_crisis, score, reasoning = DecisionTreeAnalyzer.evaluate(
            sentiment=sentiment,
            event_type="Ataque cibernético",
            context=context
        )
        
        assert isinstance(is_crisis, bool)
        assert 0 <= score <= 1
        assert isinstance(reasoning, str)


# ════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO PYTEST
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
