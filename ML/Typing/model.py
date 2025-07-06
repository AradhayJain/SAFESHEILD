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
        self.min_samples = 30
        
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

    def train_typing_model_from_dataframe(self, user_id: str, df: pd.DataFrame) -> Dict:
        """Train a typing model using in-memory DataFrame"""
        try:
            is_valid, message = self.validate_data(df)
            if not is_valid:
                return {'error': message}

            df_clean = self.preprocess_data(df)
            if len(df_clean) < self.min_samples:
                return {'error': f'Insufficient data after preprocessing: {len(df_clean)} samples'}

            X = df_clean[self.feature_columns].values
            X_train, X_val = train_test_split(X, test_size=0.2, random_state=self.random_state)

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)

            model = IsolationForest(
                n_estimators=self.n_estimators,
                contamination=self.contamination,
                random_state=self.random_state,
                max_samples='auto'
            )
            model.fit(X_train_scaled)

            train_preds = model.predict(X_train_scaled)
            val_preds = model.predict(X_val_scaled)

            train_outlier_rate = np.sum(train_preds == -1) / len(train_preds)
            val_outlier_rate = np.sum(val_preds == -1) / len(val_preds)

            if 0.05 <= train_outlier_rate <= 0.2:
                model_path = os.path.join(self.model_dir, f'{user_id}_typing_model.pkl')
                scaler_path = os.path.join(self.model_dir, f'{user_id}_typing_scaler.pkl')

                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)

                metadata = {
                    'user_id': user_id,
                    'training_date': datetime.now().isoformat(),
                    'total_samples': len(df),
                    'training_samples': len(X_train),
                    'validation_samples': len(X_val),
                    'train_outlier_rate': round(train_outlier_rate, 4),
                    'val_outlier_rate': round(val_outlier_rate, 4),
                    'contamination': self.contamination,
                    'feature_columns': self.feature_columns
                }

                metadata_path = os.path.join(self.model_dir, f'{user_id}_typing_metadata.json')
                with open(metadata_path, 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)

                logger.info(f"Typing model trained successfully for {user_id}")
                return {
                    'success': True,
                    'message': f'Model trained successfully for {user_id}',
                    'model_path': model_path,
                    'scaler_path': scaler_path,
                    'metadata_path': metadata_path,
                    'metadata': metadata
                }
            else:
                return {'error': f'Model validation failed: outlier rate {train_outlier_rate:.4f}'}

        except Exception as e:
            logger.error(f"Error training typing model for {user_id}: {str(e)}")
            return {'error': f'Training failed: {str(e)}'}
