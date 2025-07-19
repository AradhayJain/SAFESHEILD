# update_model.py - ENHANCED VERSION (same filename as yours)

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
        
        # ENHANCED: Smarter update parameters
        self.min_samples_retrain = 30  # Reduced for faster adaptation
        self.contamination = 0.08      # Slightly higher for swipe data
        self.max_pool_size = 500       # Reduced for better quality
        self.retrain_interval_days = 5  # More frequent retraining
        
        # ENHANCED: Quality control parameters
        self.confidence_threshold = 0.7    # Only add high-confidence predictions
        self.max_updates_per_day = 20      # Prevent spam updates
        self.quality_score_threshold = 0.6  # Minimum quality for updates
        
        self.feature_columns = [
            'speed_mean', 'speed_std', 'direction_mean', 
            'direction_std', 'acceleration_mean', 'acceleration_std'
        ]
    
    def should_add_to_pool(self, prediction_result: Dict) -> bool:
        """
        ENHANCED: Only add high-quality, low-risk predictions to training pool
        This prevents noise from degrading model performance
        """
        try:
            risk_category = prediction_result.get('risk_category', 'unknown')
            confidence = prediction_result.get('confidence', 0)
            anomaly_score = prediction_result.get('anomaly_score', 0)
            
            # ENHANCED CRITERIA: Only add if ALL conditions are met
            
            # 1. Must be normal or low risk (no suspicious behavior)
            if risk_category not in ['normal', 'low_risk']:
                logger.debug(f"Skipping update: risk={risk_category}")
                return False
            
            # 2. Must have high confidence
            if confidence < self.confidence_threshold:
                logger.debug(f"Skipping update: confidence={confidence:.2f} < {self.confidence_threshold}")
                return False
            
            # 3. Anomaly score should not be too extreme
            if anomaly_score < -0.5:  # Too anomalous even for "normal"
                logger.debug(f"Skipping update: anomaly_score={anomaly_score:.3f} too low")
                return False
            
            # 4. Check daily update limit
            if not self.check_daily_update_limit():
                logger.debug("Skipping update: daily limit reached")
                return False
            
            logger.info(f"✅ Adding to pool: risk={risk_category}, conf={confidence:.2f}, score={anomaly_score:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Error in should_add_to_pool: {str(e)}")
            return False
    
    def check_daily_update_limit(self) -> bool:
        """Check if daily update limit has been reached"""
        try:
            today = datetime.now().date()
            update_log_path = f'{self.pool_dir}/daily_updates.log'
            
            if not os.path.exists(update_log_path):
                return True
            
            # Count today's updates
            today_updates = 0
            with open(update_log_path, 'r') as f:
                for line in f:
                    try:
                        log_date = datetime.fromisoformat(line.strip()).date()
                        if log_date == today:
                            today_updates += 1
                    except:
                        continue
            
            return today_updates < self.max_updates_per_day
            
        except Exception as e:
            logger.error(f"Error checking daily limit: {str(e)}")
            return True
    
    def log_update(self):
        """Log an update for daily tracking"""
        try:
            update_log_path = f'{self.pool_dir}/daily_updates.log'
            with open(update_log_path, 'a') as f:
                f.write(f"{datetime.now().isoformat()}\n")
        except Exception as e:
            logger.error(f"Error logging update: {str(e)}")
    
    def add_swipe_session_to_pool(self, user_id: str, session_vector: List[float], 
                                 risk_category: str, metadata: Dict = None) -> bool:
        """
        ENHANCED: Add swipe session with quality validation
        """
        try:
            # Validate session vector quality
            if not self.validate_session_quality(session_vector):
                logger.warning("Session quality too low, skipping update")
                return False
            
            pool_path = f'{self.pool_dir}/{user_id}_swipe_pool.csv'
            
            # Create new row with enhanced metadata
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
                'confidence': metadata.get('confidence', 0) if metadata else 0,
                'is_outlier': metadata.get('is_outlier', False) if metadata else False,
                'quality_score': self.calculate_session_quality(session_vector)
            }
            
            df_new = pd.DataFrame([new_row])
            
            # Load existing pool
            if os.path.exists(pool_path):
                df_pool = pd.read_csv(pool_path)
                df_pool = pd.concat([df_pool, df_new], ignore_index=True)
            else:
                df_pool = df_new
            
            # ENHANCED: Quality-based pool management
            df_pool = self.manage_pool_quality(df_pool)
            
            df_pool.to_csv(pool_path, index=False)
            self.log_update()
            
            logger.info(f"✅ Swipe session added to pool for {user_id}. Pool size: {len(df_pool)}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding swipe session to pool: {str(e)}")
            return False
    
    def validate_session_quality(self, session_vector: List[float]) -> bool:
        """Validate session vector quality"""
        try:
            if len(session_vector) != 6:
                return False
            
            # Check for NaN or infinite values
            if not all(np.isfinite(val) for val in session_vector):
                return False
            
            # Check reasonable ranges
            speed_mean, speed_std, dir_mean, dir_std, accel_mean, accel_std = session_vector
            
            if not (0 <= speed_mean <= 20):
                return False
            if not (0 <= dir_mean <= 2 * np.pi + 1):
                return False
            if not (0 <= accel_mean <= 15000):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating session quality: {str(e)}")
            return False
    
    def calculate_session_quality(self, session_vector: List[float]) -> float:
        """Calculate quality score for session"""
        try:
            # Quality based on how "normal" the values look
            speed_mean, speed_std, dir_mean, dir_std, accel_mean, accel_std = session_vector
            
            quality_factors = []
            
            # Speed quality (1.0 is good normal speed)
            speed_quality = 1.0 / (1.0 + abs(speed_mean - 1.0))
            quality_factors.append(speed_quality)
            
            # Direction quality (π is good normal direction)
            dir_quality = 1.0 / (1.0 + abs(dir_mean - np.pi))
            quality_factors.append(dir_quality)
            
            # Acceleration quality (500 is good normal acceleration)
            accel_quality = 1.0 / (1.0 + abs(accel_mean - 500) / 500)
            quality_factors.append(accel_quality)
            
            # Standard deviation quality (not too high, not too low)
            std_quality = 1.0 / (1.0 + abs(speed_std - 0.3) + abs(dir_std - 0.5))
            quality_factors.append(std_quality)
            
            overall_quality = np.mean(quality_factors)
            return float(min(1.0, overall_quality))
            
        except Exception as e:
            logger.error(f"Error calculating session quality: {str(e)}")
            return 0.5
    
    def manage_pool_quality(self, df_pool: pd.DataFrame) -> pd.DataFrame:
        """
        ENHANCED: Manage pool quality by removing low-quality samples
        """
        try:
            # Remove samples older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            df_pool['timestamp'] = pd.to_datetime(df_pool['timestamp'])
            df_pool = df_pool[df_pool['timestamp'] > cutoff_date]
            
            # Keep only high-quality samples if pool is too large
            if len(df_pool) > self.max_pool_size:
                # Sort by quality score and timestamp (prefer recent high-quality)
                df_pool['combined_score'] = (
                    df_pool.get('quality_score', 0.5) * 0.7 + 
                    df_pool.get('confidence', 0.5) * 0.3
                )
                df_pool = df_pool.nlargest(self.max_pool_size, 'combined_score')
                
            # Remove very low quality samples
            min_quality = 0.3
            if 'quality_score' in df_pool.columns:
                df_pool = df_pool[df_pool['quality_score'] >= min_quality]
            
            logger.info(f"Pool management: kept {len(df_pool)} high-quality samples")
            return df_pool
            
        except Exception as e:
            logger.error(f"Error managing pool quality: {str(e)}")
            return df_pool
    
    def should_retrain_swipe_model(self, user_id: str) -> bool:
        """ENHANCED: Smarter retraining decisions"""
        pool_path = f'{self.pool_dir}/{user_id}_swipe_pool.csv'
        
        if not os.path.exists(pool_path):
            return False
        
        df_pool = pd.read_csv(pool_path)
        
        # Check sample count with quality consideration
        high_quality_samples = len(df_pool[df_pool.get('quality_score', 0.5) > 0.6])
        if high_quality_samples < self.min_samples_retrain:
            return False
        
        # Check model age
        model_path = f'{self.model_dir}/{user_id}_swipe_model.pkl'
        if os.path.exists(model_path):
            model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
            
            # Retrain if model is old OR we have enough new quality data
            if model_age > timedelta(days=self.retrain_interval_days):
                return True
            
            # Or if we have significantly more quality data
            if high_quality_samples >= self.min_samples_retrain * 2:
                return True
        
        return False
    
    def retrain_swipe_model(self, user_id: str) -> Dict:
        """ENHANCED: Retrain swipe model with quality validation"""
        try:
            pool_path = f'{self.pool_dir}/{user_id}_swipe_pool.csv'
            
            if not os.path.exists(pool_path):
                return {'error': 'No training data found'}
            
            df_pool = pd.read_csv(pool_path)
            
            # ENHANCED: Use only high-quality samples for retraining
            quality_threshold = 0.6
            if 'quality_score' in df_pool.columns:
                high_quality_df = df_pool[df_pool['quality_score'] >= quality_threshold]
                if len(high_quality_df) >= self.min_samples_retrain:
                    df_pool = high_quality_df
                    logger.info(f"Using {len(df_pool)} high-quality samples for retraining")
            
            # Extract features
            X = df_pool[self.feature_columns].values
            
            # Remove any NaN values
            mask = ~np.isnan(X).any(axis=1)
            X = X[mask]
            
            if len(X) < self.min_samples_retrain:
                return {'error': f'Insufficient clean data: {len(X)} samples'}
            
            # ENHANCED: Better train/validation split
            X_train, X_val = train_test_split(X, test_size=0.2, random_state=42, shuffle=True)
            
            # Scale features with robust scaling
            from sklearn.preprocessing import RobustScaler
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            
            # ENHANCED: Optimized model parameters
            model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=200,  # More trees for better accuracy
                max_samples=0.8,   # Use most of the data
                bootstrap=True,    # Better generalization
                n_jobs=-1         # Faster training
            )
            model.fit(X_train_scaled)
            
            # ENHANCED: Comprehensive validation
            train_predictions = model.predict(X_train_scaled)
            val_predictions = model.predict(X_val_scaled)
            
            train_outliers = np.sum(train_predictions == -1) / len(train_predictions)
            val_outliers = np.sum(val_predictions == -1) / len(val_predictions)
            
            # Calculate stability score
            train_scores = model.score_samples(X_train_scaled)
            val_scores = model.score_samples(X_val_scaled)
            stability = 1.0 - abs(np.mean(train_scores) - np.mean(val_scores))
            
            # ENHANCED: More lenient validation (better for real users)
            valid_outlier_range = (0.02, 0.15)  # 2-15% outliers acceptable
            stability_threshold = 0.3
            
            if (valid_outlier_range[0] <= train_outliers <= valid_outlier_range[1] and 
                stability > stability_threshold):
                
                # Save enhanced model
                model_path = f'{self.model_dir}/{user_id}_swipe_model.pkl'
                scaler_path = f'{self.model_dir}/{user_id}_swipe_scaler.pkl'
                
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                
                # Enhanced metadata
                metadata = {
                    'user_id': user_id,
                    'retrain_date': datetime.now().isoformat(),
                    'training_samples': len(X_train),
                    'validation_samples': len(X_val),
                    'train_outlier_rate': round(train_outliers, 4),
                    'val_outlier_rate': round(val_outliers, 4),
                    'stability_score': round(stability, 4),
                    'total_pool_samples': len(df_pool),
                    'clean_samples_used': len(X),
                    'quality_threshold': quality_threshold,
                    'model_parameters': {
                        'n_estimators': 200,
                        'contamination': self.contamination,
                        'max_samples': 0.8
                    }
                }
                
                metadata_path = f'{self.model_dir}/{user_id}_swipe_retrain_metadata.json'
                with open(metadata_path, 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"✅ Enhanced swipe model retrained for {user_id}")
                return {
                    'success': True,
                    'metadata': metadata
                }
            else:
                return {
                    'error': f'Enhanced validation failed: outliers={train_outliers:.4f}, stability={stability:.4f}',
                    'details': {
                        'train_outliers': train_outliers,
                        'val_outliers': val_outliers,
                        'stability': stability,
                        'valid_range': valid_outlier_range
                    }
                }
                
        except Exception as e:
            logger.error(f"Error retraining enhanced swipe model for {user_id}: {str(e)}")
            return {'error': f'Enhanced retraining failed: {str(e)}'}
    
    def update_swipe_model_if_appropriate(self, user_id: str, session_vector: List[float], 
                                        prediction_result: Dict) -> Dict:
        """
        ENHANCED: Main method with smart update decisions
        """
        try:
            # ENHANCED: First check if we should add this session
            if not self.should_add_to_pool(prediction_result):
                return {
                    'pool_updated': False,
                    'retrain_attempted': False,
                    'reason': 'Session quality/confidence too low for training',
                    'details': {
                        'risk_category': prediction_result.get('risk_category'),
                        'confidence': prediction_result.get('confidence'),
                        'anomaly_score': prediction_result.get('anomaly_score')
                    }
                }
            
            # Add session to pool
            success = self.add_swipe_session_to_pool(
                user_id, session_vector, prediction_result.get('risk_category', 'normal'), prediction_result
            )
            
            if not success:
                return {'error': 'Failed to add session to pool'}
            
            # Check if retraining is needed
            if self.should_retrain_swipe_model(user_id):
                retrain_result = self.retrain_swipe_model(user_id)
                return {
                    'pool_updated': True,
                    'retrain_attempted': True,
                    'retrain_result': retrain_result,
                    'reason': 'High-quality session added and retrain triggered'
                }
            
            return {
                'pool_updated': True,
                'retrain_attempted': False,
                'reason': 'High-quality session added to pool',
                'message': 'Session added to pool, retraining not needed yet'
            }
            
        except Exception as e:
            logger.error(f"Error updating enhanced swipe model: {str(e)}")
            return {'error': f'Enhanced update failed: {str(e)}'}

    def get_pool_statistics(self, user_id: str) -> Dict:
        """Get statistics about the training pool"""
        try:
            pool_path = f'{self.pool_dir}/{user_id}_swipe_pool.csv'
            
            if not os.path.exists(pool_path):
                return {'error': 'No pool data found'}
            
            df_pool = pd.read_csv(pool_path)
            
            # Calculate statistics
            stats = {
                'total_samples': len(df_pool),
                'high_quality_samples': len(df_pool[df_pool.get('quality_score', 0.5) > 0.6]),
                'recent_samples': len(df_pool[pd.to_datetime(df_pool['timestamp']) > datetime.now() - timedelta(days=7)]),
                'risk_distribution': df_pool['risk_category'].value_counts().to_dict(),
                'average_quality': df_pool.get('quality_score', pd.Series([0.5])).mean(),
                'average_confidence': df_pool.get('confidence', pd.Series([0.5])).mean(),
                'oldest_sample': df_pool['timestamp'].min(),
                'newest_sample': df_pool['timestamp'].max()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting pool statistics: {str(e)}")
            return {'error': f'Statistics calculation failed: {str(e)}'}