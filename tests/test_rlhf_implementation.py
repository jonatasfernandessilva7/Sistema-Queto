"""
Test suite for RLHF Implementation
Valida WeightManager, RLHFFeedbackService e RLHFController
"""

import pytest
import json
import os
import tempfile
from datetime import datetime

from src.AiServices.services.WeightManager import (
    C2MWeights,
    WeightManager,
    get_weight_manager
)
from src.AiServices.services.RLHFFeedbackService import RLHFFeedbackService
from src.backend.models.ReportFeedback import (
    ReportFeedbackCreate,
    FeedbackAnalysis,
    WeightAdjustment
)


class TestWeightManager:
    """Testes para o WeightManager"""
    
    def test_weights_default_values(self):
        """Verifica valores padrão dos pesos"""
        weights = C2MWeights()
        
        assert weights.crisis_threshold == 0.4
        assert weights.crisis_probability_threshold == 0.5
        assert weights.monte_carlo_simulations == 50000
        assert weights.decision_tree_sentiment == 0.25
        assert weights.monte_carlo_sentiment_modifier == 0.2
    
    def test_weights_to_dict(self):
        """Converte pesos para dicionário"""
        weights = C2MWeights()
        d = weights.to_dict()
        
        assert isinstance(d, dict)
        assert d["crisis_threshold"] == 0.4
        assert "Monte_carlo_sentiment_modifier" not in d
    
    def test_weights_from_dict(self):
        """Cria pesos de dicionário"""
        data = {
            "crisis_threshold": 0.5,
            "decision_tree_sentiment": 0.3,
            "monte_carlo_simulations": 75000
        }
        
        weights = C2MWeights.from_dict(data)
        
        assert weights.crisis_threshold == 0.5
        assert weights.decision_tree_sentiment == 0.3
        assert weights.monte_carlo_simulations == 75000
    
    def test_weight_manager_create(self):
        """Cria WeightManager com arquivo temporário"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            weights_file = f.name
        
        try:
            wm = WeightManager(weights_file)
            assert wm.weights is not None
            assert wm.weights.crisis_threshold == 0.4
        finally:
            if os.path.exists(weights_file):
                os.unlink(weights_file)
    
    def test_weight_manager_save_and_load(self):
        """Salva e carrega pesos do arquivo"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            weights_file = f.name
        
        try:
            # Cria e salva
            wm1 = WeightManager(weights_file)
            wm1.update_weight("crisis_threshold", 0.5)
            
            # Carrega
            wm2 = WeightManager(weights_file)
            assert wm2.weights.crisis_threshold == 0.5
        finally:
            if os.path.exists(weights_file):
                os.unlink(weights_file)
    
    def test_weight_manager_adjust_weight(self):
        """Ajusta peso relativamente"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            weights_file = f.name
        
        try:
            wm = WeightManager(weights_file)
            
            initial = wm.get_weight("decision_tree_sentiment")
            assert initial == 0.25
            
            wm.adjust_weight("decision_tree_sentiment", 0.05)
            
            after = wm.get_weight("decision_tree_sentiment")
            assert after == 0.30
        finally:
            if os.path.exists(weights_file):
                os.unlink(weights_file)
    
    def test_weight_manager_reset_defaults(self):
        """Reseta para valores padrão"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            weights_file = f.name
        
        try:
            wm = WeightManager(weights_file)
            wm.update_weight("crisis_threshold", 0.7)
            
            assert wm.get_weight("crisis_threshold") == 0.7
            
            wm.reset_to_defaults()
            assert wm.get_weight("crisis_threshold") == 0.4
        finally:
            if os.path.exists(weights_file):
                os.unlink(weights_file)


class TestRLHFFeedbackService:
    """Testes para RLHFFeedbackService"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "test_feedback.db")
        self.weights_file = os.path.join(self.temp_dir, "test_weights.json")
        self.service = RLHFFeedbackService(self.db_file, self.weights_file)
    
    def test_receive_feedback(self):
        """Recebe e armazena feedback"""
        feedback_data = ReportFeedbackCreate(
            report_id="rpt-001",
            actual_crisis=True,
            c2m_probability_comment="too_high",
            priority_correct=True,
            user_id="user-1"
        )
        
        feedback = self.service.receive_feedback(feedback_data)
        
        assert feedback.id is not None
        assert feedback.report_id == "rpt-001"
        assert feedback.actual_crisis == True
        assert feedback.created_at is not None
    
    def test_get_feedback(self):
        """Obtém feedback específico"""
        feedback_data = ReportFeedbackCreate(
            report_id="rpt-002",
            actual_crisis=False,
            user_id="user-2"
        )
        
        feedback = self.service.receive_feedback(feedback_data)
        retrieved = self.service.get_feedback(feedback.id)
        
        assert retrieved is not None
        assert retrieved.id == feedback.id
        assert retrieved.report_id == "rpt-002"
    
    def test_feedback_stats_no_feedback(self):
        """Retorna None quando não há feedback"""
        stats = self.service.get_feedback_stats("no-report")
        assert stats is None
    
    def test_feedback_stats_with_data(self):
        """Calcula estatísticas de feedback"""
        # Adiciona alguns feedbacks
        for i in range(5):
            feedback_data = ReportFeedbackCreate(
                report_id="rpt-003",
                actual_crisis=True,
                c2m_probability_comment="accurate" if i % 2 == 0 else "too_low",
                priority_correct=True
            )
            self.service.receive_feedback(feedback_data)
        
        stats = self.service.get_feedback_stats("rpt-003")
        
        assert stats is not None
        assert stats.total_feedbacks == 5
        assert stats.priority_accuracy == 1.0  # Todos corretos
    
    def test_analyze_feedback_patterns(self):
        """Analisa padrões de feedback"""
        # Cria 15 feedbacks com padrão
        for i in range(15):
            # 10 corretos, 5 falsos positivos
            is_correct = i < 10
            comment = "accurate" if is_correct else "too_high"
            
            feedback_data = ReportFeedbackCreate(
                report_id=f"rpt-{i}",
                actual_crisis=i % 2 == 0,
                c2m_probability_comment=comment,
                user_id=f"user-{i}"
            )
            self.service.receive_feedback(feedback_data)
        
        analysis = self.service.analyze_feedback_patterns(min_feedbacks=10)
        
        assert analysis is not None
        assert analysis.true_positives + analysis.true_negatives > 0
    
    def test_calculate_weight_adjustments(self):
        """Calcula ajustes de peso"""
        # Feedback com muitos falsos positivos (70%)
        analysis = FeedbackAnalysis(
            false_positives=7,
            true_negatives=3,
            true_positives=1,
            false_negatives=0
        )
        
        adjustments = self.service.calculate_weight_adjustments(analysis)
        
        # Deve sugerir aumentar crisis_threshold (para reduzir FP)
        assert len(adjustments) > 0
        
        crisis_adj = [a for a in adjustments if a.component == "crisis_threshold"]
        if crisis_adj:
            assert crisis_adj[0].new_value > crisis_adj[0].current_value
    
    def test_apply_weight_adjustment(self):
        """Aplica ajuste de peso"""
        adjustment = WeightAdjustment(
            component="crisis_threshold",
            current_value=0.4,
            adjustment_amount=0.05,
            new_value=0.45,
            reason="Test adjustment",
            confidence=0.8,
            timestamp=datetime.now()
        )
        
        success = self.service.apply_weight_adjustment(adjustment)
        
        assert success == True
        # Verifica que peso foi atualizado
        assert self.service.weight_manager.get_weight("crisis_threshold") == 0.45
    
    def test_process_and_apply_adjustments(self):
        """Processa e aplica ajustes completos"""
        # Cria 12 feedbacks
        for i in range(12):
            feedback_data = ReportFeedbackCreate(
                report_id=f"rpt-{i}",
                actual_crisis=i % 3 == 0,
                c2m_probability_comment="accurate",
                user_id=f"user-{i}"
            )
            self.service.receive_feedback(feedback_data)
        
        result = self.service.process_and_apply_adjustments(min_feedbacks=10)
        
        assert result["status"] in ["completed", "no_adjustments_needed"]
        assert result["feedbacks_analyzed"] >= 10


class TestFeedbackAnalysis:
    """Testes para análise de feedback"""
    
    def test_feedback_analysis_accuracy(self):
        """Calcula accuracy corretamente"""
        analysis = FeedbackAnalysis(
            true_positives=8,
            true_negatives=6,
            false_positives=3,
            false_negatives=3
        )
        
        # (8 + 6) / 20 = 0.7
        assert analysis.accuracy == 0.7
    
    def test_feedback_analysis_precision(self):
        """Calcula precision corretamente"""
        analysis = FeedbackAnalysis(
            true_positives=8,
            true_negatives=6,
            false_positives=2,
            false_negatives=4
        )
        
        # 8 / (8 + 2) = 0.8
        assert analysis.precision == 0.8
    
    def test_feedback_analysis_recall(self):
        """Calcula recall corretamente"""
        analysis = FeedbackAnalysis(
            true_positives=8,
            true_negatives=6,
            false_positives=2,
            false_negatives=2
        )
        
        # 8 / (8 + 2) = 0.8
        assert analysis.recall == 0.8
    
    def test_feedback_analysis_f1_score(self):
        """Calcula F1 score corretamente"""
        analysis = FeedbackAnalysis(
            true_positives=8,
            true_negatives=6,
            false_positives=2,
            false_negatives=2
        )
        
        # precision = 0.8, recall = 0.8
        # f1 = 2 * (0.8 * 0.8) / (0.8 + 0.8) = 0.8
        assert abs(analysis.f1_score - 0.8) < 0.0001


# ════════════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
