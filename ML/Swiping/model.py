import pandas as pd
import pickle
import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SwipeModelTrainer:
    def __init__(self, model_dir: str = './models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Model parameters
        self.contamination = 0.1
        self.n_estimators = 100
        self.random_state = 42
        self.min_samples = 10   # Minimum samples needed for training
        
        # Expected feature columns
        self.feature_columns = [
            'speed_mean', 'speed_std', 'direction_mean', 
            'direction_std', 'acceleration_mean', 'acceleration_std'
        ]

    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        if len(df) < self.min_samples:
            return False, f"Insufficient data: {len(df)} samples (minimum: {self.min_samples})"
        
        missing_cols = set(self.feature_columns) - set(df.columns)
        if missing_cols:
            return False, f"Missing columns: {missing_cols}"
        
        if df[self.feature_columns].isnull().any().any():
            logger.warning("Data contains null values - will be handled")

        if not (0 <= df['speed_mean'].min() and df['speed_mean'].max() <= 10):
            logger.warning(f"Unusual speed_mean range: {df['speed_mean'].min()}-{df['speed_mean'].max()}")
        
        if not (0 <= df['direction_mean'].min() and df['direction_mean'].max() <= 2*np.pi):
            logger.warning(f"Unusual direction_mean range: {df['direction_mean'].min()}-{df['direction_mean'].max()}")
        
        if not (0 <= df['acceleration_mean'].min() and df['acceleration_mean'].max() <= 1000):
            logger.warning(f"Unusual acceleration_mean range: {df['acceleration_mean'].min()}-{df['acceleration_mean'].max()}")

        return True, "Data validation passed"

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()
        df_clean = df_clean.dropna(subset=self.feature_columns)

        for col in self.feature_columns:
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]

        logger.info(f"Data preprocessing: {len(df)} -> {len(df_clean)} samples")
        return df_clean

    # Add this method SwipeModelTrainer class:

    def train_swipe_model_from_dataframe(self, user_id: str, df: pd.DataFrame) -> Dict:
        """Train a personalized swipe model from DataFrame (for onboarding)"""
        try:
            # Validate DataFrame
            is_valid, message = self.validate_data(df)
            if not is_valid:
                return {'error': message}
            
            # Preprocess data
            df_clean = self.preprocess_data(df)
            
            if len(df_clean) < 3:  # Relaxed minimum for onboarding
                return {'error': f'Insufficient data after preprocessing: {len(df_clean)} samples'}
            
            # Extract features
            X = df_clean[self.feature_columns].values
            
            # Adjust for limited data
            if len(X) < 10:
                # Don't split for very small datasets
                X_train = X
                X_val = X  # Use same data for validation
            else:
                X_train, X_val = train_test_split(X, test_size=0.2, random_state=self.random_state)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            
            # Adjust contamination for limited data
            if len(df_clean) < 15:
                contamination = 0.15  # More lenient
            else:
                contamination = self.contamination
            
            # Train model
            model = IsolationForest(
                n_estimators=self.n_estimators,
                contamination=contamination,
                random_state=self.random_state,
                max_samples='auto'
            )
            model.fit(X_train_scaled)
            
            # Validate model performance
            train_predictions = model.predict(X_train_scaled)
            val_predictions = model.predict(X_val_scaled)
            
            train_outliers = np.sum(train_predictions == -1) / len(train_predictions)
            val_outliers = np.sum(val_predictions == -1) / len(val_predictions)
            
            # More lenient validation for onboarding
            if 0.02 <= train_outliers <= 0.3:  # Wider range
                model_path = f'{self.model_dir}/{user_id}_swipe_model.pkl'
                scaler_path = f'{self.model_dir}/{user_id}_swipe_scaler.pkl'
                
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                
                # Save training metadata
                metadata = {
                    'user_id': user_id,
                    'training_date': datetime.now().isoformat(),
                    'total_samples': len(df),
                    'training_samples': len(X_train),
                    'validation_samples': len(X_val),
                    'train_outlier_rate': round(train_outliers, 4),
                    'val_outlier_rate': round(val_outliers, 4),
                    'contamination': contamination,
                    'feature_columns': self.feature_columns,
                    'training_type': 'onboarding_dataframe'
                }
                
                metadata_path = f'{self.model_dir}/{user_id}_swipe_metadata.json'
                with open(metadata_path, 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Swipe model trained from DataFrame for {user_id}")
                return {
                    'success': True,
                    'message': f'Model trained successfully for {user_id}',
                    'metadata': metadata,
                    'model_path': model_path,
                    'scaler_path': scaler_path
                }
            else:
                return {'error': f'Model validation failed: outlier rate {train_outliers:.4f}'}
                
        except Exception as e:
            logger.error(f"Error training swipe model from DataFrame for {user_id}: {str(e)}")
            return {'error': f'Training failed: {str(e)}'}