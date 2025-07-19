# update_model (1).py - ENHANCED VERSION (same filename as yours)

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, RobustScaler
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
        
        # ENHANCED: Optimized for your 200+ typing samples
        self.min_samples_retrain = 40   # Lower since typing is more consistent
        self.contamination = 0.05       # Lower contamination for typing
        self.max_pool_size = 800        # Higher for typing (you have more data)
        self.retrain_interval_days = 3  # More frequent for typing
        
        # ENHANCED: Stricter quality control for typing
        self.confidence_threshold = 0.75   # Higher threshold for typing
        self.max_updates_per_day = 30      # More updates allowed for typing
        self.quality_score_threshold = 0.7 # Higher quality threshold
        
    def should_add_to_pool(self, prediction_result: Dict) -> bool:
        """
        ENHANCED: Typing-specific quality control
        Typing patterns are more consistent, so we can be more selective
        """
        try:
            risk_category = prediction_result.get('risk_category', 'unknown')
            confidence = prediction_result.get('confidence', 0)
            anomaly_score = prediction_result.get('anomaly_score', 0)
            
            # ENHANCED CRITERIA for typing behavior
            
            # 1. Must be normal risk only (typing is more predictable)
            if risk_category != 'normal':
                logger.debug(f"Skipping typing update: risk={risk_category}")
                return False
            
            # 2. Higher confidence threshold for typing
            if confidence < self.confidence_threshold:
                logger.debug(f"Skipping typing update: confidence={confidence:.2f} < {self.confidence_threshold}")
                return False
            
            # 3. Stricter anomaly score for typing
            if anomaly_score < -0.3:  # More strict for typing
                logger.debug(f"Skipping typing update: anomaly_score={anomaly_score:.3f} too low")
                return False
            
            # 4. Check daily update limit
            if not self.check_daily_update_limit('typing'):
                logger.debug("Skipping typing update: daily limit reached")
                return False
            
            logger.info(f"✅ Adding typing session: risk={risk_category}, conf={confidence:.2f}, score={anomaly_score:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Error in typing should_add_to_pool: {str(e)}")
            return False
    
    def check_daily_update_limit(self, modality: str = 'typing') -> bool:
        """Check daily update limit for typing"""
        try:
            today = datetime.now().date()
            update_log_path = f'{self.pool_dir}/daily_typing_updates.log'
            
            if not os.path.exists(update_log_path):
                return True
            
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
            logger.error(f"Error checking typing daily limit: {str(e)}")
            return True
    
    def log_typing_update(self):
        """Log typing update"""
        try:
            update_log_path = f'{self.pool_dir}/daily_typing_updates.log'
            with open(update_log_path, 'a') as f:
                f.write(f"{datetime.now().isoformat()}\n")
        except Exception as e:
            logger.error(f"Error logging typing update: {str(e)}")
    
    def add_session_to_pool(self, user_id: str, session_vector: List[float], 
                           risk_category: str, metadata: Dict = None) -> bool:
        """
        ENHANCED: Add typing session with behavioral validation
        """
        try:
            # Validate typing session quality
            if not self.validate_typing_session_quality(session_vector):
                logger.warning("Typing session quality too low, skipping update")
                return False
            
            pool_path = f'{self.pool_dir}/{user_id}_pool.csv'
            
            # Create enhanced typing session record
            new_row = {
                'hold_mean': session_vector[0],
                'hold_std': session_vector[1],
                'flight_mean': session_vector[2],
                'flight_std': session_vector[3],
                'backspace_rate': session_vector[4],
                'typing_speed': session_vector[5],
                'risk_category': risk_category,
                'timestamp': datetime.now().isoformat(),
                'anomaly_score': metadata.get('anomaly_score', 0) if metadata else 0,
                'confidence': metadata.get('confidence', 0) if metadata else 0,
                'quality_score': self.calculate_typing_quality(session_vector),
                'behavioral_consistency': self.calculate_behavioral_consistency(session_vector),
                'typing_rhythm': self.calculate_typing_rhythm_score(session_vector)
            }
            
            df_new = pd.DataFrame([new_row])
            
            # Load existing pool
            if os.path.exists(pool_path):
                df_pool = pd.read_csv(pool_path)
                df_pool = pd.concat([df_pool, df_new], ignore_index=True)
            else:
                df_pool = df_new
            
            # ENHANCED: Typing-specific pool management
            df_pool = self.manage_typing_pool_quality(df_pool)
            
            df_pool.to_csv(pool_path, index=False)
            self.log_typing_update()
            
            logger.info(f"✅ Typing session added to pool for {user_id}. Pool size: {len(df_pool)}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding typing session to pool: {str(e)}")
            return False
    
    def validate_typing_session_quality(self, session_vector: List[float]) -> bool:
        """Validate typing session vector quality"""
        try:
            if len(session_vector) != 6:
                return False
            
            # Check for NaN or infinite values
            if not all(np.isfinite(val) for val in session_vector):
                return False
            
            # Check typing-specific ranges
            hold_mean, hold_std, flight_mean, flight_std, backspace_rate, typing_speed = session_vector
            
            # Reasonable typing ranges
            if not (10 <= hold_mean <= 1000):
                return False
            if not (10 <= flight_mean <= 2000):
                return False
            if not (0 <= backspace_rate <= 1):
                return False
            if not (0.5 <= typing_speed <= 15):  # chars per second
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating typing session quality: {str(e)}")
            return False
    
    def calculate_typing_quality(self, session_vector: List[float]) -> float:
        """Calculate typing-specific quality score"""
        try:
            hold_mean, hold_std, flight_mean, flight_std, backspace_rate, typing_speed = session_vector
            
            quality_factors = []
            
            # Hold time quality (around 150ms is good)
            hold_quality = 1.0 / (1.0 + abs(hold_mean - 150) / 150)
            quality_factors.append(hold_quality)
            
            # Flight time quality (around 200ms is good)
            flight_quality = 1.0 / (1.0 + abs(flight_mean - 200) / 200)
            quality_factors.append(flight_quality)
            
            # Backspace rate quality (low is better)
            backspace_quality = 1.0 - min(backspace_rate, 0.5)
            quality_factors.append(backspace_quality)
            
            # Typing speed quality (around 3-4 chars/sec is normal)
            speed_quality = 1.0 / (1.0 + abs(typing_speed - 3.5) / 3.5)
            quality_factors.append(speed_quality)
            
            # Standard deviation quality (not too high, indicates consistency)
            std_quality = 1.0 / (1.0 + (hold_std + flight_std) / 100)
            quality_factors.append(std_quality)
            
            overall_quality = np.mean(quality_factors)
            return float(min(1.0, overall_quality))
            
        except Exception as e:
            logger.error(f"Error calculating typing quality: {str(e)}")
            return 0.5
    
    def calculate_behavioral_consistency(self, session_vector: List[float]) -> float:
        """Calculate behavioral consistency for typing"""
        try:
            hold_mean, hold_std, flight_mean, flight_std, backspace_rate, typing_speed = session_vector
            
            # Consistency is inverse of variability
            hold_consistency = 1.0 / (1.0 + hold_std / (hold_mean + 1e-6))
            flight_consistency = 1.0 / (1.0 + flight_std / (flight_mean + 1e-6))
            
            # Lower backspace rate indicates better consistency
            backspace_consistency = 1.0 - min(backspace_rate, 0.5)
            
            overall_consistency = (hold_consistency + flight_consistency + backspace_consistency) / 3
            return float(min(1.0, overall_consistency))
            
        except Exception as e:
            logger.error(f"Error calculating behavioral consistency: {str(e)}")
            return 0.5
    
    def calculate_typing_rhythm_score(self, session_vector: List[float]) -> float:
        """Calculate typing rhythm score"""
        try:
            hold_mean, hold_std, flight_mean, flight_std, backspace_rate, typing_speed = session_vector
            
            # Good rhythm = consistent hold/flight ratio
            if flight_mean > 0:
                rhythm_ratio = hold_mean / flight_mean
                ideal_ratio = 0.75  # Typical hold/flight ratio
                rhythm_score = 1.0 / (1.0 + abs(rhythm_ratio - ideal_ratio))
            else:
                rhythm_score = 0.5
            
            # Factor in standard deviations (lower = better rhythm)
            rhythm_stability = 1.0 / (1.0 + (hold_std + flight_std) / 200)
            
            overall_rhythm = (rhythm_score + rhythm_stability) / 2
            return float(min(1.0, overall_rhythm))
            
        except Exception as e:
            logger.error(f"Error calculating typing rhythm: {str(e)}")
            return 0.5
    
    def manage_typing_pool_quality(self, df_pool: pd.DataFrame) -> pd.DataFrame:
        """
        ENHANCED: Manage typing pool with behavioral focus
        """
        try:
            # Remove samples older than 21 days (typing patterns more stable)
            cutoff_date = datetime.now() - timedelta(days=21)
            df_pool['timestamp'] = pd.to_datetime(df_pool['timestamp'])
            df_pool = df_pool[df_pool['timestamp'] > cutoff_date]
            
            # Keep high-quality samples if pool is too large
            if len(df_pool) > self.max_pool_size:
                # Combined score emphasizing behavioral consistency
                df_pool['combined_score'] = (
                    df_pool.get('quality_score', 0.5) * 0.4 + 
                    df_pool.get('confidence', 0.5) * 0.3 +
                    df_pool.get('behavioral_consistency', 0.5) * 0.2 +
                    df_pool.get('typing_rhythm', 0.5) * 0.1
                )
                df_pool = df_pool.nlargest(self.max_pool_size, 'combined_score')
            
            # Remove very low quality samples
            min_quality = 0.4
            if 'quality_score' in df_pool.columns:
                df_pool = df_pool[df_pool['quality_score'] >= min_quality]
            
            # Remove inconsistent typing patterns
            min_consistency = 0.3
            if 'behavioral_consistency' in df_pool.columns:
                df_pool = df_pool[df_pool['behavioral_consistency'] >= min_consistency]
            
            logger.info(f"Typing pool management: kept {len(df_pool)} high-quality typing samples")
            return df_pool
            
        except Exception as e:
            logger.error(f"Error managing typing pool quality: {str(e)}")
            return df_pool
    
    def should_retrain(self, user_id: str) -> bool:
        """ENHANCED: Typing-specific retraining decisions"""
        pool_path = f'{self.pool_dir}/{user_id}_pool.csv'
        
        if not os.path.exists(pool_path):
            return False
            
        df_pool = pd.read_csv(pool_path)
        
        # Check high-quality sample count
        high_quality_samples = len(df_pool[df_pool.get('quality_score', 0.5) > self.quality_score_threshold])
        if high_quality_samples < self.min_samples_retrain:
            return False
        
        # Check behavioral consistency
        consistent_samples = len(df_pool[df_pool.get('behavioral_consistency', 0.5) > 0.5])
        if consistent_samples < self.min_samples_retrain * 0.8:
            return False
        
        # Check model age
        model_path = f'{self.model_dir}/{user_id}_typing_model.pkl'
        if os.path.exists(model_path):
            model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
            
            # More frequent retraining for typing (patterns change less)
            if model_age > timedelta(days=self.retrain_interval_days):
                return True
            
            # Or if we have lots of new consistent data
            if consistent_samples >= self.min_samples_retrain * 1.5:
                return True
        
        return False
    
    def retrain_model(self, user_id: str) -> Dict:
        """ENHANCED: Retrain typing model with behavioral focus"""
        try:
            pool_path = f'{self.pool_dir}/{user_id}_pool.csv'
            
            if not os.path.exists(pool_path):
                return {'error': 'No typing training data found'}
            
            df_pool = pd.read_csv(pool_path)
            
            # ENHANCED: Use only highest quality typing samples
            quality_threshold = self.quality_score_threshold
            consistency_threshold = 0.5
            
            # Filter for high-quality, consistent typing
            high_quality_mask = (
                (df_pool.get('quality_score', 0.5) >= quality_threshold) &
                (df_pool.get('behavioral_consistency', 0.5) >= consistency_threshold)
            )
            
            if high_quality_mask.sum() >= self.min_samples_retrain:
                df_pool = df_pool[high_quality_mask]
                logger.info(f"Using {len(df_pool)} high-quality consistent typing samples")
            
            # Feature columns
            feature_cols = ['hold_mean', 'hold_std', 'flight_mean', 'flight_std', 
                          'backspace_rate', 'typing_speed']
            
            X = df_pool[feature_cols].values
            
            # Remove NaN values
            mask = ~np.isnan(X).any(axis=1)
            X = X[mask]
            
            if len(X) < self.min_samples_retrain:
                return {'error': f'Insufficient clean typing data: {len(X)} samples'}
            
            # Split for validation
            X_train, X_val = train_test_split(X, test_size=0.2, random_state=42)
            
            # Scale features (RobustScaler better for typing outliers)
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)
            
            # ENHANCED: Optimized for typing behavior
            model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=250,        # More trees for typing consistency
                max_samples=0.85,        # Use most typing data
                max_features=1.0,        # Use all typing features
                bootstrap=True,
                n_jobs=-1
            )
            model.fit(X_train_scaled)
            
            # Validate model
            train_predictions = model.predict(X_train_scaled)
            val_predictions = model.predict(X_val_scaled)
            
            train_outliers = np.sum(train_predictions == -1) / len(train_predictions)
            val_outliers = np.sum(val_predictions == -1) / len(val_predictions)
            
            # Calculate stability for typing
            train_scores = model.score_samples(X_train_scaled)
            val_scores = model.score_samples(X_val_scaled)
            score_stability = 1.0 - abs(np.mean(train_scores) - np.mean(val_scores))
            
            # ENHANCED: Stricter validation for typing (more predictable)
            valid_outlier_range = (0.01, 0.08)  # Very low outlier rate for typing
            stability_threshold = 0.4
            
            if (valid_outlier_range[0] <= train_outliers <= valid_outlier_range[1] and 
                score_stability > stability_threshold):
                
                # Save model
                model_path = f'{self.model_dir}/{user_id}_typing_model.pkl'
                scaler_path = f'{self.model_dir}/{user_id}_typing_scaler.pkl'
                
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                
                # Enhanced metadata for typing
                metadata = {
                    'user_id': user_id,
                    'retrain_date': datetime.now().isoformat(),
                    'training_samples': len(X_train),
                    'validation_samples': len(X_val),
                    'train_outlier_rate': round(train_outliers, 4),
                    'val_outlier_rate': round(val_outliers, 4),
                    'score_stability': round(score_stability, 4),
                    'total_pool_samples': len(df_pool),
                    'clean_samples_used': len(X),
                    'quality_threshold': quality_threshold,
                    'consistency_threshold': consistency_threshold,
                    'behavioral_metrics': {
                        'avg_quality': df_pool.get('quality_score', pd.Series([0.5])).mean(),
                        'avg_consistency': df_pool.get('behavioral_consistency', pd.Series([0.5])).mean(),
                        'avg_rhythm': df_pool.get('typing_rhythm', pd.Series([0.5])).mean()
                    }
                }
                
                metadata_path = f'{self.model_dir}/{user_id}_typing_retrain_metadata.json'
                with open(metadata_path, 'w') as f:
                    import json
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"✅ Enhanced typing model retrained for {user_id}")
                return {
                    'success': True,
                    'training_samples': len(X_train),
                    'validation_samples': len(X_val),
                    'train_outlier_rate': round(train_outliers, 4),
                    'val_outlier_rate': round(val_outliers, 4),
                    'score_stability': round(score_stability, 4),
                    'metadata': metadata
                }
            else:
                return {
                    'error': f'Typing model validation failed: outliers={train_outliers:.4f}, stability={score_stability:.4f}',
                    'details': {
                        'train_outliers': train_outliers,
                        'val_outliers': val_outliers,
                        'score_stability': score_stability,
                        'valid_range': valid_outlier_range
                    }
                }
                
        except Exception as e:
            logger.error(f"Error retraining typing model for {user_id}: {str(e)}")
            return {'error': f'Typing retraining failed: {str(e)}'}
    
    def update_model_if_appropriate(self, user_id: str, session_vector: List[float], 
                                  prediction_result: Dict) -> Dict:
        """
        ENHANCED: Main typing update method with behavioral validation
        """
        try:
            # ENHANCED: Check if typing session should be added
            if not self.should_add_to_pool(prediction_result):
                return {
                    'pool_updated': False,
                    'retrain_attempted': False,
                    'reason': 'Typing session quality/confidence insufficient',
                    'details': {
                        'risk_category': prediction_result.get('risk_category'),
                        'confidence': prediction_result.get('confidence'),
                        'anomaly_score': prediction_result.get('anomaly_score')
                    }
                }
            
            # Add typing session to pool
            success = self.add_session_to_pool(
                user_id, session_vector, prediction_result.get('risk_category', 'normal'), prediction_result
            )
            
            if not success:
                return {'error': 'Failed to add typing session to pool'}
            
            # Check if retraining is needed
            if self.should_retrain(user_id):
                retrain_result = self.retrain_model(user_id)
                return {
                    'pool_updated': True,
                    'retrain_attempted': True,
                    'retrain_result': retrain_result,
                    'reason': 'High-quality typing session added and retrain triggered'
                }
            
            return {
                'pool_updated': True,
                'retrain_attempted': False,
                'reason': 'High-quality typing session added to pool',
                'message': 'Typing session added to pool, retraining not needed yet'
            }
            
        except Exception as e:
            logger.error(f"Error updating typing model: {str(e)}")
            return {'error': f'Typing update failed: {str(e)}'}

    def get_typing_pool_statistics(self, user_id: str) -> Dict:
        """Get statistics about the typing training pool"""
        try:
            pool_path = f'{self.pool_dir}/{user_id}_pool.csv'
            
            if not os.path.exists(pool_path):
                return {'error': 'No typing pool data found'}
            
            df_pool = pd.read_csv(pool_path)
            
            # Calculate typing-specific statistics
            stats = {
                'total_samples': len(df_pool),
                'high_quality_samples': len(df_pool[df_pool.get('quality_score', 0.5) > self.quality_score_threshold]),
                'consistent_samples': len(df_pool[df_pool.get('behavioral_consistency', 0.5) > 0.5]),
                'recent_samples': len(df_pool[pd.to_datetime(df_pool['timestamp']) > datetime.now() - timedelta(days=7)]),
                'risk_distribution': df_pool['risk_category'].value_counts().to_dict(),
                'behavioral_metrics': {
                    'average_quality': df_pool.get('quality_score', pd.Series([0.5])).mean(),
                    'average_confidence': df_pool.get('confidence', pd.Series([0.5])).mean(),
                    'average_consistency': df_pool.get('behavioral_consistency', pd.Series([0.5])).mean(),
                    'average_rhythm': df_pool.get('typing_rhythm', pd.Series([0.5])).mean()
                },
                'typing_patterns': {
                    'avg_hold_time': df_pool['hold_mean'].mean(),
                    'avg_flight_time': df_pool['flight_mean'].mean(),
                    'avg_typing_speed': df_pool['typing_speed'].mean(),
                    'avg_backspace_rate': df_pool['backspace_rate'].mean()
                },
                'oldest_sample': df_pool['timestamp'].min(),
                'newest_sample': df_pool['timestamp'].max()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting typing pool statistics: {str(e)}")
            return {'error': f'Typing statistics calculation failed: {str(e)}'}


# Example usage and test function
if __name__ == '__main__':
    """Test the enhanced typing model updater"""
    
    print("Testing Enhanced Typing Model Updater")
    print("=" * 50)
    
    # Initialize components (these would be imported in real usage)
    # from predict_typing_risk import TypingRiskPredictor
    # predictor = TypingRiskPredictor()
    
    updater = TypingModelUpdater()
    
    # Example high-quality typing session
    test_vector = [145.0, 18.0, 185.0, 22.0, 0.06, 4.1]  # Good typing metrics
    user_id = 'enhanced_typing_user_123'
    
    # Simulate a high-quality prediction result
    prediction = {
        'risk_category': 'normal',
        'confidence': 0.85,
        'anomaly_score': -0.15,
        'user_id': user_id
    }
    
    print(f"\n1. Testing typing session quality...")
    is_quality = updater.validate_typing_session_quality(test_vector)
    print(f"   Session quality valid: {is_quality}")
    
    quality_score = updater.calculate_typing_quality(test_vector)
    print(f"   Quality score: {quality_score:.3f}")
    
    consistency_score = updater.calculate_behavioral_consistency(test_vector)
    print(f"   Behavioral consistency: {consistency_score:.3f}")
    
    print(f"\n2. Testing update decision...")
    should_add = updater.should_add_to_pool(prediction)
    print(f"   Should add to pool: {should_add}")
    
    if should_add:
        print(f"\n3. Testing pool update...")
        update_result = updater.update_model_if_appropriate(user_id, test_vector, prediction)
        print(f"   Update result: {update_result}")
        
        print(f"\n4. Getting pool statistics...")
        stats = updater.get_typing_pool_statistics(user_id)
        if 'error' not in stats:
            print(f"   Total samples: {stats['total_samples']}")
            print(f"   High quality: {stats['high_quality_samples']}")
            print(f"   Average quality: {stats['behavioral_metrics']['average_quality']:.3f}")
        else:
            print(f"   Statistics: {stats}")
    
    print(f"\n" + "=" * 50)