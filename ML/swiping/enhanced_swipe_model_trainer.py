import pandas as pd
import pickle
import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSwipeModelTrainer:
    """
    Enhanced swipe model trainer with cross-validation and transfer learning
    Handles the insufficient data problem during onboarding phase
    """
    
    def __init__(self, model_dir: str = './models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Relaxed parameters for onboarding
        self.min_samples_onboarding = 10  # Even more relaxed for swipes
        self.min_samples_full = 15
        self.contamination_onboarding = 0.15
        self.contamination_full = 0.1
        self.n_estimators = 100
        self.random_state = 42
        
        # Standardized feature columns (matching data controller output)
        self.feature_columns = [
            'speed_mean', 'speed_std', 'direction_mean', 
            'direction_std', 'acceleration_mean', 'acceleration_std'
        ]
        
        # Population baseline for swipe behavior
        self.population_baseline = {
            'speed_mean': 1.0, 'speed_std': 0.3,
            'direction_mean': np.pi, 'direction_std': np.pi/2,
            'acceleration_mean': 500.0, 'acceleration_std': 200.0
        }

    def validate_data(self, df: pd.DataFrame, is_onboarding: bool = False) -> Tuple[bool, str]:
        """Enhanced validation for swipe data"""
        min_samples = self.min_samples_onboarding if is_onboarding else self.min_samples_full
        
        if len(df) < min_samples:
            return False, f"Insufficient data: {len(df)} samples (minimum: {min_samples})"
        
        missing_cols = set(self.feature_columns) - set(df.columns)
        if missing_cols:
            return False, f"Missing columns: {missing_cols}"
        
        # Check for data quality
        if df[self.feature_columns].isnull().sum().sum() > len(df) * 0.3:
            return False, "Too many missing values (>30%)"
        
        # Validate swipe-specific ranges with warnings
        validations = [
            (df['speed_mean'], 0, 20, "speed_mean"),
            (df['direction_mean'], 0, 2*np.pi, "direction_mean"),
            (df['acceleration_mean'], 0, 5000, "acceleration_mean")
        ]
        
        for col_data, min_val, max_val, col_name in validations:
            if not (min_val <= col_data.min() and col_data.max() <= max_val):
                logger.warning(f"Unusual {col_name} range: {col_data.min():.2f}-{col_data.max():.2f}")
        
        return True, "Swipe data validation passed"

    def preprocess_data(self, df: pd.DataFrame, is_onboarding: bool = False) -> pd.DataFrame:
        """Enhanced preprocessing for swipe data"""
        df_clean = df.copy()
        df_clean = df_clean.fillna(df_clean.median())
        
        # Convert direction to radians if needed (assuming input is in degrees)
        if df_clean['direction_mean'].max() > 2 * np.pi:
            df_clean['direction_mean'] = np.radians(df_clean['direction_mean'])
            if 'direction_std' in df_clean.columns:
                df_clean['direction_std'] = np.radians(df_clean['direction_std'])
        
        # Handle outliers more conservatively for onboarding
        outlier_threshold = 2.5 if is_onboarding else 1.5
        
        for col in self.feature_columns:
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR > 0:
                lower_bound = Q1 - outlier_threshold * IQR
                upper_bound = Q3 + outlier_threshold * IQR
                
                if is_onboarding:
                    df_clean[col] = df_clean[col].clip(lower_bound, upper_bound)
                else:
                    df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]

        logger.info(f"Swipe data preprocessing: {len(df)} -> {len(df_clean)} samples")
        return df_clean

    def add_population_baseline(self, df: pd.DataFrame, weight: float = 0.5) -> pd.DataFrame:
        """Add population baseline data for transfer learning"""
        baseline_samples = max(5, int(len(df) * weight))
        
        baseline_data = []
        for _ in range(baseline_samples):
            sample = {}
            for feature, base_value in self.population_baseline.items():
                noise = np.random.normal(0, base_value * 0.1)
                sample[feature] = base_value + noise
            baseline_data.append(sample)
        
        baseline_df = pd.DataFrame(baseline_data)
        combined_df = pd.concat([df, baseline_df], ignore_index=True)
        
        logger.info(f"Added {baseline_samples} baseline samples for swipe model")
        return combined_df

    def cross_validate_swipe_model(self, X: np.ndarray, contamination: float) -> Tuple[float, float]:
        """Cross-validation for swipe model"""
        if len(X) < 10:
            model = IsolationForest(contamination=contamination, random_state=self.random_state)
            model.fit(X)
            scores = model.score_samples(X)
            return np.mean(scores), np.std(scores)
        
        scores = []
        for _ in range(3):  # 3-fold for swipe data
            indices = np.random.choice(len(X), size=int(0.8 * len(X)), replace=False)
            X_train = X[indices]
            X_val = np.delete(X, indices, axis=0)
            
            model = IsolationForest(contamination=contamination, random_state=self.random_state)
            model.fit(X_train)
            val_scores = model.score_samples(X_val)
            scores.extend(val_scores)
        
        return np.mean(scores), np.std(scores)

    def train_swipe_model_from_dataframe(self, user_id: str, df: pd.DataFrame, is_onboarding: bool = True) -> Dict:
        """Enhanced swipe model training with cross-validation"""
        try:
            logger.info(f"Training swipe model for user {user_id} (onboarding: {is_onboarding})")
            
            is_valid, message = self.validate_data(df, is_onboarding)
            if not is_valid:
                return {'error': message}
            
            df_clean = self.preprocess_data(df, is_onboarding)
            
            if is_onboarding and len(df_clean) < 20:
                # Add population baseline for very small datasets
                df_clean = self.add_population_baseline(df_clean)
            
            X = df_clean[self.feature_columns].values
            contamination = self.contamination_onboarding if is_onboarding else self.contamination_full
            
            # Cross-validation
            cv_mean, cv_std = self.cross_validate_swipe_model(X, contamination)
            
            # Train final model
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            model = IsolationForest(
                n_estimators=self.n_estimators,
                contamination=contamination,
                random_state=self.random_state,
                max_samples='auto',
                bootstrap=True
            )
            model.fit(X_scaled)
            
            # Validate performance
            predictions = model.predict(X_scaled)
            outlier_rate = np.sum(predictions == -1) / len(predictions)
            
            valid_range = (0.05, 0.4) if is_onboarding else (0.05, 0.2)
            
            if valid_range[0] <= outlier_rate <= valid_range[1]:
                # Save model
                model_path = f'{self.model_dir}/{user_id}_swipe_model.pkl'
                scaler_path = f'{self.model_dir}/{user_id}_swipe_scaler.pkl'
                
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                
                # Save metadata
                metadata = {
                    'user_id': user_id,
                    'training_date': datetime.now().isoformat(),
                    'is_onboarding': is_onboarding,
                    'total_samples': len(df),
                    'clean_samples': len(df_clean),
                    'training_samples': len(X),
                    'outlier_rate': round(outlier_rate, 4),
                    'contamination': contamination,
                    'cv_score_mean': round(cv_mean, 4),
                    'cv_score_std': round(cv_std, 4),
                    'feature_columns': self.feature_columns,
                    'model_parameters': {
                        'n_estimators': self.n_estimators,
                        'random_state': self.random_state,
                        'bootstrap': True
                    },
                    'data_quality': {
                        'missing_values_handled': True,
                        'outliers_processed': True,
                        'population_baseline_added': is_onboarding and len(df_clean) > len(df)
                    }
                }
                
                metadata_path = f'{self.model_dir}/{user_id}_swipe_metadata.json'
                with open(metadata_path, 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Swipe model successfully trained for {user_id}")
                return {
                    'success': True,
                    'message': f'Swipe model trained successfully for {user_id}',
                    'metadata': metadata,
                    'model_path': model_path,
                    'scaler_path': scaler_path,
                    'model_quality': {
                        'outlier_rate': outlier_rate,
                        'cv_score': cv_mean,
                        'confidence': 'high' if cv_std < 0.1 else 'medium' if cv_std < 0.2 else 'low'
                    }
                }
            else:
                return {
                    'error': f'Swipe model validation failed: outlier rate {outlier_rate:.4f} outside valid range {valid_range}',
                    'details': {
                        'outlier_rate': outlier_rate,
                        'valid_range': valid_range,
                        'cv_score': cv_mean
                    }
                }
                
        except Exception as e:
            logger.error(f"Error training swipe model for {user_id}: {str(e)}")
            return {'error': f'Swipe training failed: {str(e)}'}

    def create_sample_swipe_data(self, user_id: str, num_samples: int = 30) -> pd.DataFrame:
        """Generate realistic swipe test data"""
        np.random.seed(42)
        
        samples = []
        for i in range(num_samples):
            # Simulate different swipe patterns
            base_speed = np.random.normal(1.0, 0.3)
            base_direction = np.random.uniform(0, 2 * np.pi)
            base_acceleration = np.random.normal(500, 150)
            
            sample = {
                'speed_mean': max(0.1, base_speed + np.random.normal(0, 0.1)),
                'speed_std': max(0.05, base_speed * 0.2 + np.random.normal(0, 0.05)),
                'direction_mean': base_direction,
                'direction_std': max(0.1, np.random.normal(np.pi/4, np.pi/8)),
                'acceleration_mean': max(100, base_acceleration + np.random.normal(0, 50)),
                'acceleration_std': max(50, base_acceleration * 0.3 + np.random.normal(0, 30))
            }
            samples.append(sample)
        
        df = pd.DataFrame(samples)
        test_data_path = f'{self.model_dir}/{user_id}_swipe_test_data.csv'
        df.to_csv(test_data_path, index=False)
        
        logger.info(f"Generated {num_samples} swipe test samples for {user_id}")
        return df

    def train_swipe_model(self, user_id: str) -> Dict:
        """Legacy method for backward compatibility"""
        try:
            # This method should load CSV data and call train_swipe_model_from_dataframe
            csv_path = f'./data/{user_id}_swipe_session_dataset.csv'
            
            if not os.path.exists(csv_path):
                return {'error': f'Training data file not found: {csv_path}'}
            
            df = pd.read_csv(csv_path)
            return self.train_swipe_model_from_dataframe(user_id, df, is_onboarding=False)
            
        except Exception as e:
            logger.error(f"Error in legacy train_swipe_model for {user_id}: {str(e)}")
            return {'error': f'Legacy training failed: {str(e)}'}


# Test function
def test_enhanced_swipe_trainer():
    """Test the enhanced swipe model trainer"""
    print("Testing Enhanced Swipe Model Trainer")
    print("=" * 50)
    
    trainer = EnhancedSwipeModelTrainer()
    test_user_id = "test_swipe_user_001"
    
    print("\n1. Generating test data...")
    test_data = trainer.create_sample_swipe_data(test_user_id, 20)
    print(f"Generated swipe test data shape: {test_data.shape}")
    print("Sample data:")
    print(test_data.head(3))
    
    print("\n2. Training model...")
    result = trainer.train_swipe_model_from_dataframe(test_user_id, test_data, is_onboarding=True)
    
    if result.get('success'):
        print(f"Training successful!")
        print(f"   - Model quality: {result['model_quality']['confidence']}")
        print(f"   - CV score: {result['metadata']['cv_score_mean']:.4f}")
        print(f"   - Outlier rate: {result['metadata']['outlier_rate']:.4f}")
        print(f"   - Training samples: {result['metadata']['training_samples']}")
    else:
        print(f"❌ Training failed: {result.get('error')}")
    
    print("\n" + "=" * 50)
    return result

if __name__ == "__main__":
    test_enhanced_swipe_trainer()