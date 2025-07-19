import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ImprovedDataPreprocessor:
    """
    Enhanced preprocessor that handles:
    1. Small data samples during onboarding (insufficient for mean/std)
    2. Real-time single-event processing
    3. Progressive data accumulation
    4. Robust feature extraction with fallbacks
    """
    
    def __init__(self):
        # Mapping from frontend variable names to standardized names
        self.swipe_field_mapping = {
            'swipeDistances': 'distances',
            'swipeDurations': 'durations', 
            'swipeSpeeds': 'speeds',
            'swipeDirections': 'directions',
            'swipeAccelerations': 'accelerations'
        }
        
        self.typing_field_mapping = {
            'holdTimes': 'hold_times',
            'HoldTimes': 'hold_times',
            'flightTimes': 'flight_times',
            'FlightTimes': 'flight_times',
            'backspaceRates': 'backspace_rates',
            'typingSpeeds': 'typing_speeds'
        }
        
        # Target feature columns for ML models
        self.swipe_features = [
            'speed_mean', 'speed_std', 'direction_mean', 
            'direction_std', 'acceleration_mean', 'acceleration_std'
        ]
        
        self.typing_features = [
            'hold_mean', 'hold_std', 'flight_mean', 'flight_std',
            'backspace_rate', 'typing_speed'
        ]
        
        # Minimum samples needed for reliable statistics
        self.min_samples_for_std = 3
        self.min_samples_for_training = {
            'swipe': 2,    # Very minimal for swipes
            'typing': 3    # Minimal for typing
        }
        
        # Default values when insufficient data
        self.defaults = {
            'swipe': {
                'speed_mean': 1.0, 'speed_std': 0.3,
                'direction_mean': 1.57, 'direction_std': 0.5,  # ~90 degrees
                'acceleration_mean': 500.0, 'acceleration_std': 150.0
            },
            'typing': {
                'hold_mean': 150.0, 'hold_std': 25.0,
                'flight_mean': 200.0, 'flight_std': 30.0,
                'backspace_rate': 0.1, 'typing_speed': 60.0
            }
        }
        
    def process_onboarding_data(self, user_id: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process onboarding data for model training (MISSING METHOD - ADD THIS)
        This method is called by the training utility
        """
        try:
            # Clean and standardize
            cleaned_data, warnings = self.validate_and_clean_data(raw_data)
            standardized_data = self.standardize_input_data(cleaned_data)
            
            # Assess data readiness
            readiness = self.assess_data_readiness(standardized_data)
            
            # Create training DataFrames if ready
            training_data = {}
            
            # Process swipe data
            if 'swiping' in readiness['modalities'] and readiness['modalities']['swiping']['readiness'] != 'insufficient':
                # Create multiple sessions from the data for training
                swipe_features_list = []
                
                # Extract all swipe data
                swipe_data = {k: v for k, v in standardized_data.items() 
                             if k in ['distances', 'durations', 'speeds', 'directions', 'accelerations']}
                
                if swipe_data:
                    # Determine number of sessions (swipes)
                    max_sessions = max([len(v) for v in swipe_data.values() if isinstance(v, list)], default=0)
                    
                    # Create features for each swipe session
                    for i in range(max_sessions):
                        session_data = {}
                        for field in ['speeds', 'directions', 'accelerations']:
                            if field in swipe_data and i < len(swipe_data[field]):
                                session_data[field] = [swipe_data[field][i]]  # Single swipe as list
                            else:
                                session_data[field] = [1.0] if field == 'speeds' else [1.57] if field == 'directions' else [500.0]
                        
                        session_features = self.extract_robust_swipe_features(session_data, is_realtime=False)
                        swipe_features_list.append(session_features)
                    
                    if swipe_features_list:
                        training_data['swiping'] = pd.DataFrame(swipe_features_list)
                        logger.info(f"Created swipe training DataFrame with {len(swipe_features_list)} sessions")
            
            # Process typing data  
                if 'typing' in readiness['modalities'] and readiness['modalities']['typing']['readiness'] != 'insufficient':
                    typing_features_list = []
                    
                    # Extract all typing data
                    typing_data = {k: v for k, v in standardized_data.items() 
                                if k in ['hold_times', 'flight_times', 'backspace_rates', 'typing_speeds']}
                    
                    if typing_data:
                        # Get the arrays
                        hold_times = typing_data.get('hold_times', [])
                        flight_times = typing_data.get('flight_times', [])
                        backspace_rates = typing_data.get('backspace_rates', [])
                        typing_speeds = typing_data.get('typing_speeds', [])
                        
                        # Find the minimum length to avoid index errors
                        min_length = min(
                            len(hold_times) if hold_times else 0,
                            len(flight_times) if flight_times else 0,
                            len(backspace_rates) if backspace_rates else 0,
                            len(typing_speeds) if typing_speeds else 0
                        )
                        
                        logger.info(f"Typing data lengths: hold={len(hold_times)}, flight={len(flight_times)}, backspace={len(backspace_rates)}, speed={len(typing_speeds)}")
                        logger.info(f"Using minimum length: {min_length}")
                        
                        # Create individual feature rows for each typing event
                        if min_length > 0:
                            for i in range(min_length):
                                # Create session data for each individual typing event
                                session_data = {
                                    'hold_times': [hold_times[i]] if i < len(hold_times) else [150.0],
                                    'flight_times': [flight_times[i]] if i < len(flight_times) else [200.0],
                                    'backspace_rates': [backspace_rates[i]] if i < len(backspace_rates) else [0.1],
                                    'typing_speeds': [typing_speeds[i]] if i < len(typing_speeds) else [60.0]
                                }
                                
                                # Extract features for this individual event
                                session_features = self.extract_robust_typing_features(session_data, is_realtime=False)
                                typing_features_list.append(session_features)
                            
                            if typing_features_list:
                                training_data['typing'] = pd.DataFrame(typing_features_list)
                                logger.info(f"Created typing training DataFrame with {len(typing_features_list)} individual samples")
            # Prepare result
            result = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'training_data': training_data,
                'readiness_assessment': readiness,
                'data_quality': {
                    'warnings': warnings,
                    'raw_data_fields': len(raw_data),
                    'standardized_fields': len(standardized_data),
                    'processing_mode': readiness['processing_mode']
                }
            }
            
            if not training_data:
                result['error'] = 'Insufficient data for training any models'
            
            logger.info(f"Processed onboarding data for user {user_id}: {len(training_data)} modalities ready")
            return result
            
        except Exception as e:
            logger.error(f"Error processing onboarding data for user {user_id}: {str(e)}")
            return {
                'user_id': user_id,
                'error': f'Onboarding processing failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    # Add these methods to your existing ImprovedDataPreprocessor class in ML/preprocessing/improved_data_preprocessor.py

    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a prediction request (wrapper for process_for_realtime_prediction)
        
        Args:
            request_data: Dictionary containing 'user_id' and 'data'
        
        Returns:
            Processed features ready for prediction
        """
        try:
            user_id = request_data.get('user_id')
            data = request_data.get('data', {})
            
            if not user_id:
                return {
                    'error': 'Missing user_id in request',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Use existing realtime prediction processing
            return self.process_for_realtime_prediction(user_id, data)
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                'error': f'Request processing failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def enable_performance_mode(self):
        """Enable performance mode for faster processing"""
        # Store original settings
        if not hasattr(self, '_original_settings'):
            self._original_settings = {
                'min_samples_for_std': self.min_samples_for_std,
                'min_samples_for_training': self.min_samples_for_training.copy()
            }
        
        # Set performance mode settings (less validation, faster processing)
        self.min_samples_for_std = 1  # Accept single samples
        self.min_samples_for_training = {'swipe': 1, 'typing': 1}  # Very minimal requirements
        self.performance_mode = True
        
        logger.info("Performance mode enabled for faster processing")
    
    def disable_performance_mode(self):
        """Disable performance mode and restore original settings"""
        if hasattr(self, '_original_settings'):
            self.min_samples_for_std = self._original_settings['min_samples_for_std']
            self.min_samples_for_training = self._original_settings['min_samples_for_training']
            self.performance_mode = False
            logger.info("Performance mode disabled, restored original settings")
    
    def process_lightweight(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lightweight processing for maximum speed
        
        Args:
            request_data: Dictionary containing 'user_id' and 'data'
        
        Returns:
            Processed features with minimal validation
        """
        try:
            user_id = request_data.get('user_id')
            data = request_data.get('data', {})
            
            if not user_id:
                return {
                    'error': 'Missing user_id in request',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Enable performance mode temporarily
            original_mode = getattr(self, 'performance_mode', False)
            if not original_mode:
                self.enable_performance_mode()
            
            try:
                # Quick data standardization (minimal validation)
                standardized_data = self.standardize_input_data(data)
                
                # Extract features with minimal processing
                features = {}
                
                # Quick swipe feature extraction
                swipe_data = {k: v for k, v in standardized_data.items() 
                             if k in ['distances', 'durations', 'speeds', 'directions', 'accelerations']}
                
                if swipe_data and any(len(v) > 0 if isinstance(v, list) else v for v in swipe_data.values()):
                    swipe_features = self.extract_robust_swipe_features(swipe_data, is_realtime=True)
                    features['swiping'] = [swipe_features[f] for f in self.swipe_features]
                
                # Quick typing feature extraction
                typing_data = {k: v for k, v in standardized_data.items() 
                              if k in ['hold_times', 'flight_times', 'backspace_rates', 'typing_speeds']}
                
                if typing_data and any(len(v) > 0 if isinstance(v, list) else v for v in typing_data.values()):
                    typing_features = self.extract_robust_typing_features(typing_data, is_realtime=True)
                    features['typing'] = [typing_features[f] for f in self.typing_features]
                
                result = {
                    'user_id': str(user_id),
                    'timestamp': datetime.now().isoformat(),
                    'features': features,
                    'mode': 'lightweight'
                }
                
                if not features:
                    result['error'] = 'No valid features extracted'
                
                return result
                
            finally:
                # Restore original mode if it was disabled
                if not original_mode:
                    self.disable_performance_mode()
            
        except Exception as e:
            logger.error(f"Error in lightweight processing for user {user_id}: {str(e)}")
            return {
                'user_id': str(user_id),
                'error': f'Lightweight processing failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def batch_process_features(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple requests efficiently
        
        Args:
            requests: List of request dictionaries
        
        Returns:
            List of processed results
        """
        try:
            # Enable performance mode for batch processing
            original_mode = getattr(self, 'performance_mode', False)
            if not original_mode:
                self.enable_performance_mode()
            
            results = []
            
            try:
                for request in requests:
                    result = self.process_lightweight(request)
                    results.append(result)
                
                return results
                
            finally:
                # Restore original mode
                if not original_mode:
                    self.disable_performance_mode()
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            return [{'error': f'Batch processing failed: {str(e)}'}]
    
    def quick_feature_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quick check to see what features can be extracted from data
        
        Args:
            data: Raw input data
        
        Returns:
            Dictionary with availability information
        """
        try:
            standardized_data = self.standardize_input_data(data)
            
            # Check swipe data availability
            swipe_data = {k: v for k, v in standardized_data.items() 
                         if k in ['distances', 'durations', 'speeds', 'directions', 'accelerations']}
            swipe_available = any(len(v) > 0 if isinstance(v, list) else v for v in swipe_data.values())
            swipe_sample_count = max([len(v) for v in swipe_data.values() if isinstance(v, list)], default=0)
            
            # Check typing data availability
            typing_data = {k: v for k, v in standardized_data.items() 
                          if k in ['hold_times', 'flight_times', 'backspace_rates', 'typing_speeds']}
            typing_available = any(len(v) > 0 if isinstance(v, list) else v for v in typing_data.values())
            typing_sample_count = max([len(v) for v in typing_data.values() if isinstance(v, list)], default=0)
            
            return {
                'swiping': {
                    'available': swipe_available,
                    'sample_count': swipe_sample_count,
                    'fields': list(swipe_data.keys()) if swipe_available else []
                },
                'typing': {
                    'available': typing_available,
                    'sample_count': typing_sample_count,
                    'fields': list(typing_data.keys()) if typing_available else []
                },
                'total_modalities': sum([swipe_available, typing_available]),
                'prediction_ready': swipe_available or typing_available
            }
            
        except Exception as e:
            logger.error(f"Error in quick feature check: {str(e)}")
            return {
                'error': f'Feature check failed: {str(e)}',
                'prediction_ready': False
            }
    def standardize_input_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize input data format with better error handling"""
        standardized = {}
        
        for key, value in data.items():
            # Remove 'New' suffix if present
            clean_key = key.replace('New', '') if key.endswith('New') else key
            
            # Map to standardized names
            if clean_key in self.swipe_field_mapping:
                std_key = self.swipe_field_mapping[clean_key]
                # Ensure it's a list, handle single values
                if isinstance(value, (int, float)):
                    standardized[std_key] = [float(value)]
                elif isinstance(value, list):
                    standardized[std_key] = [float(v) for v in value if isinstance(v, (int, float))]
                else:
                    standardized[std_key] = []
            elif clean_key in self.typing_field_mapping:
                std_key = self.typing_field_mapping[clean_key]
                # Handle different data types
                if isinstance(value, (int, float)):
                    standardized[std_key] = [float(value)]
                elif isinstance(value, list):
                    # Handle nested lists (like flight_times)
                    if value and isinstance(value[0], list):
                        flat_list = [float(item) for sublist in value for item in sublist 
                                   if isinstance(item, (int, float))]
                        standardized[std_key] = flat_list
                    else:
                        standardized[std_key] = [float(v) for v in value if isinstance(v, (int, float))]
                else:
                    standardized[std_key] = []
            else:
                standardized[clean_key] = value
        
        return standardized
    def extract_enhanced_swipe_features(self, swipe_data: Dict[str, List[float]], 
                                  is_realtime: bool = False) -> Dict[str, float]:
        """
        Extract enhanced swipe features from existing frontend data
        NO new sensors needed - all calculated from speeds, directions, accelerations
        """
        try:
            speeds = np.array(swipe_data.get('speeds', []))
            directions = np.array(swipe_data.get('directions', []))
            accelerations = np.array(swipe_data.get('accelerations', []))
            
            if len(speeds) == 0:
                return self._get_default_enhanced_swipe_features()
            
            # Convert directions to radians if needed
            if len(directions) > 0 and directions.max() > 2 * np.pi:
                directions = np.radians(directions)
            
            features = {}
            
            # ORIGINAL 6 features (keep these)
            features['speed_mean'] = float(np.mean(speeds))
            features['speed_std'] = float(np.std(speeds)) if len(speeds) > 1 else 0.1
            features['direction_mean'] = float(np.mean(directions)) if len(directions) > 0 else 1.57
            features['direction_std'] = float(np.std(directions)) if len(directions) > 1 else 0.5
            features['acceleration_mean'] = float(np.mean(accelerations)) if len(accelerations) > 0 else 500.0
            features['acceleration_std'] = float(np.std(accelerations)) if len(accelerations) > 1 else 150.0
            
            # NEW ENHANCED features (calculated from existing data)
            features['speed_trend'] = self.calculate_trend(speeds)
            features['direction_consistency'] = self.calculate_direction_consistency(directions)
            features['acceleration_smoothness'] = self.calculate_smoothness(accelerations)
            features['gesture_complexity'] = self.calculate_gesture_complexity(speeds, directions)
            features['speed_variability'] = float(np.var(speeds)) if len(speeds) > 1 else 0.1
            features['pressure_estimate'] = self.estimate_pressure_from_motion(speeds, accelerations)
            
            # Additional behavioral features from existing data
            features['velocity_entropy'] = self.calculate_entropy(speeds)
            features['direction_entropy'] = self.calculate_entropy(directions) if len(directions) > 0 else 0.5
            features['motion_jerk'] = self.calculate_jerk(accelerations)
            features['gesture_duration'] = self.estimate_gesture_duration(speeds)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting enhanced swipe features: {str(e)}")
            return self._get_default_enhanced_swipe_features()

    def extract_enhanced_typing_features(self, typing_data: Dict[str, List[float]], 
                                    is_realtime: bool = False) -> Dict[str, float]:
        """
        Extract enhanced typing features from existing frontend data
        NO new sensors needed - all calculated from hold_times, flight_times, etc.
        """
        try:
            hold_times = np.array(typing_data.get('hold_times', []))
            flight_times = np.array(typing_data.get('flight_times', []))
            backspace_rates = np.array(typing_data.get('backspace_rates', []))
            typing_speeds = np.array(typing_data.get('typing_speeds', []))
            
            if len(hold_times) == 0:
                return self._get_default_enhanced_typing_features()
            
            features = {}
            
            # ORIGINAL 6 features (keep these)
            features['hold_mean'] = float(np.mean(hold_times))
            features['hold_std'] = float(np.std(hold_times)) if len(hold_times) > 1 else 10.0
            features['flight_mean'] = float(np.mean(flight_times)) if len(flight_times) > 0 else 200.0
            features['flight_std'] = float(np.std(flight_times)) if len(flight_times) > 1 else 15.0
            features['backspace_rate'] = float(np.mean(backspace_rates)) if len(backspace_rates) > 0 else 0.1
            features['typing_speed'] = float(np.mean(typing_speeds)) if len(typing_speeds) > 0 else 3.5
            
            # NEW ENHANCED features (calculated from existing data)
            features['rhythm_consistency'] = self.calculate_typing_rhythm(hold_times, flight_times)
            features['keystroke_dynamics'] = self.calculate_keystroke_dynamics(hold_times, flight_times)
            features['pressure_variance'] = float(np.var(hold_times)) if len(hold_times) > 1 else 100.0
            features['typing_flow'] = self.calculate_typing_flow(flight_times)
            
            # Additional behavioral features from existing timing data
            features['hold_flight_ratio'] = self.calculate_hold_flight_ratio(hold_times, flight_times)
            features['typing_entropy'] = self.calculate_entropy(hold_times)
            features['speed_consistency'] = self.calculate_speed_consistency(typing_speeds)
            features['backspace_pattern'] = self.analyze_backspace_pattern(backspace_rates)
            features['timing_complexity'] = self.calculate_timing_complexity(hold_times, flight_times)
            features['keystroke_pressure'] = self.estimate_keystroke_pressure(hold_times)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting enhanced typing features: {str(e)}")
            return self._get_default_enhanced_typing_features()
    def calculate_trend(self, values: np.ndarray) -> float:
        """Calculate trend in time series (slope of linear fit)"""
        if len(values) < 3:
            return 0.0
        try:
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            return float(slope)
        except:
            return 0.0

    def calculate_direction_consistency(self, directions: np.ndarray) -> float:
        """Calculate how consistent direction changes are"""
        if len(directions) < 3:
            return 0.5
        try:
            # Calculate direction changes
            direction_changes = np.diff(directions)
            # Normalize to -π to π
            direction_changes = np.arctan2(np.sin(direction_changes), np.cos(direction_changes))
            # Consistency = 1 / (1 + variance of changes)
            consistency = 1.0 / (1.0 + np.var(direction_changes))
            return float(min(1.0, consistency))
        except:
            return 0.5

    def calculate_smoothness(self, values: np.ndarray) -> float:
        """Calculate smoothness (inverse of jerk/sudden changes)"""
        if len(values) < 3:
            return 0.5
        try:
            # Calculate second derivative (jerk)
            jerk = np.diff(values, n=2)
            jerk_variance = np.var(jerk) if len(jerk) > 0 else 0
            smoothness = 1.0 / (1.0 + jerk_variance / 100.0)  # Normalize
            return float(min(1.0, smoothness))
        except:
            return 0.5

    def calculate_gesture_complexity(self, speeds: np.ndarray, directions: np.ndarray) -> float:
        """Calculate gesture complexity from speed and direction patterns"""
        if len(speeds) < 3 or len(directions) < 3:
            return 0.5
        try:
            # Speed complexity
            speed_changes = np.sum(np.abs(np.diff(speeds)) > np.std(speeds) / 2)
            
            # Direction complexity  
            direction_changes = np.sum(np.abs(np.diff(directions)) > np.pi/6)  # >30 degree changes
            
            # Normalize by gesture length
            total_points = min(len(speeds), len(directions)) - 1
            if total_points <= 0:
                return 0.5
                
            complexity = (speed_changes + direction_changes) / (2 * total_points)
            return float(min(1.0, complexity))
        except:
            return 0.5

    def estimate_pressure_from_motion(self, speeds: np.ndarray, accelerations: np.ndarray) -> float:
        """Estimate pressure from motion patterns (higher acceleration = more pressure)"""
        if len(accelerations) == 0:
            return 0.5
        try:
            # Higher accelerations suggest more forceful gestures
            pressure_proxy = np.mean(accelerations) / 1000.0  # Normalize
            return float(min(1.0, max(0.0, pressure_proxy)))
        except:
            return 0.5

    def calculate_entropy(self, values: np.ndarray) -> float:
        """Calculate entropy (randomness) of values"""
        if len(values) < 3:
            return 0.5
        try:
            # Discretize values into bins
            hist, _ = np.histogram(values, bins=min(10, len(values)//2))
            hist = hist[hist > 0]  # Remove empty bins
            prob = hist / np.sum(hist)
            entropy = -np.sum(prob * np.log2(prob + 1e-10))
            # Normalize to 0-1
            max_entropy = np.log2(len(prob))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            return float(min(1.0, normalized_entropy))
        except:
            return 0.5

    def calculate_jerk(self, accelerations: np.ndarray) -> float:
        """Calculate jerk (rate of change of acceleration)"""
        if len(accelerations) < 3:
            return 0.5
        try:
            jerk = np.diff(accelerations, n=2)
            jerk_magnitude = np.mean(np.abs(jerk)) if len(jerk) > 0 else 0
            # Normalize
            normalized_jerk = min(1.0, jerk_magnitude / 1000.0)
            return float(normalized_jerk)
        except:
            return 0.5

    def estimate_gesture_duration(self, speeds: np.ndarray) -> float:
        """Estimate gesture duration from speed patterns"""
        if len(speeds) < 2:
            return 0.5
        try:
            # Find start and end of gesture (when speed > threshold)
            threshold = np.mean(speeds) * 0.3
            active_points = np.sum(speeds > threshold)
            duration_proxy = active_points / len(speeds)
            return float(min(1.0, duration_proxy))
        except:
            return 0.5

    def calculate_typing_rhythm(self, hold_times: np.ndarray, flight_times: np.ndarray) -> float:
        """Calculate typing rhythm consistency"""
        if len(hold_times) < 3 or len(flight_times) < 3:
            return 0.5
        try:
            # Combine hold and flight times to create rhythm pattern
            min_len = min(len(hold_times), len(flight_times))
            rhythm_pattern = []
            for i in range(min_len):
                rhythm_pattern.append(hold_times[i])
                if i < len(flight_times):
                    rhythm_pattern.append(flight_times[i])
            
            # Calculate rhythm consistency (low variance = high consistency)
            rhythm_variance = np.var(rhythm_pattern)
            consistency = 1.0 / (1.0 + rhythm_variance / 1000.0)
            return float(min(1.0, consistency))
        except:
            return 0.5

    def calculate_keystroke_dynamics(self, hold_times: np.ndarray, flight_times: np.ndarray) -> float:
        """Calculate keystroke dynamics pattern"""
        if len(hold_times) < 2 or len(flight_times) < 2:
            return 0.5
        try:
            # Calculate hold-to-flight ratios
            min_len = min(len(hold_times), len(flight_times))
            ratios = []
            for i in range(min_len):
                if flight_times[i] > 0:
                    ratios.append(hold_times[i] / flight_times[i])
            
            if len(ratios) < 2:
                return 0.5
                
            # Consistency of ratios indicates typing dynamics
            ratio_consistency = 1.0 / (1.0 + np.var(ratios))
            return float(min(1.0, ratio_consistency))
        except:
            return 0.5

    def calculate_typing_flow(self, flight_times: np.ndarray) -> float:
        """Calculate typing flow (smoothness of transitions)"""
        if len(flight_times) < 3:
            return 0.5
        try:
            # Calculate flow as inverse of flight time variance
            flow = 1.0 / (1.0 + np.var(flight_times) / 1000.0)
            return float(min(1.0, flow))
        except:
            return 0.5

    def calculate_hold_flight_ratio(self, hold_times: np.ndarray, flight_times: np.ndarray) -> float:
        """Calculate average hold-to-flight time ratio"""
        if len(hold_times) == 0 or len(flight_times) == 0:
            return 0.75  # Default ratio
        try:
            avg_hold = np.mean(hold_times)
            avg_flight = np.mean(flight_times)
            ratio = avg_hold / (avg_flight + 1e-6)  # Avoid division by zero
            # Normalize to reasonable range
            normalized_ratio = min(2.0, max(0.1, ratio)) / 2.0
            return float(normalized_ratio)
        except:
            return 0.75

    def calculate_speed_consistency(self, typing_speeds: np.ndarray) -> float:
        """Calculate consistency of typing speed"""
        if len(typing_speeds) < 2:
            return 0.5
        try:
            speed_variance = np.var(typing_speeds)
            consistency = 1.0 / (1.0 + speed_variance)
            return float(min(1.0, consistency))
        except:
            return 0.5

    def analyze_backspace_pattern(self, backspace_rates: np.ndarray) -> float:
        """Analyze backspace usage pattern"""
        if len(backspace_rates) == 0:
            return 0.1  # Default low backspace pattern
        try:
            avg_backspace = np.mean(backspace_rates)
            backspace_consistency = 1.0 / (1.0 + np.var(backspace_rates) + 1e-6)
            # Combine rate and consistency
            pattern_score = (1.0 - avg_backspace) * 0.7 + backspace_consistency * 0.3
            return float(min(1.0, max(0.0, pattern_score)))
        except:
            return 0.1

    def calculate_timing_complexity(self, hold_times: np.ndarray, flight_times: np.ndarray) -> float:
        """Calculate complexity of timing patterns"""
        if len(hold_times) < 3 or len(flight_times) < 3:
            return 0.5
        try:
            # Combine timing data
            all_times = np.concatenate([hold_times, flight_times])
            
            # Calculate complexity as entropy
            complexity = self.calculate_entropy(all_times)
            return float(complexity)
        except:
            return 0.5

    def estimate_keystroke_pressure(self, hold_times: np.ndarray) -> float:
        """Estimate keystroke pressure from hold times"""
        if len(hold_times) == 0:
            return 0.5
        try:
            # Longer hold times might indicate more pressure
            avg_hold = np.mean(hold_times)
            # Normalize to 0-1 range (assuming 50-300ms normal range)
            pressure_estimate = (avg_hold - 50) / 250.0
            return float(min(1.0, max(0.0, pressure_estimate)))
        except:
            return 0.5

    def _get_default_enhanced_swipe_features(self) -> Dict[str, float]:
        """Default enhanced swipe features"""
        return {
            # Original 6
            'speed_mean': 1.0, 'speed_std': 0.3, 'direction_mean': 1.57, 
            'direction_std': 0.5, 'acceleration_mean': 500.0, 'acceleration_std': 150.0,
            # Enhanced 10  
            'speed_trend': 0.0, 'direction_consistency': 0.5, 'acceleration_smoothness': 0.5,
            'gesture_complexity': 0.5, 'speed_variability': 0.1, 'pressure_estimate': 0.5,
            'velocity_entropy': 0.5, 'direction_entropy': 0.5, 'motion_jerk': 0.5, 'gesture_duration': 0.5
        }

    def _get_default_enhanced_typing_features(self) -> Dict[str, float]:
        """Default enhanced typing features"""
        return {
            # Original 6
            'hold_mean': 150.0, 'hold_std': 25.0, 'flight_mean': 200.0, 
            'flight_std': 30.0, 'backspace_rate': 0.1, 'typing_speed': 3.5,
            # Enhanced 10
            'rhythm_consistency': 0.5, 'keystroke_dynamics': 0.5, 'pressure_variance': 100.0,
            'typing_flow': 0.5, 'hold_flight_ratio': 0.75, 'typing_entropy': 0.5,
            'speed_consistency': 0.5, 'backspace_pattern': 0.1, 'timing_complexity': 0.5, 'keystroke_pressure': 0.5
        }
    def extract_robust_swipe_features(self, swipe_data: Dict[str, List[float]], 
                                    is_realtime: bool = False) -> Dict[str, float]:
        """
        Extract swipe features with robust handling of insufficient data
        
        Args:
            swipe_data: Dictionary with swipe data
            is_realtime: True if this is a single real-time event
        
        Returns:
            Dictionary with statistical features
        """
        try:
            # Handle real-time single event
            if is_realtime:
                return self._extract_realtime_swipe_features(swipe_data)
            
            # Get required data
            speeds = np.array(swipe_data.get('speeds', []))
            directions = np.array(swipe_data.get('directions', []))
            accelerations = np.array(swipe_data.get('accelerations', []))
            
            # Check if we have any data
            if len(speeds) == 0 and len(directions) == 0 and len(accelerations) == 0:
                logger.warning("No swipe data available, using defaults")
                return self.defaults['swipe'].copy()
            
            # Convert directions from degrees to radians if needed
            if len(directions) > 0 and directions.max() > 2 * np.pi:
                directions = np.radians(directions)
            
            features = {}
            
            # Speed features
            if len(speeds) >= 1:
                features['speed_mean'] = float(np.mean(speeds))
                if len(speeds) >= self.min_samples_for_std:
                    features['speed_std'] = float(np.std(speeds))
                else:
                    # Use reasonable default based on mean
                    features['speed_std'] = max(0.1, features['speed_mean'] * 0.2)
            else:
                features['speed_mean'] = self.defaults['swipe']['speed_mean']
                features['speed_std'] = self.defaults['swipe']['speed_std']
            
            # Direction features
            if len(directions) >= 1:
                features['direction_mean'] = float(np.mean(directions))
                if len(directions) >= self.min_samples_for_std:
                    features['direction_std'] = float(np.std(directions))
                else:
                    # Default std for directions (about 30 degrees in radians)
                    features['direction_std'] = 0.5
            else:
                features['direction_mean'] = self.defaults['swipe']['direction_mean']
                features['direction_std'] = self.defaults['swipe']['direction_std']
            
            # Acceleration features
            if len(accelerations) >= 1:
                features['acceleration_mean'] = float(np.mean(accelerations))
                if len(accelerations) >= self.min_samples_for_std:
                    features['acceleration_std'] = float(np.std(accelerations))
                else:
                    # Use reasonable default based on mean
                    features['acceleration_std'] = max(50.0, features['acceleration_mean'] * 0.3)
            else:
                features['acceleration_mean'] = self.defaults['swipe']['acceleration_mean']
                features['acceleration_std'] = self.defaults['swipe']['acceleration_std']
            
            # Validate features
            for key, value in features.items():
                if np.isnan(value) or np.isinf(value):
                    features[key] = self.defaults['swipe'][key]
                    logger.warning(f"Invalid swipe feature {key}, using default")
            
            logger.debug(f"Extracted swipe features from {len(speeds)} speed, {len(directions)} direction, {len(accelerations)} acceleration samples")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting swipe features: {str(e)}")
            return self.defaults['swipe'].copy()

    def _extract_realtime_swipe_features(self, swipe_data: Dict[str, List[float]]) -> Dict[str, float]:
        """Extract features from a single real-time swipe event"""
        # For real-time, we get single values, so we use them directly with sensible defaults for std
        features = self.defaults['swipe'].copy()
        
        if 'speeds' in swipe_data and swipe_data['speeds']:
            features['speed_mean'] = float(swipe_data['speeds'][-1])  # Latest value
            features['speed_std'] = features['speed_mean'] * 0.2  # 20% of mean as std
        
        if 'directions' in swipe_data and swipe_data['directions']:
            direction = float(swipe_data['directions'][-1])
            if direction > 2 * np.pi:
                direction = np.radians(direction)
            features['direction_mean'] = direction
            features['direction_std'] = 0.5  # ~30 degrees
        
        if 'accelerations' in swipe_data and swipe_data['accelerations']:
            features['acceleration_mean'] = float(swipe_data['accelerations'][-1])
            features['acceleration_std'] = features['acceleration_mean'] * 0.3
        
        return features

    def extract_robust_typing_features(self, typing_data: Dict[str, List[float]], is_realtime: bool = False) -> Dict[str, float]:
        """
        Extract typing features - UPDATED for new data format
        - typingSpeeds now contains characters per second values
        - backspaceRates now contains per-keystroke rates
        
        Args:
            typing_data: Dictionary with typing data
            is_realtime: True if this is a single real-time event
        
        Returns:
            Dictionary with statistical features
        """
        try:
            # Handle real-time single event
            if is_realtime:
                return self._extract_realtime_typing_features(typing_data)
            
            # Get data arrays
            hold_times = np.array(typing_data.get('hold_times', []))
            flight_times = np.array(typing_data.get('flight_times', []))
            backspace_rates = np.array(typing_data.get('backspace_rates', []))
            typing_speeds = np.array(typing_data.get('typing_speeds', []))
            
            # Check if we have any data
            if (len(hold_times) == 0 and len(flight_times) == 0 and 
                len(backspace_rates) == 0 and len(typing_speeds) == 0):
                logger.warning("No typing data available, using defaults")
                return self.defaults['typing'].copy()
            
            features = {}
            
            # Hold time features (unchanged)
            if len(hold_times) >= 1:
                features['hold_mean'] = float(np.mean(hold_times))
                if len(hold_times) >= self.min_samples_for_std:
                    features['hold_std'] = float(np.std(hold_times))
                else:
                    features['hold_std'] = max(10.0, features['hold_mean'] * 0.15)
            else:
                features['hold_mean'] = self.defaults['typing']['hold_mean']
                features['hold_std'] = self.defaults['typing']['hold_std']
            
            # Flight time features (unchanged)
            if len(flight_times) >= 1:
                features['flight_mean'] = float(np.mean(flight_times))
                if len(flight_times) >= self.min_samples_for_std:
                    features['flight_std'] = float(np.std(flight_times))
                else:
                    features['flight_std'] = max(15.0, features['flight_mean'] * 0.15)
            else:
                features['flight_mean'] = self.defaults['typing']['flight_mean']
                features['flight_std'] = self.defaults['typing']['flight_std']
            
            # UPDATED: Backspace rate - now average of per-keystroke rates
            if len(backspace_rates) >= 1:
                # Since we now get per-keystroke rates, take the mean
                features['backspace_rate'] = float(np.mean(backspace_rates))
            else:
                features['backspace_rate'] = self.defaults['typing']['backspace_rate']
            
            # UPDATED: Typing speed - now characters per second, take mean
            if len(typing_speeds) >= 1:
                # Since we now get per-keystroke speeds in chars/sec, take the mean
                features['typing_speed'] = float(np.mean(typing_speeds))
            else:
                features['typing_speed'] = self.defaults['typing']['typing_speed']
            
            # Validate features
            for key, value in features.items():
                if np.isnan(value) or np.isinf(value):
                    features[key] = self.defaults['typing'][key]
                    logger.warning(f"Invalid typing feature {key}, using default")
            
            # UPDATED: Additional validation for new ranges
            features['backspace_rate'] = max(0.0, min(1.0, features['backspace_rate']))
            features['typing_speed'] = max(0.5, min(15.0, features['typing_speed']))  # chars/sec range
            
            logger.debug(f"Extracted typing features: hold={len(hold_times)}, flight={len(flight_times)}, "
                        f"backspace={len(backspace_rates)}, speed={len(typing_speeds)} samples")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting typing features: {str(e)}")
            return self.defaults['typing'].copy()

    def _extract_realtime_typing_features(self, typing_data: Dict[str, List[float]]) -> Dict[str, float]:
        """Extract features from a single real-time typing event - UPDATED"""
        features = self.defaults['typing'].copy()
        
        if 'hold_times' in typing_data and typing_data['hold_times']:
            features['hold_mean'] = float(typing_data['hold_times'][-1])
            features['hold_std'] = features['hold_mean'] * 0.15
        
        if 'flight_times' in typing_data and typing_data['flight_times']:
            features['flight_mean'] = float(typing_data['flight_times'][-1])
            features['flight_std'] = features['flight_mean'] * 0.15
        
        # UPDATED: Handle new backspace rate format (per-keystroke)
        if 'backspace_rates' in typing_data and typing_data['backspace_rates']:
            features['backspace_rate'] = float(typing_data['backspace_rates'][-1])
        
        # UPDATED: Handle new typing speed format (chars/sec)
        if 'typing_speeds' in typing_data and typing_data['typing_speeds']:
            features['typing_speed'] = float(typing_data['typing_speeds'][-1])
        
        return features


    def assess_data_readiness(self, standardized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess if data is ready for training and what type of processing is needed
        
        Returns:
            Dictionary with readiness assessment and recommendations
        """
        assessment = {
            'overall_readiness': 'insufficient',
            'modalities': {},
            'recommendations': [],
            'processing_mode': 'onboarding'  # onboarding, realtime, or full_training
        }
        
        # Assess swipe data
        swipe_data = {k: v for k, v in standardized_data.items() 
                     if k in ['distances', 'durations', 'speeds', 'directions', 'accelerations']}
        
        if swipe_data:
            total_swipe_samples = max([len(v) for v in swipe_data.values() if isinstance(v, list)], default=0)
            
            swipe_assessment = {
                'available': True,
                'sample_count': total_swipe_samples,
                'readiness': 'insufficient',
                'quality': 'poor'
            }
            
            if total_swipe_samples >= self.min_samples_for_training['swipe']:
                swipe_assessment['readiness'] = 'minimal'
                swipe_assessment['quality'] = 'acceptable'
                
                if total_swipe_samples >= 15:
                    swipe_assessment['readiness'] = 'good'
                    swipe_assessment['quality'] = 'good'
                elif total_swipe_samples >= 25:
                    swipe_assessment['readiness'] = 'excellent'
                    swipe_assessment['quality'] = 'excellent'
            
            assessment['modalities']['swiping'] = swipe_assessment
        
        # Assess typing data
        typing_data = {k: v for k, v in standardized_data.items() 
                      if k in ['hold_times', 'flight_times', 'backspace_rates', 'typing_speeds']}
        
        if typing_data:
            # Count total typing events
            total_typing_samples = 0
            for key, values in typing_data.items():
                if isinstance(values, list):
                    if key in ['hold_times', 'flight_times']:
                        total_typing_samples = max(total_typing_samples, len(values))
            
            typing_assessment = {
                'available': True,
                'sample_count': total_typing_samples,
                'readiness': 'insufficient',
                'quality': 'poor'
            }
            
            if total_typing_samples >= self.min_samples_for_training['typing']:
                typing_assessment['readiness'] = 'minimal'
                typing_assessment['quality'] = 'acceptable'
                
                if total_typing_samples >= 20:
                    typing_assessment['readiness'] = 'good'
                    typing_assessment['quality'] = 'good'
                elif total_typing_samples >= 40:
                    typing_assessment['readiness'] = 'excellent'
                    typing_assessment['quality'] = 'excellent'
            
            assessment['modalities']['typing'] = typing_assessment
        
        # Overall assessment
        ready_modalities = [mod for mod, data in assessment['modalities'].items() 
                          if data['readiness'] in ['minimal', 'good', 'excellent']]
        
        if ready_modalities:
            assessment['overall_readiness'] = 'ready'
            
            # Determine processing mode
            total_samples = sum([data['sample_count'] for data in assessment['modalities'].values()])
            if total_samples >= 50:
                assessment['processing_mode'] = 'full_training'
            elif total_samples >= 15:
                assessment['processing_mode'] = 'onboarding'
            else:
                assessment['processing_mode'] = 'minimal_onboarding'
        
        # Generate recommendations
        if not ready_modalities:
            assessment['recommendations'].append("Continue data collection - insufficient samples for any behavioral models")
        elif len(ready_modalities) == 1:
            assessment['recommendations'].append(f"Single modality ({ready_modalities[0]}) ready - consider collecting more data for multi-modal authentication")
        else:
            assessment['recommendations'].append("Multiple modalities ready for training")
        
        # Specific recommendations
        for modality, data in assessment['modalities'].items():
            if data['readiness'] == 'insufficient':
                
                assessment['recommendations'].append(f"Need more {modality} samples for training")
            elif data['quality'] == 'acceptable':
                assessment['recommendations'].append(f"Consider collecting more {modality} data for improved accuracy")
        
        return assessment

    def process_for_training(self, user_id: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data for model training with comprehensive readiness assessment
        """
        try:
            # Clean and standardize
            cleaned_data, warnings = self.validate_and_clean_data(raw_data)
            standardized_data = self.standardize_input_data(cleaned_data)
            
            # Assess data readiness
            readiness = self.assess_data_readiness(standardized_data)
            
            # Create training data if ready
            training_data = {}
            
            if 'swiping' in readiness['modalities'] and readiness['modalities']['swiping']['readiness'] != 'insufficient':
                swipe_features = self.extract_robust_swipe_features(standardized_data, is_realtime=False)
                training_data['swiping'] = pd.DataFrame([swipe_features])
                logger.info(f"Created swipe training data with {readiness['modalities']['swiping']['sample_count']} samples")
            
            if 'typing' in readiness['modalities'] and readiness['modalities']['typing']['readiness'] != 'insufficient':
                typing_features = self.extract_robust_typing_features(standardized_data, is_realtime=False)
                training_data['typing'] = pd.DataFrame([typing_features])
                logger.info(f"Created typing training data with {readiness['modalities']['typing']['sample_count']} samples")
            
            result = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'training_data': training_data,
                'readiness_assessment': readiness,
                'data_quality': {
                    'warnings': warnings,
                    'raw_data_fields': len(raw_data),
                    'standardized_fields': len(standardized_data),
                    'processing_mode': readiness['processing_mode']
                }
            }
            
            if not training_data:
                result['error'] = 'Insufficient data for training any models'
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing training data for user {user_id}: {str(e)}")
            return {
                'user_id': user_id,
                'error': f'Processing failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    def process_for_realtime_prediction(self, user_id: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process real-time data for immediate prediction
        Handles single events or small batches
        """
        try:
            # Clean and standardize
            cleaned_data, warnings = self.validate_and_clean_data(raw_data)
            standardized_data = self.standardize_input_data(cleaned_data)
            
            # Extract features for prediction
            features = {}
            
            # Check if we have swipe data
            swipe_data = {k: v for k, v in standardized_data.items() 
                         if k in ['distances', 'durations', 'speeds', 'directions', 'accelerations']}
            
            if swipe_data and any(len(v) > 0 if isinstance(v, list) else v for v in swipe_data.values()):
                swipe_features = self.extract_robust_swipe_features(swipe_data, is_realtime=True)
                features['swiping'] = [swipe_features[f] for f in self.swipe_features]
            
            # Check if we have typing data
            typing_data = {k: v for k, v in standardized_data.items() 
                          if k in ['hold_times', 'flight_times', 'backspace_rates', 'typing_speeds']}
            
            if typing_data and any(len(v) > 0 if isinstance(v, list) else v for v in typing_data.values()):
                typing_features = self.extract_robust_typing_features(typing_data, is_realtime=True)
                features['typing'] = [typing_features[f] for f in self.typing_features]
            
            result = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'features': features,
                'data_quality': {
                    'warnings': warnings,
                    'is_realtime': True,
                    'available_modalities': list(features.keys())
                }
            }
            
            if not features:
                result['error'] = 'No valid features extracted for prediction'
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing realtime data for user {user_id}: {str(e)}")
            return {
                'user_id': user_id,
                'error': f'Realtime processing failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    def validate_and_clean_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """ENHANCED validation with better noise handling"""
        cleaned_data = {}
        warnings = []
        
        try:
            for key, value in data.items():
                if isinstance(value, list):
                    # ENHANCED: Better noise detection and removal
                    clean_list = self.clean_noisy_data(value, key)
                    
                    if len(clean_list) != len(value):
                        removed_count = len(value) - len(clean_list)
                        warnings.append(f"Removed {removed_count} noisy values from {key}")
                    
                    # ENHANCED: Detect and handle sensor drift
                    if self.detect_sensor_drift(clean_list, key):
                        clean_list = self.correct_sensor_drift(clean_list, key)
                        warnings.append(f"Corrected sensor drift in {key}")
                    
                    cleaned_data[key] = clean_list
                    
                elif isinstance(value, (int, float)):
                    if not (np.isnan(value) or np.isinf(value)):
                        cleaned_data[key] = float(value)
                    else:
                        warnings.append(f"Invalid value in {key}: {value}")
                else:
                    cleaned_data[key] = value
            
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            warnings.append(f"Data validation error: {str(e)}")
        
        return cleaned_data, warnings

    def clean_noisy_data(self, values: List, field_name: str) -> List[float]:
        """ENHANCED: Remove noise from sensor data"""
        if not values:
            return []
        
        try:
            # Convert to numpy array
            arr = np.array([float(x) for x in values if isinstance(x, (int, float)) 
                           and not (np.isnan(x) or np.isinf(x))])
            
            if len(arr) == 0:
                return []
            
            # ENHANCED: Multi-stage noise removal
            
            # Stage 1: Remove extreme outliers (likely sensor errors)
            arr = self.remove_extreme_outliers(arr, field_name)
            
            # Stage 2: Apply median filter for spike removal
            if len(arr) >= 5:
                arr = self.apply_median_filter(arr)
            
            # Stage 3: Remove statistical outliers
            arr = self.remove_statistical_outliers(arr, field_name)
            
            # Stage 4: Apply smoothing if needed
            if self.should_apply_smoothing(field_name) and len(arr) >= 3:
                arr = self.apply_smoothing(arr)
            
            return arr.tolist()
            
        except Exception as e:
            logger.error(f"Error cleaning noisy data for {field_name}: {str(e)}")
            return [float(x) for x in values if isinstance(x, (int, float)) 
                   and not (np.isnan(x) or np.isinf(x))]

    def remove_extreme_outliers(self, arr: np.ndarray, field_name: str) -> np.ndarray:
        """Remove extreme outliers based on field-specific thresholds"""
        
        # Field-specific extreme value thresholds
        extreme_thresholds = {
            'speeds': (0, 50),          # Max reasonable swipe speed
            'directions': (0, 2*np.pi + 1),  # Direction range
            'accelerations': (0, 20000),     # Max reasonable acceleration
            'hold_times': (5, 2000),         # Reasonable typing hold times
            'flight_times': (5, 5000),       # Reasonable flight times
            'backspace_rates': (0, 1),       # Rate range
            'typing_speeds': (0.1, 25)       # Reasonable typing speeds
        }
        
        # Find matching threshold
        threshold = None
        for key, (min_val, max_val) in extreme_thresholds.items():
            if key in field_name.lower():
                threshold = (min_val, max_val)
                break
        
        if threshold:
            min_val, max_val = threshold
            mask = (arr >= min_val) & (arr <= max_val)
            removed = len(arr) - np.sum(mask)
            if removed > 0:
                logger.debug(f"Removed {removed} extreme outliers from {field_name}")
            return arr[mask]
        
        return arr

    def apply_median_filter(self, arr: np.ndarray, window_size: int = 3) -> np.ndarray:
        """Apply median filter to remove spikes"""
        try:
            from scipy.ndimage import median_filter
            # Use scipy if available
            return median_filter(arr, size=window_size)
        except ImportError:
            # Fallback: simple median filter
            filtered = arr.copy()
            half_window = window_size // 2
            
            for i in range(half_window, len(arr) - half_window):
                window = arr[i-half_window:i+half_window+1]
                filtered[i] = np.median(window)
            
            return filtered

    def remove_statistical_outliers(self, arr: np.ndarray, field_name: str) -> np.ndarray:
        """Remove statistical outliers using IQR method"""
        if len(arr) < 4:
            return arr
        
        try:
            Q1 = np.percentile(arr, 25)
            Q3 = np.percentile(arr, 75)
            IQR = Q3 - Q1
            
            if IQR == 0:
                return arr
            
            # Adaptive outlier threshold based on data type
            if any(keyword in field_name.lower() for keyword in ['speed', 'acceleration']):
                # More lenient for motion data (can have natural spikes)
                multiplier = 2.5
            else:
                # Standard threshold for timing data
                multiplier = 1.5
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            mask = (arr >= lower_bound) & (arr <= upper_bound)
            removed = len(arr) - np.sum(mask)
            
            if removed > 0:
                logger.debug(f"Removed {removed} statistical outliers from {field_name}")
            
            return arr[mask]
            
        except Exception as e:
            logger.error(f"Error removing statistical outliers: {str(e)}")
            return arr

    def should_apply_smoothing(self, field_name: str) -> bool:
        """Determine if smoothing should be applied based on field type"""
        # Apply smoothing to motion data but not timing data
        motion_fields = ['speed', 'acceleration', 'direction']
        return any(field in field_name.lower() for field in motion_fields)

    def apply_smoothing(self, arr: np.ndarray, alpha: float = 0.3) -> np.ndarray:
        """Apply exponential smoothing"""
        if len(arr) < 2:
            return arr
        
        smoothed = arr.copy()
        for i in range(1, len(arr)):
            smoothed[i] = alpha * arr[i] + (1 - alpha) * smoothed[i-1]
        
        return smoothed

    def detect_sensor_drift(self, values: List[float], field_name: str) -> bool:
        """Detect if there's sensor drift in the data"""
        if len(values) < 10:
            return False
        
        try:
            arr = np.array(values)
            
            # Check for monotonic trend (possible drift)
            trend_test = np.corrcoef(np.arange(len(arr)), arr)[0, 1]
            
            # Check for sudden level shifts
            diff = np.diff(arr)
            mean_diff = np.mean(np.abs(diff))
            
            # Strong trend indicates possible drift
            if abs(trend_test) > 0.7 and mean_diff > np.std(arr) * 0.5:
                logger.debug(f"Detected possible sensor drift in {field_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting sensor drift: {str(e)}")
            return False

    def correct_sensor_drift(self, values: List[float], field_name: str) -> List[float]:
        """Correct sensor drift by detrending"""
        if len(values) < 3:
            return values
        
        try:
            arr = np.array(values)
            x = np.arange(len(arr))
            
            # Fit linear trend
            slope, intercept = np.polyfit(x, arr, 1)
            
            # Remove trend
            detrended = arr - (slope * x + intercept) + np.mean(arr)
            
            logger.debug(f"Corrected drift in {field_name}: slope={slope:.4f}")
            return detrended.tolist()
            
        except Exception as e:
            logger.error(f"Error correcting sensor drift: {str(e)}")
            return values

    def calculate_data_quality_score(self, standardized_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality scores for different data types"""
        quality_scores = {}
        
        try:
            # Swipe data quality
            swipe_fields = ['speeds', 'directions', 'accelerations']
            swipe_data = {k: v for k, v in standardized_data.items() if k in swipe_fields}
            
            if swipe_data:
                quality_scores['swipe'] = self.calculate_swipe_quality(swipe_data)
            
            # Typing data quality
            typing_fields = ['hold_times', 'flight_times', 'backspace_rates', 'typing_speeds']
            typing_data = {k: v for k, v in standardized_data.items() if k in typing_fields}
            
            if typing_data:
                quality_scores['typing'] = self.calculate_typing_quality_score(typing_data)
            
            return quality_scores
            
        except Exception as e:
            logger.error(f"Error calculating quality scores: {str(e)}")
            return {}

    def calculate_swipe_quality(self, swipe_data: Dict[str, List]) -> float:
        """Calculate quality score for swipe data"""
        try:
            quality_factors = []
            
            for field, values in swipe_data.items():
                if not values:
                    continue
                
                arr = np.array(values)
                
                # Sample count quality
                sample_quality = min(1.0, len(arr) / 15)  # Target 15 samples
                quality_factors.append(sample_quality)
                
                # Variance quality (not too low, not too high)
                variance = np.var(arr)
                if field == 'speeds':
                    ideal_variance = 0.5
                elif field == 'directions':
                    ideal_variance = 1.0
                else:  # accelerations
                    ideal_variance = 50000
                
                variance_quality = 1.0 / (1.0 + abs(variance - ideal_variance) / ideal_variance)
                quality_factors.append(variance_quality)
                
                # Continuity quality (no big gaps)
                if len(arr) > 1:
                    continuity = 1.0 / (1.0 + np.std(np.diff(arr)) / np.mean(arr))
                    quality_factors.append(continuity)
            
            return float(np.mean(quality_factors)) if quality_factors else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating swipe quality: {str(e)}")
            return 0.5

    def calculate_typing_quality_score(self, typing_data: Dict[str, List]) -> float:
        """Calculate quality score for typing data"""
        try:
            quality_factors = []
            
            for field, values in typing_data.items():
                if not values:
                    continue
                
                arr = np.array(values)
                
                # Sample count quality
                sample_quality = min(1.0, len(arr) / 25)  # Target 25 samples
                quality_factors.append(sample_quality)
                
                # Consistency quality (lower CV is better for typing)
                if np.mean(arr) > 0:
                    cv = np.std(arr) / np.mean(arr)
                    consistency_quality = 1.0 / (1.0 + cv)
                    quality_factors.append(consistency_quality)
                
                # Range quality (values in reasonable range)
                if field == 'hold_times':
                    range_quality = 1.0 if 50 <= np.mean(arr) <= 500 else 0.5
                elif field == 'flight_times':
                    range_quality = 1.0 if 100 <= np.mean(arr) <= 1000 else 0.5
                elif field == 'typing_speeds':
                    range_quality = 1.0 if 1 <= np.mean(arr) <= 10 else 0.5
                else:
                    range_quality = 1.0
                
                quality_factors.append(range_quality)
            
            return float(np.mean(quality_factors)) if quality_factors else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating typing quality: {str(e)}")
            return 0.5


# Test functions
def test_small_data_handling():
    """Test the preprocessor with very small datasets"""
    print("Testing Small Data Handling")
    print("=" * 50)
    
    preprocessor = ImprovedDataPreprocessor()
    
    # Test 1: Very small onboarding data (like your real scenario)
    small_data = {
        "swipeSpeedsNew": [0.901, 0.977],  # Only 2 samples
        "swipeDirectionsNew": [79.344, 79.853],
        "swipeAccelerationsNew": [834.579, 800.845],
        "holdTimesNew": [183, 218, 199],  # Only 3 samples
        "typingSpeedsNew": [60, 65, 58]
    }
    
    print(f"\n1. Testing minimal onboarding data:")
    print(f"   Swipe samples: 2, Typing samples: 3")
    
    result = preprocessor.process_for_training("small_user", small_data)
    
    if 'error' not in result:
        readiness = result['readiness_assessment']
        print(f"  Processing successful")
        print(f"   Overall readiness: {readiness['overall_readiness']}")
        print(f"   Processing mode: {readiness['processing_mode']}")
        
        for modality, assessment in readiness['modalities'].items():
            print(f"   {modality}: {assessment['readiness']} ({assessment['sample_count']} samples)")
        
        print(f"   Recommendations:")
        for rec in readiness['recommendations']:
            print(f"     - {rec}")
    else:
        print(f"Processing failed: {result['error']}")
    
    # Test 2: Single real-time event
    realtime_data = {
        "swipeSpeedsNew": [1.2],  # Single event
        "swipeDirectionsNew": [85.5],
        "swipeAccelerationsNew": [750.0]
    }
    
    print(f"\n2. Testing single real-time event:")
    realtime_result = preprocessor.process_for_realtime_prediction("realtime_user", realtime_data)
    
    if 'error' not in realtime_result:
        print(f"Realtime processing successful")
        print(f"   Available modalities: {realtime_result['data_quality']['available_modalities']}")
        
        if 'swiping' in realtime_result['features']:
            features = realtime_result['features']['swiping']
            print(f"   Swipe features: speed={features[0]:.3f}, direction={features[2]:.3f}, accel={features[4]:.1f}")
    else:
        print(f" Realtime processing failed: {realtime_result['error']}")
    
    print("\n" + "=" * 50)
    return result, realtime_result

if __name__ == "__main__":
    test_small_data_handling()