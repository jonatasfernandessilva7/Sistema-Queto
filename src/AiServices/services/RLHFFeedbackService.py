"""
RLHF Feedback Service
Handles collection, analysis, and application of human feedback to improve C2M model
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sqlite3
import uuid

from src.backend.models.ReportFeedback import (
    ReportFeedback,
    ReportFeedbackCreate,
    FeedbackStats,
    WeightAdjustment,
    FeedbackAnalysis
)
from src.agents.orchestrator import (
    C2MOrchestrator,
    CRISIS_THRESHOLD,
    MONTE_CARLO_SIMULATIONS
)
from src.AiServices.services.WeightManager import (
    get_weight_manager,
    initialize_weight_manager
)

log = logging.getLogger(__name__)


class RLHFFeedbackService:
    """
    Service for managing RLHF feedback loop
    
    Responsibilities:
    - Receive and store feedback from users
    - Analyze feedback patterns
    - Calculate weight adjustments
    - Apply adjustments to C2M components
    """
    
    def __init__(self, db_path: str = None, weights_file: str = None):
        """
        Initialize RLHF Feedback Service
        
        Args:
            db_path: Path to feedback database (default: data/feedback.db)
            weights_file: Path to weights configuration (default: data/c2m_weights.json)
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "feedback.db")
        
        self.db_path = db_path
        self._ensure_db()
        
        # Initialize weight manager
        self.weight_manager = initialize_weight_manager(weights_file)
        
        # Weight adjustment thresholds
        self.false_positive_threshold = 0.2  # If FP rate > 20%, adjust
        self.false_negative_threshold = 0.15  # If FN rate > 15%, adjust
        self.max_adjustment_step = 0.05  # Don't adjust weights by more than 5%
    
    def _ensure_db(self):
        """Create feedback database and tables if they don't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Feedback table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_feedbacks (
            id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL,
            actual_crisis INTEGER NOT NULL,
            c2m_probability_comment TEXT,
            priority_correct INTEGER,
            risk_agents_relevant INTEGER,
            sentiment_accurate INTEGER,
            feedback_text TEXT,
            user_id TEXT,
            suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed INTEGER DEFAULT 0,
            impact_score REAL DEFAULT 0.0
        )
        """)
        
        # Weight adjustments history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_adjustments (
            id TEXT PRIMARY KEY,
            component TEXT NOT NULL,
            current_value REAL NOT NULL,
            adjustment_amount REAL NOT NULL,
            new_value REAL NOT NULL,
            reason TEXT,
            confidence REAL DEFAULT 0.5,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
    
    def receive_feedback(self, feedback_data: ReportFeedbackCreate) -> ReportFeedback:
        """
        Receive and store feedback from user
        
        Args:
            feedback_data: Feedback data from user
            
        Returns:
            Created ReportFeedback object
        """
        feedback_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO report_feedbacks (
            id, report_id, actual_crisis, c2m_probability_comment,
            priority_correct, risk_agents_relevant, sentiment_accurate,
            feedback_text, user_id, suggestions, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback_id,
            feedback_data.report_id,
            int(feedback_data.actual_crisis),
            feedback_data.c2m_probability_comment,
            int(feedback_data.priority_correct) if feedback_data.priority_correct is not None else None,
            int(feedback_data.risk_agents_relevant) if feedback_data.risk_agents_relevant is not None else None,
            int(feedback_data.sentiment_accurate) if feedback_data.sentiment_accurate is not None else None,
            feedback_data.feedback_text,
            feedback_data.user_id,
            feedback_data.suggestions,
            created_at
        ))
        
        conn.commit()
        conn.close()
        
        return ReportFeedback(
            id=feedback_id,
            report_id=feedback_data.report_id,
            actual_crisis=feedback_data.actual_crisis,
            c2m_probability_comment=feedback_data.c2m_probability_comment,
            priority_correct=feedback_data.priority_correct,
            risk_agents_relevant=feedback_data.risk_agents_relevant,
            sentiment_accurate=feedback_data.sentiment_accurate,
            feedback_text=feedback_data.feedback_text,
            user_id=feedback_data.user_id,
            suggestions=feedback_data.suggestions,
            created_at=created_at
        )
    
    def get_feedback_stats(self, report_id: str) -> Optional[FeedbackStats]:
        """
        Get feedback statistics for a report
        
        Args:
            report_id: ID of the report
            
        Returns:
            FeedbackStats object or None if no feedback
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT COUNT(*), SUM(actual_crisis), 
               GROUP_CONCAT(c2m_probability_comment),
               SUM(CAST(priority_correct AS INTEGER)),
               SUM(CAST(risk_agents_relevant AS INTEGER)),
               SUM(CAST(sentiment_accurate AS INTEGER))
        FROM report_feedbacks
        WHERE report_id = ?
        """, (report_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or row[0] == 0:
            return None
        
        total, actual_crises_count, prob_comments, priority_correct_count, \
            risk_agents_count, sentiment_count = row
        
        accuracy_rate = (actual_crises_count / total) if total > 0 else 0.0
        
        # Analyze probability comments
        prob_comment = None
        if prob_comments:
            comments = [c for c in prob_comments.split(',') if c]
            if comments:
                # Most common comment
                prob_comment = max(set(comments), key=comments.count)
        
        priority_accuracy = (priority_correct_count / total) if total > 0 else 0.0
        risk_agents_accuracy = ((risk_agents_count or 0) / total) if total > 0 else 0.0
        sentiment_accuracy = ((sentiment_count or 0) / total) if total > 0 else 0.0
        
        return FeedbackStats(
            total_feedbacks=total,
            accuracy_rate=accuracy_rate,
            probability_accuracy=prob_comment,
            priority_accuracy=priority_accuracy,
            risk_agents_accuracy=risk_agents_accuracy,
            sentiment_accuracy=sentiment_accuracy
        )
    
    def analyze_feedback_patterns(self, min_feedbacks: int = 10) -> Optional[FeedbackAnalysis]:
        """
        Analyze feedback patterns to detect systematic issues
        
        Requires C2M probability to be stored with feedback for proper analysis.
        Currently reconstructs decision from feedback comments.
        
        Args:
            min_feedbacks: Minimum feedbacks required for analysis
            
        Returns:
            FeedbackAnalysis with metrics for weight adjustment
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all unprocessed feedbacks
        cursor.execute("""
        SELECT id, report_id, actual_crisis, c2m_probability_comment 
        FROM report_feedbacks
        WHERE processed = 0
        ORDER BY created_at DESC
        """)
        
        feedbacks = cursor.fetchall()
        conn.close()
        
        if len(feedbacks) < min_feedbacks:
            log.warning(f"Not enough feedbacks for analysis: {len(feedbacks)} < {min_feedbacks}")
            return None
        
        # Analyze feedback patterns
        # Note: Ideally, we'd have stored the original C2M prediction probability
        # For now, we infer it from the comments
        true_positives = 0    # Predicted crisis, was crisis
        true_negatives = 0    # Predicted no crisis, wasn't crisis
        false_positives = 0   # Predicted crisis, wasn't crisis
        false_negatives = 0   # Predicted no crisis, was crisis
        
        for fb in feedbacks:
            actual_crisis = bool(fb['actual_crisis'])
            
            # Infer C2M prediction from comment
            # If no comment, we can't determine - skip
            if not fb['c2m_probability_comment']:
                continue
            
            comment = fb['c2m_probability_comment']
            
            # c2m_probability_comment can be: "too_high", "too_low", "accurate"
            if comment == "accurate":
                # C2M was correct
                if actual_crisis:
                    true_positives += 1
                else:
                    true_negatives += 1
            elif comment == "too_high":
                # C2M predicted higher than reality
                # Means C2M said crisis but wasn't
                false_positives += 1
            elif comment == "too_low":
                # C2M predicted lower than reality
                # Means C2M said no crisis but it was
                false_negatives += 1
        
        # If no valid data, return None
        total = true_positives + true_negatives + false_positives + false_negatives
        if total == 0:
            log.warning("No valid feedback data for pattern analysis")
            return None
        
        log.info(f"Feedback Analysis: TP={true_positives}, TN={true_negatives}, "
                 f"FP={false_positives}, FN={false_negatives}")
        
        return FeedbackAnalysis(
            false_positives=false_positives,
            false_negatives=false_negatives,
            true_positives=true_positives,
            true_negatives=true_negatives
        )
    
    def calculate_weight_adjustments(
        self,
        feedback_analysis: FeedbackAnalysis
    ) -> List[WeightAdjustment]:
        """
        Calculate recommended weight adjustments based on feedback patterns
        
        Args:
            feedback_analysis: Analysis of feedback patterns
            
        Returns:
            List of recommended weight adjustments
        """
        adjustments = []
        
        # Check false positive rate (predicted crisis, wasn't)
        fp_rate = feedback_analysis.false_positives / (
            feedback_analysis.false_positives + feedback_analysis.true_negatives
        ) if (feedback_analysis.false_positives + feedback_analysis.true_negatives) > 0 else 0.0
        
        # Check false negative rate (didn't predict crisis, was)
        fn_rate = feedback_analysis.false_negatives / (
            feedback_analysis.false_negatives + feedback_analysis.true_positives
        ) if (feedback_analysis.false_negatives + feedback_analysis.true_positives) > 0 else 0.0
        
        # Adjust CRISIS_THRESHOLD based on false positive rate
        if fp_rate > self.false_positive_threshold:
            # Too many false positives, raise threshold
            adjustment = min(fp_rate * self.max_adjustment_step, self.max_adjustment_step)
            new_threshold = min(CRISIS_THRESHOLD + adjustment, 0.9)
            
            adjustments.append(WeightAdjustment(
                component="crisis_threshold",
                current_value=CRISIS_THRESHOLD,
                adjustment_amount=adjustment,
                new_value=new_threshold,
                reason=f"High false positive rate ({fp_rate:.1%})",
                confidence=min(0.5 + fp_rate, 1.0),
                timestamp=datetime.now()
            ))
        
        # Adjust Decision Tree sentiment factor based on false negatives
        if fn_rate > self.false_negative_threshold:
            # Too many false negatives, increase sentiment sensitivity
            adjustment = min(fn_rate * self.max_adjustment_step, self.max_adjustment_step)
            current_sentiment_weight = 0.25  # Current weight in decision tree
            new_sentiment_weight = min(current_sentiment_weight + adjustment, 0.40)
            
            adjustments.append(WeightAdjustment(
                component="decision_tree_sentiment",
                current_value=current_sentiment_weight,
                adjustment_amount=adjustment,
                new_value=new_sentiment_weight,
                reason=f"High false negative rate ({fn_rate:.1%})",
                confidence=min(0.5 + fn_rate, 1.0),
                timestamp=datetime.now()
            ))
        
        # Adjust Monte Carlo modifiers based on overall accuracy
        if feedback_analysis.accuracy < 0.8:
            # Low accuracy, increase Monte Carlo simulations visibility
            # or adjust sentiment modifier
            adjustment = (1.0 - feedback_analysis.accuracy) * 0.1
            current_modifier = 0.2  # Current sentiment modifier
            new_modifier = min(current_modifier + adjustment, 0.35)
            
            adjustments.append(WeightAdjustment(
                component="monte_carlo_sentiment_modifier",
                current_value=current_modifier,
                adjustment_amount=adjustment,
                new_value=new_modifier,
                reason=f"Low overall accuracy ({feedback_analysis.accuracy:.1%})",
                confidence=feedback_analysis.accuracy,
                timestamp=datetime.now()
            ))
        
        return adjustments
    
    def apply_weight_adjustment(self, adjustment: WeightAdjustment) -> bool:
        """
        Apply a weight adjustment to the C2M system
        
        Uses WeightManager to persist adjustments dynamically.
        
        Args:
            adjustment: WeightAdjustment to apply
            
        Returns:
            True if successful
        """
        adj_id = str(uuid.uuid4())
        
        try:
            # Validate adjustment bounds
            new_value = adjustment.new_value
            
            # Apply constraints based on component type
            if adjustment.component == "monte_carlo_simulations":
                new_value = int(max(1000, min(new_value, 1000000)))
            else:
                new_value = float(max(0.0, min(new_value, 2.0)))  # Clamp to 0-2
            
            # Apply to weight manager
            success = self.weight_manager.update_weight(
                adjustment.component,
                new_value
            )
            
            if not success:
                log.error(f"Failed to update weight {adjustment.component}")
                return False
            
            # Store in database for history/audit trail
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO weight_adjustments (
                id, component, current_value, adjustment_amount,
                new_value, reason, confidence, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                adj_id,
                adjustment.component,
                adjustment.current_value,
                adjustment.adjustment_amount,
                new_value,  # Use clamped value
                adjustment.reason,
                adjustment.confidence,
                adjustment.timestamp
            ))
            
            conn.commit()
            conn.close()
            
            log.info(
                f"✓ Weight adjustment applied: {adjustment.component} "
                f"({adjustment.current_value:.4f} → {new_value:.4f}) "
                f"- Reason: {adjustment.reason}"
            )
            
            return True
            
        except Exception as e:
            log.error(f"Error applying weight adjustment: {e}")
            return False
    
    def mark_feedback_processed(self, report_id: str) -> bool:
        """
        Mark feedbacks as processed after applying adjustments
        
        Args:
            report_id: ID of report
            
        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE report_feedbacks
        SET processed = 1
        WHERE report_id = ?
        """, (report_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    def process_and_apply_adjustments(self, min_feedbacks: int = 10) -> Dict:
        """
        Main RLHF loop: analyze patterns and apply weight adjustments
        
        This is the core of the RLHF implementation:
        1. Analyze feedback patterns
        2. Calculate weight adjustments
        3. Apply adjustments to WeightManager
        4. Mark feedbacks as processed
        
        Args:
            min_feedbacks: Minimum feedbacks to accumulate before triggering adjustments
            
        Returns:
            Dict with results of processing
        """
        log.info("=" * 80)
        log.info("RLHF: Starting feedback processing and weight adjustment")
        log.info("=" * 80)
        
        result = {
            "status": "idle",
            "feedbacks_analyzed": 0,
            "adjustments_applied": [],
            "errors": []
        }
        
        # Step 1: Analyze feedback patterns
        feedback_analysis = self.analyze_feedback_patterns(min_feedbacks)
        
        if feedback_analysis is None:
            result["status"] = "insufficient_feedback"
            log.info(f"RLHF: Insufficient feedback (need {min_feedbacks})")
            return result
        
        result["feedbacks_analyzed"] = (
            feedback_analysis.true_positives + 
            feedback_analysis.true_negatives +
            feedback_analysis.false_positives +
            feedback_analysis.false_negatives
        )
        
        log.info(f"RLHF: Analyzing {result['feedbacks_analyzed']} feedbacks")
        log.info(f"  Accuracy: {feedback_analysis.accuracy:.1%}")
        log.info(f"  Precision: {feedback_analysis.precision:.1%}")
        log.info(f"  Recall: {feedback_analysis.recall:.1%}")
        log.info(f"  F1 Score: {feedback_analysis.f1_score:.1%}")
        
        # Step 2: Calculate weight adjustments
        adjustments = self.calculate_weight_adjustments(feedback_analysis)
        
        if not adjustments:
            result["status"] = "no_adjustments_needed"
            log.info("RLHF: No adjustments needed (system performing well)")
            return result
        
        log.info(f"RLHF: {len(adjustments)} weight adjustments calculated")
        
        # Step 3: Apply adjustments
        for adjustment in adjustments:
            log.info(f"\nApplying adjustment: {adjustment.component}")
            log.info(f"  Current: {adjustment.current_value:.4f}")
            log.info(f"  New:     {adjustment.new_value:.4f}")
            log.info(f"  Reason:  {adjustment.reason}")
            log.info(f"  Confidence: {adjustment.confidence:.1%}")
            
            success = self.apply_weight_adjustment(adjustment)
            
            if success:
                result["adjustments_applied"].append({
                    "component": adjustment.component,
                    "from": adjustment.current_value,
                    "to": adjustment.new_value,
                    "reason": adjustment.reason
                })
            else:
                result["errors"].append(f"Failed to apply adjustment: {adjustment.component}")
        
        # Step 4: Mark feedbacks as processed
        # Get all unprocessed feedback report IDs
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT report_id FROM report_feedbacks WHERE processed = 0")
        reports = cursor.fetchall()
        conn.close()
        
        for (report_id,) in reports:
            self.mark_feedback_processed(report_id)
        
        result["status"] = "completed"
        
        log.info("\n" + "=" * 80)
        log.info(f"RLHF: Processing completed - {len(result['adjustments_applied'])} adjustments applied")
        log.info("=" * 80)
        
        return result
    
    def get_adjustment_history(self, limit: int = 50) -> List[WeightAdjustment]:
        """
        Get recent weight adjustments history
        
        Args:
            limit: Maximum number of adjustments to return
            
        Returns:
            List of recent adjustments
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, component, current_value, adjustment_amount,
               new_value, reason, confidence, timestamp
        FROM weight_adjustments
        ORDER BY timestamp DESC
        LIMIT ?
        """, (limit,))
        
        adjustments = []
        for row in cursor.fetchall():
            adjustments.append(WeightAdjustment(
                component=row[1],
                current_value=row[2],
                adjustment_amount=row[3],
                new_value=row[4],
                reason=row[5],
                confidence=row[6],
                timestamp=datetime.fromisoformat(row[7])
            ))
        
        conn.close()
        return adjustments
    
    def get_feedback(self, feedback_id: str) -> Optional[ReportFeedback]:
        """
        Get a specific feedback record
        
        Args:
            feedback_id: ID of feedback to retrieve
            
        Returns:
            ReportFeedback or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, report_id, actual_crisis, c2m_probability_comment,
               priority_correct, risk_agents_relevant, sentiment_accurate,
               feedback_text, user_id, suggestions, created_at, processed, impact_score
        FROM report_feedbacks
        WHERE id = ?
        """, (feedback_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return ReportFeedback(
            id=row[0],
            report_id=row[1],
            actual_crisis=bool(row[2]),
            c2m_probability_comment=row[3],
            priority_correct=bool(row[4]) if row[4] is not None else None,
            risk_agents_relevant=bool(row[5]) if row[5] is not None else None,
            sentiment_accurate=bool(row[6]) if row[6] is not None else None,
            feedback_text=row[7],
            user_id=row[8],
            suggestions=row[9],
            created_at=datetime.fromisoformat(row[10]),
            processed=bool(row[11]),
            impact_score=row[12]
        )
