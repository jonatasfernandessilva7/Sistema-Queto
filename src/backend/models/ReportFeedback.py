"""
Report Feedback Model for RLHF (Reinforcement Learning from Human Feedback)
Tracks human feedback on C2M analysis results for continuous improvement
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class ReportFeedbackCreate(BaseModel):
    """
    Input model for creating feedback on a C2M report
    
    Attributes:
        report_id: ID of the C2M report being evaluated
        actual_crisis: Was it actually a crisis? (true/false diagnosis correction)
        c2m_probability_comment: Feedback on probability accuracy
        priority_correct: Was the priority classification correct?
        risk_agents_relevant: Were identified risk agents relevant?
        sentiment_accurate: Was sentiment analysis accurate?
        feedback_text: Free-form feedback from user
        user_id: ID of the feedback provider
        suggestions: Improvement suggestions
    """
    report_id: str
    actual_crisis: bool
    c2m_probability_comment: Optional[Literal["too_high", "too_low", "accurate"]] = None
    priority_correct: Optional[bool] = None
    risk_agents_relevant: Optional[bool] = None
    sentiment_accurate: Optional[bool] = None
    feedback_text: Optional[str] = None
    user_id: Optional[str] = None
    suggestions: Optional[str] = None


class ReportFeedback(BaseModel):
    """
    Complete Report Feedback model with all fields
    """
    id: str
    report_id: str
    actual_crisis: bool
    c2m_probability_comment: Optional[str] = None
    priority_correct: Optional[bool] = None
    risk_agents_relevant: Optional[bool] = None
    sentiment_accurate: Optional[bool] = None
    feedback_text: Optional[str] = None
    user_id: Optional[str] = None
    suggestions: Optional[str] = None
    created_at: datetime
    processed: bool = False
    impact_score: float = Field(default=0.0, ge=0.0, le=1.0)

    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """
    Statistics about feedback for a report
    """
    total_feedbacks: int
    accuracy_rate: float  # % of feedback saying it was accurate
    probability_accuracy: Optional[str] = None  # "too_high" | "too_low" | "accurate"
    priority_accuracy: float  # % correct priority assessments
    risk_agents_accuracy: float  # % relevant risk agents
    sentiment_accuracy: float  # % accurate sentiment


class WeightAdjustment(BaseModel):
    """
    Represents a weight adjustment based on feedback
    
    Used by RLHF system to adjust:
    - Decision tree factors
    - Risk agent severities
    - Monte Carlo modifiers
    - Threshold values
    """
    component: Literal[
        "decision_tree_sentiment",
        "decision_tree_type",
        "decision_tree_governance",
        "decision_tree_maturity",
        "risk_severity",
        "monte_carlo_sentiment_modifier",
        "monte_carlo_maturity_modifier",
        "monte_carlo_governance_modifier",
        "crisis_threshold"
    ]
    current_value: float
    adjustment_amount: float
    new_value: float
    reason: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    timestamp: datetime


class FeedbackAnalysis(BaseModel):
    """
    Analysis of feedback patterns for weight adjustment
    """
    false_positives: int  # Predicted crisis, wasn't
    false_negatives: int  # Didn't predict crisis, was
    true_positives: int  # Predicted crisis, was
    true_negatives: int  # Predicted no crisis, wasn't
    
    @property
    def accuracy(self) -> float:
        """Calculate overall accuracy"""
        total = self.false_positives + self.false_negatives + self.true_positives + self.true_negatives
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total
    
    @property
    def precision(self) -> float:
        """Calculate precision (TP / TP + FP)"""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def recall(self) -> float:
        """Calculate recall (TP / TP + FN)"""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator
    
    @property
    def f1_score(self) -> float:
        """Calculate F1 score"""
        p = self.precision
        r = self.recall
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)
