# preprocessing/onboarding_preprocessor.py

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from .base_preprocessor import BaseBehavioralPreprocessor

logger = logging.getLogger(__name__)

class OnboardingPreprocessor(BaseBehavioralPreprocessor):
    """
    Specialized preprocessor for onboarding process
    Handles 15-20 samples and creates DataFrames for model training
    """
    
    def __init__(self):
        super().__init__()
        
        # Onboarding-specific thresholds
        self.min_swipes_for_training = 15
        self.optimal_swipes = 20
        self.min_typing_samples = 10
        self.optimal_typing_samples = 15
        
        # Sliding window parameters for creating multiple training samples
        self.swipe_window_size = 8  # Use 8 swipes per training sample
        self.typing_window_size = 6  # Use 6 keystrokes per training sample
        self.overlap_ratio = 0.5    # 50% overlap between windows
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for onboarding preprocessing
        Creates DataFrames suitable for model training
        """
        # Validate request structure
        is_valid, message = self.validate_request_structure(request_data)
        if not is_valid:
            return {'error': message}
        
        user_id = request_data['user_id']
        data = request_data['data']
        
        result = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'training_data': {},
            'metadata': {},
            'readiness': {}
        }
        
        # Process swiping data for training
        if 'swiping' in data and data['swiping']:
            swipe_result = self.process_swiping_for_training(data['swiping'])
            if 'error' not in swipe_result:
                result['training_data']['swiping'] = swipe_result['dataframe']
                result['metadata']['swiping'] = swipe_result['metadata']
                result['readiness']['swiping'] = swipe_result['readiness']
            else:
                result['metadata']['swiping_error'] = swipe_result['error']
                result['readiness']['swiping'] = 'insufficient_data'
        
        # Process typing data for training
        if 'typing' in data and data['typing']:
            typing_result = self.process_typing_for_training(data['typing'])
            if 'error' not in typing_result:
                result['training_data']['typing'] = typing_result['dataframe']
                result['metadata']['typing'] = typing_result['metadata']
                result['readiness']['typing'] = typing_result['readiness']
            else:
                result['metadata']['typing_error'] = typing_result['error']
                result['readiness']['typing'] = 'insufficient_data'
        
        # Check overall readiness
        if not result['training_data']:
            return {
                'error': 'No valid training data could be created',
                'metadata': result['metadata'],
                'readiness': result['readiness']
            }
        
        return result
    
    def process_swiping_for_training(self, swiping_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process swiping data and create training DataFrame"""
        try:
            # Extract raw data
            speeds, directions, accelerations = self.extract_swipe_data(swiping_data)
            
            if not speeds:
                return {'error': 'No valid swipe speed data found'}
            
            sample_count = len(speeds)
            logger.info(f"Processing {sample_count} swipes for training")
            
            # Check if we have sufficient data
            if sample_count < 5:  # Absolute minimum
                return {'error': f'Insufficient swipe data: {sample_count} samples (minimum: 5)'}
            
            # Determine readiness level
            if sample_count >= self.optimal_swipes:
                readiness = 'optimal'
                contamination = 0.1
            elif sample_count >= self.min_swipes_for_training:
                readiness = 'sufficient'
                contamination = 0.12
            elif sample_count >= 10:
                readiness = 'limited'
                contamination = 0.15
            else:
                readiness = 'minimal'
                contamination = 0.2
            
            # Create training samples using sliding windows
            training_samples = self.create_swipe_training_samples(speeds, directions, accelerations)
            
            if not training_samples:
                return {'error': 'Failed to create training samples'}
            
            # Create DataFrame
            df = pd.DataFrame(training_samples)
            
            # Validate all features
            feature_validation_errors = []
            for idx, row in df.iterrows():
                features = row[self.swipe_features].tolist()
                is_valid, error_msg = self.validate_swipe_features(features)
                if not is_valid:
                    feature_validation_errors.append(f"Row {idx}: {error_msg}")
            
            if feature_validation_errors:
                logger.warning(f"Feature validation issues: {feature_validation_errors}")
                # Remove invalid rows
                valid_rows = []
                for idx, row in df.iterrows():
                    features = row[self.swipe_features].tolist()
                    is_valid, _ = self.validate_swipe_features(features)
                    if is_valid:
                        valid_rows.append(idx)
                
                if not valid_rows:
                    return {'error': 'No valid training samples after feature validation'}
                
                df = df.loc[valid_rows].reset_index(drop=True)
            
            # Calculate metadata
            data_quality = self.calculate_data_quality_score(speeds, 'swiping')
            
            metadata = {
                'sample_count': sample_count,
                'training_samples_created': len(df),
                'readiness_level': readiness,
                'recommended_contamination': contamination,
                'data_quality': data_quality,
                'feature_columns': self.swipe_features,
                'window_size_used': min(self.swipe_window_size, sample_count),
                'raw_data_summary': {
                    'speed_range': [float(min(speeds)), float(max(speeds))],
                    'speed_mean': float(np.mean(speeds)),
                    'direction_available': directions is not None,
                    'acceleration_available': accelerations is not None
                }
            }
            
            return {
                'dataframe': df,
                'metadata': metadata,
                'readiness': readiness
            }
            
        except Exception as e:
            logger.error(f"Error processing swiping data for training: {str(e)}")
            return {'error': f'Swiping processing failed: {str(e)}'}
    
    def process_typing_for_training(self, typing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process typing data and create training DataFrame"""
        try:
            # Extract raw data
            hold_times, flight_times, backspace_rates, typing_speeds = self.extract_typing_data(typing_data)
            
            if not hold_times:
                return {'error': 'No valid hold times data found'}
            
            sample_count = len(hold_times)
            logger.info(f"Processing {sample_count} keystrokes for training")
            
            # Check if we have sufficient data
            if sample_count < 5:  # Absolute minimum
                return {'error': f'Insufficient typing data: {sample_count} samples (minimum: 5)'}
            
            # Determine readiness level
            if sample_count >= self.optimal_typing_samples:
                readiness = 'optimal'
            elif sample_count >= self.min_typing_samples:
                readiness = 'sufficient'
            elif sample_count >= 7:
                readiness = 'limited'
            else:
                readiness = 'minimal'
            
            # Create training samples using sliding windows
            training_samples = self.create_typing_training_samples(
                hold_times, flight_times, backspace_rates, typing_speeds
            )
            
            if not training_samples:
                return {'error': 'Failed to create training samples'}
            
            # Create DataFrame
            df = pd.DataFrame(training_samples)
            
            # Validate all features
            feature_validation_errors = []
            for idx, row in df.iterrows():
                features = row[self.typing_features].tolist()
                is_valid, error_msg = self.validate_typing_features(features)
                if not is_valid:
                    feature_validation_errors.append(f"Row {idx}: {error_msg}")
            
            if feature_validation_errors:
                logger.warning(f"Feature validation issues: {feature_validation_errors}")
                # Remove invalid rows
                valid_rows = []
                for idx, row in df.iterrows():
                    features = row[self.typing_features].tolist()
                    is_valid, _ = self.validate_typing_features(features)
                    if is_valid:
                        valid_rows.append(idx)
                
                if not valid_rows:
                    return {'error': 'No valid training samples after feature validation'}
                
                df = df.loc[valid_rows].reset_index(drop=True)
            
            # Calculate metadata
            data_quality = self.calculate_data_quality_score(hold_times, 'typing')
            
            metadata = {
                'sample_count': sample_count,
                'training_samples_created': len(df),
                'readiness_level': readiness,
                'data_quality': data_quality,
                'feature_columns': self.typing_features,
                'window_size_used': min(self.typing_window_size, sample_count),
                'raw_data_summary': {
                    'hold_time_range': [float(min(hold_times)), float(max(hold_times))],
                    'hold_time_mean': float(np.mean(hold_times)),
                    'flight_times_available': flight_times is not None,
                    'backspace_rates_available': backspace_rates is not None,
                    'typing_speeds_available': typing_speeds is not None
                }
            }
            
            return {
                'dataframe': df,
                'metadata': metadata,
                'readiness': readiness
            }
            
        except Exception as e:
            logger.error(f"Error processing typing data for training: {str(e)}")
            return {'error': f'Typing processing failed: {str(e)}'}
    
    def create_swipe_training_samples(self, speeds: List[float], directions: Optional[List[float]], 
                                    accelerations: Optional[List[float]]) -> List[Dict]:
        """Create multiple training samples using sliding windows"""
        try:
            samples = []
            data_length = len(speeds)
            
            # Adjust window size based on available data
            window_size = min(self.swipe_window_size, data_length)
            
            if window_size >= data_length:
                # Use all data as a single sample
                features = self.calculate_basic_swipe_features(speeds, directions, accelerations)
                sample = dict(zip(self.swipe_features, features))
                sample['sample_type'] = 'full_data'
                sample['window_start'] = 0
                sample['window_size'] = data_length
                samples.append(sample)
            else:
                # Create overlapping windows
                step_size = max(1, int(window_size * (1 - self.overlap_ratio)))
                
                for start_idx in range(0, data_length - window_size + 1, step_size):
                    end_idx = start_idx + window_size
                    
                    window_speeds = speeds[start_idx:end_idx]
                    window_directions = directions[start_idx:end_idx] if directions else None
                    window_accelerations = accelerations[start_idx:end_idx] if accelerations else None
                    
                    features = self.calculate_basic_swipe_features(
                        window_speeds, window_directions, window_accelerations
                    )
                    
                    sample = dict(zip(self.swipe_features, features))
                    sample['sample_type'] = 'windowed'
                    sample['window_start'] = start_idx
                    sample['window_size'] = window_size
                    samples.append(sample)
            
            # Ensure we have at least 3 samples for training
            while len(samples) < 3 and data_length >= 3:
                # Create additional samples with different window sizes
                alt_window_size = max(3, window_size - 2)
                if alt_window_size < data_length:
                    for start_idx in range(0, data_length - alt_window_size + 1, alt_window_size):
                        end_idx = start_idx + alt_window_size
                        
                        window_speeds = speeds[start_idx:end_idx]
                        window_directions = directions[start_idx:end_idx] if directions else None
                        window_accelerations = accelerations[start_idx:end_idx] if accelerations else None
                        
                        features = self.calculate_basic_swipe_features(
                            window_speeds, window_directions, window_accelerations
                        )
                        
                        sample = dict(zip(self.swipe_features, features))
                        sample['sample_type'] = 'alternative_window'
                        sample['window_start'] = start_idx
                        sample['window_size'] = alt_window_size
                        samples.append(sample)
                        
                        if len(samples) >= 3:
                            break
                break
            
            logger.info(f"Created {len(samples)} swipe training samples from {data_length} raw samples")
            return samples
            
        except Exception as e:
            logger.error(f"Error creating swipe training samples: {str(e)}")
            return []
    
    def create_typing_training_samples(self, hold_times: List[float], flight_times: Optional[List[float]],
                                     backspace_rates: Optional[List[float]], 
                                     typing_speeds: Optional[List[float]]) -> List[Dict]:
        """Create multiple training samples using sliding windows"""
        try:
            samples = []
            data_length = len(hold_times)
            
            # Adjust window size based on available data
            window_size = min(self.typing_window_size, data_length)
            
            if window_size >= data_length:
                # Use all data as a single sample
                features = self.calculate_basic_typing_features(
                    hold_times, flight_times, backspace_rates, typing_speeds
                )
                sample = dict(zip(self.typing_features, features))
                sample['sample_type'] = 'full_data'
                sample['window_start'] = 0
                sample['window_size'] = data_length
                samples.append(sample)
            else:
                # Create overlapping windows
                step_size = max(1, int(window_size * (1 - self.overlap_ratio)))
                
                for start_idx in range(0, data_length - window_size + 1, step_size):
                    end_idx = start_idx + window_size
                    
                    window_hold = hold_times[start_idx:end_idx]
                    window_flight = flight_times[start_idx:end_idx] if flight_times else None
                    
                    features = self.calculate_basic_typing_features(
                        window_hold, window_flight, backspace_rates, typing_speeds
                    )
                    
                    sample = dict(zip(self.typing_features, features))
                    sample['sample_type'] = 'windowed'
                    sample['window_start'] = start_idx
                    sample['window_size'] = window_size
                    samples.append(sample)
            
            # Ensure we have at least 3 samples for training
            while len(samples) < 3 and data_length >= 3:
                # Create additional samples with different window sizes
                alt_window_size = max(3, window_size - 1)
                if alt_window_size < data_length:
                    for start_idx in range(0, data_length - alt_window_size + 1, alt_window_size):
                        end_idx = start_idx + alt_window_size
                        
                        window_hold = hold_times[start_idx:end_idx]
                        window_flight = flight_times[start_idx:end_idx] if flight_times else None
                        
                        features = self.calculate_basic_typing_features(
                            window_hold, window_flight, backspace_rates, typing_speeds
                        )
                        
                        sample = dict(zip(self.typing_features, features))
                        sample['sample_type'] = 'alternative_window'
                        sample['window_start'] = start_idx
                        sample['window_size'] = alt_window_size
                        samples.append(sample)
                        
                        if len(samples) >= 3:
                            break
                break
            
            logger.info(f"Created {len(samples)} typing training samples from {data_length} raw samples")
            return samples
            
        except Exception as e:
            logger.error(f"Error creating typing training samples: {str(e)}")
            return []