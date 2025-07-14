import pickle
import numpy as np
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TypingRiskPredictor:
    def __init__(self, model_dir: str = './models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
    
    def get_risk_category(self, score: float) -> str:
        """Categorize risk based on anomaly score with more nuanced thresholds"""
        if score < -0.5:
            return 'high_risk'
        elif score < -0.3:
            return 'medium_risk'
        elif score < -0.1:
            return 'low_risk'
        return 'normal'
    
    def validate_session_vector(self, session_vector: List[float]) -> bool:
        """Validate input data quality"""
        if len(session_vector) != 6:
            logger.error(f"Expected 6 features, got {len(session_vector)}")
            return False
        
        # Check for reasonable ranges
        hold_mean, hold_std, flight_mean, flight_std, backspace_rate, typing_speed = session_vector
        
        if not (0 <= hold_mean <= 1000):  # milliseconds
            logger.warning(f"Unusual hold_mean: {hold_mean}")
        if not (0 <= flight_mean <= 1000):  # milliseconds
            logger.warning(f"Unusual flight_mean: {flight_mean}")
        if not (0 <= backspace_rate <= 1):  # percentage
            logger.warning(f"Unusual backspace_rate: {backspace_rate}")
        if not (0 <= typing_speed <= 200):  # WPM
            logger.warning(f"Unusual typing_speed: {typing_speed}")
            
        return True
    
    def predict_risk(self, user_id: str, session_vector: List[float]) -> Dict:
        """Predict risk with enhanced error handling and validation"""
        try:
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
            confidence = min(abs(decision_scores[0]) * 100, 100)  # Scale to 0-100%
            
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
                    'typing_speed': session_vector[5]
                }
            }
            
        except Exception as e:
            logger.error(f"Error predicting risk for user {user_id}: {str(e)}")
            return {'error': f'Prediction failed: {str(e)}'}