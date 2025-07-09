import pandas as pd
import pickle
import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TypingModelTrainer:
    def __init__(self, model_dir: str = './models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        self.contamination = 0.1
        self.n_estimators = 100
        self.random_state = 42
        self.min_samples = 8
        
        self.feature_columns = [
            'hold_mean', 'hold_std', 'flight_mean', 'flight_std',
            'backspace_rate', 'typing_speed'
        ]

    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        if len(df) < self.min_samples:
            return False, f"Insufficient data: {len(df)} samples (minimum: {self.min_samples})"
        
        missing_cols = set(self.feature_columns) - set(df.columns)
        if missing_cols:
            return False, f"Missing columns: {missing_cols}"
        
        if df[self.feature_columns].isnull().any().any():
            logger.warning("Data contains null values - will be handled")

        if not (0 <= df['hold_mean'].min() and df['hold_mean'].max() <= 1000):
            logger.warning(f"Unusual hold_mean range: {df['hold_mean'].min()}-{df['hold_mean'].max()} ms")
        
        if not (0 <= df['flight_mean'].min() and df['flight_mean'].max() <= 2000):
            logger.warning(f"Unusual flight_mean range: {df['flight_mean'].min()}-{df['flight_mean'].max()} ms")
        
        if not (0 <= df['backspace_rate'].min() and df['backspace_rate'].max() <= 1):
            logger.warning(f"Invalid backspace_rate range: {df['backspace_rate'].min()}-{df['backspace_rate'].max()}")
        
        if not (5 <= df['typing_speed'].min() and df['typing_speed'].max() <= 200):
            logger.warning(f"Unusual typing_speed range: {df['typing_speed'].min()}-{df['typing_speed'].max()} WPM")
        
        return True, "Data validation passed"

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean = df.copy()
        df_clean = df_clean.dropna(subset=self.feature_columns)

        for col in self.feature_columns:
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]

        logger.info(f"Data preprocessing: {len(df)} -> {len(df_clean)} samples")
        return df_clean

    # Add this method to TypingModelTrainer class:

def train_typing_model_from_dataframe(self, user_id: str, df: pd.DataFrame) -> Dict:
    """Train a personalized typing model from DataFrame (for onboarding)"""
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
            model_path = f'{self.model_dir}/{user_id}_typing_model.pkl'
            scaler_path = f'{self.model_dir}/{user_id}_typing_scaler.pkl'
            
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
            
            metadata_path = f'{self.model_dir}/{user_id}_typing_metadata.json'
            with open(metadata_path, 'w') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Typing model trained from DataFrame for {user_id}")
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
        logger.error(f"Error training typing model from DataFrame for {user_id}: {str(e)}")
        return {'error': f'Training failed: {str(e)}'}