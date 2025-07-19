import pickle
import numpy as np
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SwipeRiskPredictor:
    def __init__(self, model_dir: str = './models'):
        self.model_dir = model_dir
        self.feature_names = [
            'speed_mean', 'speed_std', 'direction_mean', 
            'direction_std', 'acceleration_mean', 'acceleration_std'
        ]
        
        # UPDATED: More lenient risk thresholds to reduce false positives
        self.min_samples_required = 5  # NEW: Minimum samples before prediction
    
    def get_risk_category(self, score: float) -> str:
        """Enhanced risk categorization - MORE LENIENT thresholds"""
        # UPDATED: More lenient thresholds to reduce false positives
        if score < -1.5:    # Was -0.6, now much stricter for critical
            return 'critical_risk'
        elif score < -1.2:  # Was -0.4, now stricter for high risk
            return 'high_risk'
        elif score < -0.9:  # Was -0.2, now stricter for medium risk
            return 'medium_risk'
        elif score < -0.5:  # Was -0.1, now stricter for low risk
            return 'low_risk'
        return 'normal'
    
    def validate_session_vector(self, session_vector: List[float]) -> bool:
        """Validate swipe session input"""
        if len(session_vector) != 6:
            logger.error(f"Expected 6 features, got {len(session_vector)}")
            return False
        
        speed_mean, speed_std, direction_mean, direction_std, acceleration_mean, acceleration_std = session_vector
        
        # Validate reasonable ranges
        if not (0 <= speed_mean <= 10):
            logger.warning(f"Unusual speed_mean: {speed_mean}")
        if not (0 <= direction_mean <= 2*np.pi):
            logger.warning(f"Unusual direction_mean: {direction_mean}")
        if not (0 <= acceleration_mean <= 3000):  # Increased upper limit
            logger.warning(f"Unusual acceleration_mean: {acceleration_mean}")
        
        return True
    
    def predict_swipe_risk(self, user_id: str, session_vector: List[float], 
                          sample_count: int = None) -> Dict:
        """Predict swipe risk with minimum sample requirement"""
        try:
            # NEW: Check minimum sample requirement
            if sample_count is not None and sample_count < self.min_samples_required:
                return {
                    'error': f'Insufficient swipe samples: {sample_count} (minimum: {self.min_samples_required})',
                    'requires_more_samples': True,
                    'samples_needed': self.min_samples_required - sample_count
                }
            
            if not self.validate_session_vector(session_vector):
                return {'error': 'Invalid session vector'}
            
            model_path = f'{self.model_dir}/{user_id}_swipe_model.pkl'
            scaler_path = f'{self.model_dir}/{user_id}_swipe_scaler.pkl'
            
            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                return {'error': 'Model not found for this user'}
            
            # Load model and scaler
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            
            # Transform and predict
            X_scaled = scaler.transform([session_vector])
            
            # Get anomaly score and decision function
            anomaly_score = model.score_samples(X_scaled)[0]
            decision_score = model.decision_function(X_scaled)[0]
            is_outlier = model.predict(X_scaled)[0] == -1
            
            risk_category = self.get_risk_category(anomaly_score)
            
            # UPDATED: More conservative confidence calculation
            base_confidence = min(abs(decision_score) * 100, 100)
            # Reduce confidence for swipe predictions (less reliable with fewer samples)
            confidence = base_confidence * 0.7  # Reduced by 30%
            
            # Analyze individual features
            feature_analysis = {}
            for i, (feature_name, value) in enumerate(zip(self.feature_names, session_vector)):
                feature_scaled = X_scaled[0][i]
                feature_analysis[feature_name] = {
                    'value': value,
                    'scaled_value': round(feature_scaled, 4),
                    'contribution': 'high' if abs(feature_scaled) > 2 else 'normal'
                }
            
            return {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'anomaly_score': round(anomaly_score, 4),
                'decision_score': round(decision_score, 4),
                'risk_category': risk_category,
                'is_outlier': is_outlier,
                'confidence': round(confidence, 2),
                'feature_analysis': feature_analysis,
                'session_vector': session_vector,
                'sample_count': sample_count,
                'modality_weight': 0.2  # NEW: Weight for overall risk calculation
            }
            
        except Exception as e:
            logger.error(f"Error predicting swipe risk for {user_id}: {str(e)}")
            return {'error': f'Prediction failed: {str(e)}'}
