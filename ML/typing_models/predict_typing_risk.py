import pickle
import numpy as np
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class TypingRiskPredictor:
    def __init__(self, model_dir: str = './models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # NEW: Minimum samples required before making predictions
        self.min_samples_required = 20
    
    def get_risk_category(self, score: float) -> str:
        """Enhanced risk categorization - MORE LENIENT thresholds"""
        # UPDATED: More lenient thresholds to reduce false positives
        if score < -0.8:    # Was -0.6, now much stricter for critical
            return 'critical_risk'
        elif score < -0.65:  # Was -0.4, now stricter for high risk
            return 'high_risk'
        elif score < -0.45:  # Was -0.2, now stricter for medium risk
            return 'medium_risk'
        elif score < -0.25:  # Was -0.1, now stricter for low risk
            return 'low_risk'
        return 'normal'
    
    def validate_session_vector(self, session_vector: List[float]) -> bool:
        """Validate input data quality - Updated for new typing speed format"""
        if len(session_vector) != 6:
            logger.error(f"Expected 6 features, got {len(session_vector)}")
            return False
        
        hold_mean, hold_std, flight_mean, flight_std, backspace_rate, typing_speed = session_vector
        
        # Updated validation ranges
        if not (0 <= hold_mean <= 1000):
            logger.warning(f"Unusual hold_mean: {hold_mean}")
        if not (0 <= flight_mean <= 1000):
            logger.warning(f"Unusual flight_mean: {flight_mean}")
        if not (0 <= backspace_rate <= 1):
            logger.warning(f"Unusual backspace_rate: {backspace_rate}")
        if not (0 <= typing_speed <= 50):  # Increased range for chars/sec
            logger.warning(f"Unusual typing_speed (chars/sec): {typing_speed}")
            
        return True
    
    def predict_risk(self, user_id: str, session_vector: List[float], 
                    sample_count: int = None) -> Dict:
        """Predict risk with minimum sample requirement"""
        try:
            # NEW: Check minimum sample requirement
            if sample_count is not None and sample_count < self.min_samples_required:
                return {
                    'error': f'Insufficient typing samples: {sample_count} (minimum: {self.min_samples_required})',
                    'requires_more_samples': True,
                    'samples_needed': self.min_samples_required - sample_count
                }
            
            if not self.validate_session_vector(session_vector):
                return {'error': 'Invalid session vector'}
            
            model_path = f'{self.model_dir}/{user_id}_typing_model.pkl'
            scaler_path = f'{self.model_dir}/{user_id}_typing_scaler.pkl'
            
            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                return {'error': 'Model not found for this user'}
            
            # Load model and scaler
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            
            # Transform and predict
            X_scaled = scaler.transform([session_vector])
            score = model.score_samples(X_scaled)[0]
            risk = self.get_risk_category(score)
            
            # Calculate confidence based on decision boundary distance
            decision_scores = model.decision_function(X_scaled)
            base_confidence = min(abs(decision_scores[0]) * 100, 100)
            # Typing gets higher confidence (more data available)
            confidence = base_confidence * 1.1  # Boost by 10%
            confidence = min(confidence, 100)  # Cap at 100%
            
            return {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'anomaly_score': round(score, 4),
                'decision_score': round(decision_scores[0], 4),
                'risk_category': risk,
                'confidence': round(confidence, 2),
                'features': {
                    'hold_mean': session_vector[0],
                    'hold_std': session_vector[1],
                    'flight_mean': session_vector[2],
                    'flight_std': session_vector[3],
                    'backspace_rate': session_vector[4],
                    'typing_speed_chars_per_sec': session_vector[5]
                },
                'sample_count': sample_count,
                'modality_weight': 0.8  # NEW: Weight for overall risk calculation
            }
            
        except Exception as e:
            logger.error(f"Error predicting risk for user {user_id}: {str(e)}")
            return {'error': f'Prediction failed: {str(e)}'}