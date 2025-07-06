import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SwipeModelUpdater:
    def __init__(self, pool_dir: str = './data/retrain_pool', model_dir: str = './models'):
        self.pool_dir = pool_dir
        self.model_dir = model_dir
        os.makedirs(pool_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)
        
        # Update parameters
        self.min_samples_retrain = 50
        self.contamination = 0.1
        self.max_pool_size = 1000
        self.retrain_interval_days = 7
        
        self.feature_columns = [
            'speed_mean', 'speed_std', 'direction_mean', 
            'direction_std', 'acceleration_mean', 'acceleration_std'
        ]
    
    def add_swipe_session_to_pool(self, user_id: str, session_vector: List[float], 
                                 risk_category: str, metadata: Dict = None) -> bool:
        """Add swipe session to training pool"""
        try:
            pool_path = f'{self.pool_dir}/{user_id}_swipe_pool.csv'
            
            # Create new row
            new_row = {
                'speed_mean': session_vector[0],
                'speed_std': session_vector[1],
                'direction_mean': session_vector[2],
                'direction_std': session_vector[3],
                'acceleration_mean': session_vector[4],
                'acceleration_std': session_vector[5],
                'risk_category': risk_category,
                'timestamp': datetime.now().isoformat(),
                'anomaly_score': metadata.get('anomaly_score', 0) if metadata else 0,
                'is_outlier': metadata.get('is_outlier', False) if metadata else False
            }
            
            df_new = pd.DataFrame([new_row])
            
            # Load existing pool
            if os.path.exists(pool_path):
                df_pool = pd.read_csv(pool_path)
                df_pool = pd.concat([df_pool, df_new], ignore_index=True)
            else:
                df_pool = df_new
            
            # Manage pool size
            if len(df_pool) > self.max_pool_size:
                # Keep most recent samples and maintain class balance
                df_pool = df_pool.sort_values('timestamp').tail(self.max_pool_size)
            
            df_pool.to_csv(pool_path, index=False)
            logger.info(f"Swipe session added to pool for {user_id}. Pool size: {len(df_pool)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding swipe session to pool: {str(e)}")
            return False
    
    def should_retrain_swipe_model(self, user_id: str) -> bool:
        """Determine if swipe model should be retrained"""
        pool_path = f'{self.pool_dir}/{user_id}_swipe_pool.csv'
        
        if not os.path.exists(pool_path):
            return False
        
        df_pool = pd.read_csv(pool_path)
        
        # Check sample count
        if len(df_pool) < self.min_samples_retrain:
            return False
        
        # Check model age
        model_path = f'{self.model_dir}/{user_id}_swipe_model.pkl'
        if os.path.exists(model_path):
            model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
            if model_age > timedelta(days=self.retrain_interval_days):
                return True
        
        # Check if we have enough new samples
        return len(df_pool) % self.min_samples_retrain == 0
    
    def retrain_swipe_model(self, user_id: str) -> Dict:
        """Retrain swipe model with validation"""
        try:
            pool_path = f'{self.pool_dir}/{user_id}_swipe_pool.csv'
            
            if not os.path.exists(pool_path):
                return {'error': 'No training data found'}
            
            df_pool = pd.read_csv(pool_path)
            
            # Extract features
            X = df_pool[self.feature_columns].values
            
            # Remove any NaN values
            mask = ~np.isnan(X).any(axis=1)
            X = X[mask]
            
            if len(X) < self.min_samples_retrain:
                return {'error': f'Insufficient clean data: {len(X)} samples'}
            
            # Split for validation
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
            
            # Save model if validation passes
            if 0.05 <= train_outliers <= 0.2:
                model_path = f'{self.model_dir}/{user_id}_swipe_model.pkl'
                scaler_path = f'{self.model_dir}/{user_id}_swipe_scaler.pkl'
                
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                
                # Update metadata
                metadata = {
                    'user_id': user_id,
                    'retrain_date': datetime.now().isoformat(),
                    'training_samples': len(X_train),
                    'validation_samples': len(X_val),
                    'train_outlier_rate': round(train_outliers, 4),
                    'val_outlier_rate': round(val_outliers, 4),
                    'total_pool_samples': len(df_pool),
                    'clean_samples_used': len(X)
                }
                
                metadata_path = f'{self.model_dir}/{user_id}_swipe_retrain_metadata.json'
                with open(metadata_path, 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Swipe model retrained for {user_id}")
                return {
                    'success': True,
                    'metadata': metadata
                }
            else:
                return {'error': f'Model validation failed: outlier rate {train_outliers:.4f}'}
                
        except Exception as e:
            logger.error(f"Error retraining swipe model for {user_id}: {str(e)}")
            return {'error': f'Retraining failed: {str(e)}'}
    
    def update_swipe_model_if_appropriate(self, user_id: str, session_vector: List[float], 
                                        prediction_result: Dict) -> Dict:
        """Main method to handle swipe model updates"""
        try:
            # Add session to pool (both normal and anomalous for better training)
            risk_category = prediction_result.get('risk_category', 'unknown')
            
            success = self.add_swipe_session_to_pool(
                user_id, session_vector, risk_category, prediction_result
            )
            
            if not success:
                return {'error': 'Failed to add session to pool'}
            
            # Check if retraining is needed
            if self.should_retrain_swipe_model(user_id):
                retrain_result = self.retrain_swipe_model(user_id)
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
            logger.error(f"Error updating swipe model: {str(e)}")
            return {'error': f'Update failed: {str(e)}'}