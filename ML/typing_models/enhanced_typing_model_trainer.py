import pandas as pd
import pickle
import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold, TimeSeriesSplit
from sklearn.metrics import silhouette_score
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTypingModelTrainer:
    """
    Enhanced typing model trainer with cross-validation and transfer learning
    Handles the insufficient data problem during onboarding phase
    """
    
    def __init__(self, model_dir: str = './models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Relaxed parameters for onboarding (small datasets)
        self.min_samples_onboarding = 15  # Reduced from 50
        self.min_samples_full = 50
        self.contamination_onboarding = 0.15  # More lenient
        self.contamination_full = 0.1
        self.n_estimators = 100
        self.random_state = 42
        
        # Standardized feature columns (matching data controller output)
        self.feature_columns = [
            'hold_mean', 'hold_std', 'flight_mean', 'flight_std',
            'backspace_rate', 'typing_speed'
        ]
        
        # Population baseline for transfer learning (helps with small datasets)
        self.population_baseline = {
            'hold_mean': 150.0, 'hold_std': 25.0,
            'flight_mean': 200.0, 'flight_std': 30.0,
            'backspace_rate': 0.1, 'typing_speed': 3.5
        }

    def validate_data(self, df: pd.DataFrame, is_onboarding: bool = False) -> Tuple[bool, str]:
        """Enhanced validation with onboarding consideration"""
        min_samples = self.min_samples_onboarding if is_onboarding else self.min_samples_full
        
        if len(df) < min_samples:
            return False, f"Insufficient data: {len(df)} samples (minimum: {min_samples})"
        
        missing_cols = set(self.feature_columns) - set(df.columns)
        if missing_cols:
            return False, f"Missing columns: {missing_cols}"
        
        # Check for data quality
        if df[self.feature_columns].isnull().sum().sum() > len(df) * 0.2:
            return False, "Too many missing values (>20%)"
        
        # Validate reasonable ranges with warnings (not failures)
        validations = [
            (df['hold_mean'], 10, 1000, "hold_mean"),
            (df['flight_mean'], 10, 2000, "flight_mean"), 
            (df['backspace_rate'], 0, 1, "backspace_rate"),
            (df['typing_speed'], 0.5, 15, "typing_speed")
        ]
        
        for col_data, min_val, max_val, col_name in validations:
            if not (min_val <= col_data.min() and col_data.max() <= max_val):
                logger.warning(f"Unusual {col_name} range: {col_data.min():.2f}-{col_data.max():.2f}")
        
        return True, "Data validation passed"

    def preprocess_data(self, df: pd.DataFrame, is_onboarding: bool = False) -> pd.DataFrame:
        """Enhanced preprocessing with outlier handling"""
        df_clean = df.copy()
        
        # Handle missing values
        df_clean = df_clean.fillna(df_clean.median())
        
        # For onboarding, be more conservative with outlier removal
        outlier_threshold = 2.0 if is_onboarding else 1.5
        
        for col in self.feature_columns:
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR > 0:
                lower_bound = Q1 - outlier_threshold * IQR
                upper_bound = Q3 + outlier_threshold * IQR
                
                # For onboarding, clip outliers instead of removing
                if is_onboarding:
                    df_clean[col] = df_clean[col].clip(lower_bound, upper_bound)
                else:
                    df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]

        logger.info(f"Data preprocessing: {len(df)} -> {len(df_clean)} samples")
        return df_clean

    def add_population_baseline(self, df: pd.DataFrame, weight: float = 0.3) -> pd.DataFrame:
        """Add population baseline data for transfer learning"""
        baseline_samples = max(5, int(len(df) * weight))
        
        baseline_data = []
        for _ in range(baseline_samples):
            # Add some noise to baseline values
            sample = {}
            for feature, base_value in self.population_baseline.items():
                noise_factor = 0.1  # 10% noise
                noise = np.random.normal(0, base_value * noise_factor)
                sample[feature] = base_value + noise
            baseline_data.append(sample)
        
        baseline_df = pd.DataFrame(baseline_data)
        combined_df = pd.concat([df, baseline_df], ignore_index=True)
        
        logger.info(f"Added {baseline_samples} baseline samples for transfer learning")
        return combined_df

    def cross_validate_model(self, X: np.ndarray, contamination: float) -> Tuple[float, float]:
        """Perform cross-validation for model selection"""
        if len(X) < 10:
            # For very small datasets, use simple validation
            model = IsolationForest(
                contamination=contamination,
                random_state=self.random_state,
                n_estimators=50
            )
            model.fit(X)
            scores = model.score_samples(X)
            return np.mean(scores), np.std(scores)
        
        # For larger datasets, use proper cross-validation
        scores = []
        cv_folds = min(5, len(X) // 5)  # Adjust folds based on data size
        
        for _ in range(cv_folds):
            # Random split for unsupervised learning
            indices = np.random.choice(len(X), size=int(0.8 * len(X)), replace=False)
            X_train = X[indices]
            X_val = np.delete(X, indices, axis=0)
            
            model = IsolationForest(
                contamination=contamination,
                random_state=self.random_state,
                n_estimators=self.n_estimators
            )
            model.fit(X_train)
            
            # Evaluate on validation set
            val_scores = model.score_samples(X_val)
            scores.extend(val_scores)
        
        return np.mean(scores), np.std(scores)

    def train_typing_model_from_dataframe(self, user_id: str, df: pd.DataFrame, is_onboarding: bool = True) -> Dict:
        """Enhanced training with cross-validation and transfer learning"""
        try:
            logger.info(f"Training typing model for user {user_id} (onboarding: {is_onboarding})")
            
            # Validate input
            is_valid, message = self.validate_data(df, is_onboarding)
            if not is_valid:
                return {'error': message}
            
            # Preprocess data
            df_clean = self.preprocess_data(df, is_onboarding)
            
            # Add population baseline for small datasets
            if is_onboarding and len(df_clean) < 30:
                df_clean = self.add_population_baseline(df_clean)
            
            # Extract features
            X = df_clean[self.feature_columns].values
            
            # Select contamination based on dataset size
            contamination = self.contamination_onboarding if is_onboarding else self.contamination_full
            
            # Perform cross-validation
            cv_mean, cv_std = self.cross_validate_model(X, contamination)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train final model on all data
            model = IsolationForest(
                n_estimators=self.n_estimators,
                contamination=contamination,
                random_state=self.random_state,
                max_samples='auto',
                bootstrap=True  # Add bootstrap for better generalization
            )
            model.fit(X_scaled)
            
            # Validate model performance
            predictions = model.predict(X_scaled)
            outlier_rate = np.sum(predictions == -1) / len(predictions)
            
            # Calculate silhouette score for clustering quality
            try:
                silhouette_avg = silhouette_score(X_scaled, predictions)
            except:
                silhouette_avg = -1  # Fallback if silhouette calculation fails
            
            # More lenient validation for onboarding
            valid_outlier_range = (0.05, 0.4) if is_onboarding else (0.05, 0.2)
            
            if valid_outlier_range[0] <= outlier_rate <= valid_outlier_range[1]:
                # Save model and scaler
                model_path = f'{self.model_dir}/{user_id}_typing_model.pkl'
                scaler_path = f'{self.model_dir}/{user_id}_typing_scaler.pkl'
                
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                
                # Save comprehensive metadata
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
                    'silhouette_score': round(silhouette_avg, 4),
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
                
                metadata_path = f'{self.model_dir}/{user_id}_typing_metadata.json'
                with open(metadata_path, 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Typing model successfully trained for {user_id}")
                return {
                    'success': True,
                    'message': f'Model trained successfully for {user_id}',
                    'metadata': metadata,
                    'model_path': model_path,
                    'scaler_path': scaler_path,
                    'model_quality': {
                        'outlier_rate': outlier_rate,
                        'cv_score': cv_mean,
                        'silhouette_score': silhouette_avg,
                        'confidence': 'high' if cv_std < 0.1 else 'medium' if cv_std < 0.2 else 'low'
                    }
                }
            else:
                return {
                    'error': f'Model validation failed: outlier rate {outlier_rate:.4f} outside valid range {valid_outlier_range}',
                    'details': {
                        'outlier_rate': outlier_rate,
                        'valid_range': valid_outlier_range,
                        'cv_score': cv_mean,
                        'silhouette_score': silhouette_avg
                    }
                }
                
        except Exception as e:
            logger.error(f"Error training typing model for {user_id}: {str(e)}")
            return {'error': f'Training failed: {str(e)}'}

    def create_sample_data_for_testing(self, user_id: str, num_samples: int = 50) -> pd.DataFrame:
        """Generate realistic sample data for testing"""
        np.random.seed(42)  # For reproducible testing
        
        # Generate correlated features that simulate real typing behavior
        samples = []
        for i in range(num_samples):
            # Base typing characteristics with individual variation
            base_hold = np.random.normal(150, 30)
            base_flight = np.random.normal(200, 40)
            base_speed = np.random.normal(60, 15)
            
            # Add correlation between features
            hold_mean = max(50, base_hold + np.random.normal(0, 10))
            hold_std = max(5, hold_mean * 0.15 + np.random.normal(0, 5))
            
            flight_mean = max(50, base_flight + np.random.normal(0, 15))
            flight_std = max(5, flight_mean * 0.12 + np.random.normal(0, 8))
            
            typing_speed = max(20, base_speed + np.random.normal(0, 8))
            
            # Backspace rate correlated with typing speed (faster typists make more mistakes)
            backspace_rate = max(0, min(0.5, 0.15 - (typing_speed - 60) * 0.002 + np.random.normal(0, 0.05)))
            
            samples.append({
                'hold_mean': hold_mean,
                'hold_std': hold_std,
                'flight_mean': flight_mean,
                'flight_std': flight_std,
                'backspace_rate': backspace_rate,
                'typing_speed': typing_speed
            })
        
        df = pd.DataFrame(samples)
        
        # Save test data
        test_data_path = f'{self.model_dir}/{user_id}_typing_test_data.csv'
        df.to_csv(test_data_path, index=False)
        
        logger.info(f"Generated {num_samples} typing test samples for {user_id}")
        return df

    def train_typing_model(self, user_id: str) -> Dict:
        """Legacy method for backward compatibility"""
        try:
            # This method should load CSV data and call train_typing_model_from_dataframe
            csv_path = f'./data/{user_id}_typing_session_dataset.csv'
            
            if not os.path.exists(csv_path):
                return {'error': f'Training data file not found: {csv_path}'}
            
            df = pd.read_csv(csv_path)
            return self.train_typing_model_from_dataframe(user_id, df, is_onboarding=False)
            
        except Exception as e:
            logger.error(f"Error in legacy train_typing_model for {user_id}: {str(e)}")
            return {'error': f'Legacy training failed: {str(e)}'}


# Test function
def test_enhanced_typing_trainer():
    """Test the enhanced typing model trainer"""
    print("Testing Enhanced Typing Model Trainer")
    print("=" * 50)
    
    trainer = EnhancedTypingModelTrainer()
    test_user_id = "test_typing_user_001"
    
    print("\n1. Generating test data...")
    test_data = trainer.create_sample_data_for_testing(test_user_id, 25)
    print(f"Generated typing test data shape: {test_data.shape}")
    print("Sample data:")
    print(test_data.head(3))
    
    print("\n2. Training model...")
    result = trainer.train_typing_model_from_dataframe(test_user_id, test_data, is_onboarding=True)
    
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
    test_enhanced_typing_trainer()
