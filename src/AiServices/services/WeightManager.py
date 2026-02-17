"""
Weight Manager for RLHF
Gerencia pesos dinâmicos do modelo C2M que podem ser ajustados por feedback
"""

import json
import os
import logging
from typing import Dict, Optional
from datetime import datetime
from dataclasses import asdict, dataclass

log = logging.getLogger(__name__)


@dataclass
class C2MWeights:
    """Representa todos os pesos ajustáveis do modelo C2M"""
    
    # Decision Tree sentiment factor (default 0.25)
    decision_tree_sentiment: float = 0.25
    
    # Decision Tree type classification weight (default 0.20)
    decision_tree_type: float = 0.20
    
    # Decision Tree governance factor (default 0.15)
    decision_tree_governance: float = 0.15
    
    # Decision Tree maturity factor (default 0.15)
    decision_tree_maturity: float = 0.15
    
    # Risk agent severity multiplier (default 1.0)
    risk_severity_multiplier: float = 1.0
    
    # Monte Carlo sentiment modifier (default 0.2)
    monte_carlo_sentiment_modifier: float = 0.2
    
    # Monte Carlo maturity modifier (default 0.15)
    monte_carlo_maturity_modifier: float = 0.15
    
    # Monte Carlo governance modifier (default 0.1)
    monte_carlo_governance_modifier: float = 0.1
    
    # Crisis threshold (default 0.4)
    crisis_threshold: float = 0.4
    
    # Crisis probability threshold (default 0.5 = 50%)
    crisis_probability_threshold: float = 0.5
    
    # Monte Carlo simulation count (default 50000)
    monte_carlo_simulations: int = 50000
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'C2MWeights':
        """Create from dictionary"""
        return cls(**data)


class WeightManager:
    """
    Gerencia pesos dinâmicos para RLHF
    Persiste ajustes em JSON para serem carregados ao iniciar
    """
    
    def __init__(self, weights_file: str = None):
        """
        Inicializa WeightManager
        
        Args:
            weights_file: Caminho para arquivo de pesos (default: data/c2m_weights.json)
        """
        if weights_file is None:
            weights_file = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", 
                "data", "c2m_weights.json"
            )
        
        self.weights_file = weights_file
        self.weights = self._load_weights()
        
        log.info(f"WeightManager initialized with weights from {weights_file}")
    
    def _ensure_weights_dir(self):
        """Garante que o diretório existe"""
        os.makedirs(os.path.dirname(self.weights_file), exist_ok=True)
    
    def _load_weights(self) -> C2MWeights:
        """
        Carrega pesos do arquivo JSON ou retorna defaults
        
        Returns:
            C2MWeights com valores persistidos ou defaults
        """
        if os.path.exists(self.weights_file):
            try:
                with open(self.weights_file, 'r') as f:
                    data = json.load(f)
                    log.info(f"Weights loaded from {self.weights_file}")
                    return C2MWeights.from_dict(data)
            except Exception as e:
                log.error(f"Error loading weights: {e}, using defaults")
                return C2MWeights()
        else:
            log.info(f"No weights file found at {self.weights_file}, using defaults")
            return C2MWeights()
    
    def save_weights(self) -> bool:
        """
        Persiste pesos atuais em arquivo JSON
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            self._ensure_weights_dir()
            
            # Adiciona timestamp ao arquivo
            backup_file = self.weights_file.replace('.json', '_backup.json')
            if os.path.exists(self.weights_file):
                os.rename(self.weights_file, backup_file)
            
            with open(self.weights_file, 'w') as f:
                json.dump(self.weights.to_dict(), f, indent=2)
            
            log.info(f"Weights saved to {self.weights_file}")
            return True
        except Exception as e:
            log.error(f"Error saving weights: {e}")
            return False
    
    def update_weight(self, component: str, new_value: float) -> bool:
        """
        Atualiza um peso específico
        
        Args:
            component: Nome do componente (ex: crisis_threshold)
            new_value: Novo valor
            
        Returns:
            True se sucesso
        """
        if not hasattr(self.weights, component):
            log.error(f"Unknown component: {component}")
            return False
        
        # Validações de limite
        if component == "monte_carlo_simulations":
            new_value = int(max(1000, min(new_value, 1000000)))
        else:
            new_value = float(max(0.0, min(new_value, 2.0)))  # Limita 0-2
        
        old_value = getattr(self.weights, component)
        setattr(self.weights, component, new_value)
        
        log.info(f"Weight updated: {component} = {old_value} → {new_value}")
        return self.save_weights()
    
    def adjust_weight(self, component: str, adjustment: float) -> bool:
        """
        Ajusta um peso relativamente (não absolutamente)
        
        Args:
            component: Nome do componente
            adjustment: Valor a adicionar/subtrair
            
        Returns:
            True se sucesso
        """
        if not hasattr(self.weights, component):
            log.error(f"Unknown component: {component}")
            return False
        
        old_value = getattr(self.weights, component)
        new_value = old_value + adjustment
        
        return self.update_weight(component, new_value)
    
    def get_weight(self, component: str) -> Optional[float]:
        """
        Obtém valor de um peso
        
        Args:
            component: Nome do componente
            
        Returns:
            Valor do peso ou None se não existe
        """
        return getattr(self.weights, component, None)
    
    def get_all_weights(self) -> Dict:
        """Retorna todos os pesos"""
        return self.weights.to_dict()
    
    def reset_to_defaults(self) -> bool:
        """
        Reset para valores padrão
        
        Returns:
            True se sucesso
        """
        self.weights = C2MWeights()
        log.info("Weights reset to defaults")
        return self.save_weights()
    
    def get_weight_history(self, limit: int = 10) -> list:
        """
        Retorna histórico de alterações (requer database)
        Por enquanto retorna vazio - implementado no histórico de ajustes
        
        Returns:
            Lista de alterações recentes
        """
        # Implementado via RLHFFeedbackService.get_adjustment_history()
        return []


# Instância global do WeightManager
_weight_manager: Optional[WeightManager] = None


def get_weight_manager() -> WeightManager:
    """Obtém instância singleton do WeightManager"""
    global _weight_manager
    if _weight_manager is None:
        _weight_manager = WeightManager()
    return _weight_manager


def initialize_weight_manager(weights_file: str = None) -> WeightManager:
    """
    Inicializa o WeightManager com arquivo específico
    
    Args:
        weights_file: Caminho para arquivo de pesos
        
    Returns:
        Instância do WeightManager
    """
    global _weight_manager
    _weight_manager = WeightManager(weights_file)
    return _weight_manager
