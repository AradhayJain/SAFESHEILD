import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TypingModelUpdater:
    def __init__(self, pool_dir: str = './data/retrain_pool', model_dir: str = './models'):
        self.pool_dir = pool_dir
        self.model_dir = model_dir
        os.makedirs(pool_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)
        
        # Model parameters
        self.min_samples_retrain = 50  # Increased for better stability
        self.contamination = 0.1
        self.max_pool_size = 1000  # Prevent unlimited growth
        
    def add_session_to_pool(self, user_id: str, session_vector: List[float], 
                           risk_category: str, metadata: Dict = None) -> bool:
        """Add session to training pool with metadata"""
        try:
            pool_path = f'{self.pool_dir}/{user_id}_pool.csv'
            
            # Create new row with metadata
            new_row = {
                'hold_mean': session_vector[0],
                'hold_std': session_vector[1],
                'flight_mean': session_vector[2],
                'flight_std': session_vector[3],
                'backspace_rate': session_vector[4],
                'typing_speed': session_vector[5],
                'risk_category': risk_category,
                'timestamp': datetime.now().isoformat(),
                'anomaly_score': metadata.get('anomaly_score', 0) if metadata else 0
            }
            
            df_new = pd.DataFrame([new_row])
            
            # Load existing pool or create new
            if os.path.exists(pool_path):
                df_pool = pd.read_csv(pool_path)
                df_pool = pd.concat([df_pool, df_new], ignore_index=True)
            else:
                df_pool = df_new
            
            # Manage pool size - keep most recent samples
            if len(df_pool) > self.max_pool_size:
                df_pool = df_pool.tail(self.max_pool_size)
            
            df_pool.to_csv(pool_path, index=False)
            logger.info(f"Session added to pool for user {user_id}. Pool size: {len(df_pool)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding session to pool: {str(e)}")
            return False
    
    def should_retrain(self, user_id: str) -> bool:
        """Determine if model should be retrained"""
        pool_path = f'{self.pool_dir}/{user_id}_pool.csv'
        
        if not os.path.exists(pool_path):
            return False
            
        df_pool = pd.read_csv(pool_path)
        
        # Check if we have enough samples
        if len(df_pool) < self.min_samples_retrain:
            return False
        
        # Check if model exists and how old it is
        model_path = f'{self.model_dir}/{user_id}_typing_model.pkl'
        if os.path.exists(model_path):
            model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
            # Retrain if model is older than 7 days and we have new data
            if model_age > timedelta(days=7):
                return True
        
        # Retrain every N samples
        return len(df_pool) % self.min_samples_retrain == 0
    
    def retrain_model(self, user_id: str) -> Dict:
        """Retrain model with validation"""
        try:
            pool_path = f'{self.pool_dir}/{user_id}_pool.csv'
            
            if not os.path.exists(pool_path):
                return {'error': 'No training data found'}
            
            df_pool = pd.read_csv(pool_path)
            
            # Feature columns
            feature_cols = ['hold_mean', 'hold_std', 'flight_mean', 'flight_std', 
                          'backspace_rate', 'typing_speed']
            
            X = df_pool[feature_cols].values
            
            # Split data for validation
            X_train, X_val = train_test_split(X, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            
            # Train model
            model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
                max_samples='auto'
            )
            model.fit(X_train_scaled)
            
            # Validate model
            train_predictions = model.predict(X_train_scaled)
            val_predictions = model.predict(X_val_scaled)
            
            train_outliers = np.sum(train_predictions == -1) / len(train_predictions)
            val_outliers = np.sum(val_predictions == -1) / len(val_predictions)
            
            # Save model if validation looks reasonable
            if 0.05 <= train_outliers <= 0.2:  # Reasonable outlier rate
                model_path = f'{self.model_dir}/{user_id}_typing_model.pkl'
                scaler_path = f'{self.model_dir}/{user_id}_typing_scaler.pkl'
                
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                
                logger.info(f"Model retrained for user {user_id}")
                
                return {
                    'success': True,
                    'training_samples': len(X_train),
                    'validation_samples': len(X_val),
                    'train_outlier_rate': round(train_outliers, 4),
                    'val_outlier_rate': round(val_outliers, 4),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"Model validation failed for user {user_id}: outlier rate {train_outliers}")
                return {'error': 'Model validation failed'}
                
        except Exception as e:
            logger.error(f"Error retraining model for user {user_id}: {str(e)}")
            return {'error': f'Retraining failed: {str(e)}'}
    
    def update_model_if_appropriate(self, user_id: str, session_vector: List[float], 
                                  prediction_result: Dict) -> Dict:
        """Main method to handle model updates"""
        try:
            # Always add session to pool for future analysis
            risk_category = prediction_result.get('risk_category', 'unknown')
            
            success = self.add_session_to_pool(
                user_id, session_vector, risk_category, prediction_result
            )
            
            if not success:
                return {'error': 'Failed to add session to pool'}
            
            # Check if retraining is needed
            if self.should_retrain(user_id):
                retrain_result = self.retrain_model(user_id)
                return {
                    'pool_updated': True,
                    'retrain_attempted': True,
                    'retrain_result': retrain_result
                }
            
            return {
                'pool_updated': True,
                'retrain_attempted': False,
                'message': 'Session added to pool, retraining not needed yet'
            }
            
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            return {'error': f'Update failed: {str(e)}'}

# Example usage
if __name__ == '__main__':
    # Initialize components
    predictor = TypingRiskPredictor()
    updater = TypingModelUpdater()
    
    # Example session
    test_vector = [95.0, 12.0, 145.0, 25.0, 0.1, 5.2]
    user_id = 'user123'
    
    # Predict risk
    prediction = predictor.predict_risk(user_id, test_vector)
    print("Prediction:", prediction)
    
    # Update model if appropriate
    if 'error' not in prediction:
        update_result = updater.update_model_if_appropriate(user_id, test_vector, prediction)
        print("Update result:", update_result)