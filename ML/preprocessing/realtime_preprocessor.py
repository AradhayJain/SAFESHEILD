# preprocessing/realtime_preprocessor.py

import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from .base_preprocessor import BaseBehavioralPreprocessor

logger = logging.getLogger(__name__)

class RealtimePreprocessor(BaseBehavioralPreprocessor):
    """
    Specialized preprocessor for real-time prediction
    Handles 1-5 samples and creates feature vectors for existing models
    Optimized for speed and minimal validation
    """
    
    def __init__(self):
        super().__init__()
        
        # Real-time specific thresholds (more lenient)
        self.min_swipes_for_prediction = 1
        self.min_typing_samples = 2
        self.max_samples_to_process = 20  # Limit for performance
        
        # Performance optimization settings
        self.enable_detailed_validation = False  # Skip detailed validation for speed
        self.enable_quality_assessment = False   # Skip quality assessment for speed
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for real-time preprocessing
        Creates feature vectors suitable for model prediction
        """
        # Quick validation (minimal for speed)
        is_valid, message = self.validate_request_structure(request_data)
        if not is_valid:
            return {'error': message}
        
        user_id = request_data['user_id']
        data = request_data['data']
        
        result = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'features': {},
            'metadata': {}
        }
        
        # Process swiping data for prediction
        if 'swiping' in data and data['swiping']:
            swipe_result = self.process_swiping_for_prediction(data['swiping'])
            if 'error' not in swipe_result:
                result['features']['swiping'] = swipe_result['features']
                result['metadata']['swiping'] = swipe_result['metadata']
            else:
                result['metadata']['swiping_error'] = swipe_result['error']
        
        # Process typing data for prediction
        if 'typing' in data and data['typing']:
            typing_result = self.process_typing_for_prediction(data['typing'])
            if 'error' not in typing_result:
                result['features']['typing'] = typing_result['features']
                result['metadata']['typing'] = typing_result['metadata']
            else:
                result['metadata']['typing_error'] = typing_result['error']
        
        # Check if we have any valid features
        if not result['features']:
            return {
                'error': 'No valid prediction features could be extracted',
                'metadata': result['metadata']
            }
        
        return result
    
    def process_swiping_for_prediction(self, swiping_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process swiping data and create feature vector for prediction"""
        try:
            # Extract raw data
            speeds, directions, accelerations = self.extract_swipe_data(swiping_data)
            
            if not speeds:
                return {'error': 'No valid swipe speed data found'}
            
            sample_count = len(speeds)
            
            # Check minimum requirements
            if sample_count < self.min_swipes_for_prediction:
                return {'error': f'Insufficient swipe data: {sample_count} samples (minimum: {self.min_swipes_for_prediction})'}
            
            # Limit processing for performance (use most recent samples)
            if sample_count > self.max_samples_to_process:
                speeds = speeds[-self.max_samples_to_process:]
                if directions:
                    directions = directions[-self.max_samples_to_process:]
                if accelerations:
                    accelerations = accelerations[-self.max_samples_to_process:]
                sample_count = self.max_samples_to_process
                logger.info(f"Limited swipe processing to {self.max_samples_to_process} most recent samples")
            
            # Calculate features using all available data (more robust for real-time)
            features = self.calculate_basic_swipe_features(speeds, directions, accelerations)
            
            # Quick validation (only if enabled)
            if self.enable_detailed_validation:
                is_valid, error_msg = self.validate_swipe_features(features)
                if not is_valid:
                    return {'error': f'Feature validation failed: {error_msg}'}
            else:
                # Minimal validation - just check for NaN/inf
                if any(np.isnan(f) or np.isinf(f) for f in features):
                    return {'error': 'Features contain invalid values (NaN/inf)'}
            
            # Calculate confidence based on sample size
            confidence_level = self.calculate_prediction_confidence(sample_count, 'swiping')
            
            # Minimal metadata for performance
            metadata = {
                'sample_count': sample_count,
                'confidence_level': confidence_level,
                'feature_names': self.swipe_features,
                'processing_time': datetime.now().isoformat()
            }
            
            # Add quality assessment only if enabled
            if self.enable_quality_assessment:
                metadata['data_quality'] = self.calculate_data_quality_score(speeds, 'swiping')
                metadata['speed_stats'] = {
                    'mean': float(np.mean(speeds)),
                    'std': float(np.std(speeds)),
                    'range': [float(min(speeds)), float(max(speeds))]
                }
            
            return {
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing swiping data for prediction: {str(e)}")
            return {'error': f'Swiping processing failed: {str(e)}'}
    
    def process_typing_for_prediction(self, typing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process typing data and create feature vector for prediction"""
        try:
            # Extract raw data
            hold_times, flight_times, backspace_rates, typing_speeds = self.extract_typing_data(typing_data)
            
            if not hold_times:
                return {'error': 'No valid hold times data found'}
            
            sample_count = len(hold_times)
            
            # Check minimum requirements
            if sample_count < self.min_typing_samples:
                return {'error': f'Insufficient typing data: {sample_count} samples (minimum: {self.min_typing_samples})'}
            
            # Limit processing for performance (use most recent samples)
            if sample_count > self.max_samples_to_process:
                hold_times = hold_times[-self.max_samples_to_process:]
                if flight_times:
                    flight_times = flight_times[-self.max_samples_to_process:]
                sample_count = self.max_samples_to_process
                logger.info(f"Limited typing processing to {self.max_samples_to_process} most recent samples")
            
            # Calculate features using all available data
            features = self.calculate_basic_typing_features(
                hold_times, flight_times, backspace_rates, typing_speeds
            )
            
            # Quick validation (only if enabled)
            if self.enable_detailed_validation:
                is_valid, error_msg = self.validate_typing_features(features)
                if not is_valid:
                    return {'error': f'Feature validation failed: {error_msg}'}
            else:
                # Minimal validation - just check for NaN/inf
                if any(np.isnan(f) or np.isinf(f) for f in features):
                    return {'error': 'Features contain invalid values (NaN/inf)'}
            
            # Calculate confidence based on sample size
            confidence_level = self.calculate_prediction_confidence(sample_count, 'typing')
            
            # Minimal metadata for performance
            metadata = {
                'sample_count': sample_count,
                'confidence_level': confidence_level,
                'feature_names': self.typing_features,
                'processing_time': datetime.now().isoformat()
            }
            
            # Add quality assessment only if enabled
            if self.enable_quality_assessment:
                metadata['data_quality'] = self.calculate_data_quality_score(hold_times, 'typing')
                metadata['hold_time_stats'] = {
                    'mean': float(np.mean(hold_times)),
                    'std': float(np.std(hold_times)),
                    'range': [float(min(hold_times)), float(max(hold_times))]
                }
            
            return {
                'features': features,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing typing data for prediction: {str(e)}")
            return {'error': f'Typing processing failed: {str(e)}'}
    
    def calculate_prediction_confidence(self, sample_count: int, modality: str) -> str:
        """Calculate confidence level for prediction based on sample count"""
        if modality == 'swiping':
            if sample_count >= 5:
                return 'high'
            elif sample_count >= 3:
                return 'medium'
            elif sample_count >= 2:
                return 'low'
            else:
                return 'very_low'
        else:  # typing
            if sample_count >= 8:
                return 'high'
            elif sample_count >= 5:
                return 'medium'
            elif sample_count >= 3:
                return 'low'
            else:
                return 'very_low'
    
    def enable_performance_mode(self):
        """Enable maximum performance mode (disable all optional features)"""
        self.enable_detailed_validation = False
        self.enable_quality_assessment = False
        self.max_samples_to_process = 10
        logger.info("Performance mode enabled - minimal validation and processing")
    
    def enable_quality_mode(self):
        """Enable quality mode (enable detailed validation and assessment)"""
        self.enable_detailed_validation = True
        self.enable_quality_assessment = True
        self.max_samples_to_process = 20
        logger.info("Quality mode enabled - detailed validation and assessment")
    
    def process_lightweight(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ultra-lightweight processing for high-frequency predictions
        Minimal validation, maximum speed
        """
        try:
            user_id = request_data.get('user_id')
            data = request_data.get('data', {})
            
            if not user_id or not data:
                return {'error': 'Missing user_id or data'}
            
            features = {}
            
            # Minimal swiping processing
            if 'swiping' in data:
                swiping_data = data['swiping']
                speeds = self.safe_extract_array(swiping_data, 'swipeSpeeds')
                if speeds and len(speeds) >= 1:
                    directions = self.safe_extract_array(swiping_data, 'swipeDirections')
                    accelerations = self.safe_extract_array(swiping_data, 'swipeAccelerations')
                    
                    # Use only most recent 5 samples for speed
                    if len(speeds) > 5:
                        speeds = speeds[-5:]
                        if directions:
                            directions = directions[-5:]
                        if accelerations:
                            accelerations = accelerations[-5:]
                    
                    swipe_features = self.calculate_basic_swipe_features(speeds, directions, accelerations)
                    if not any(np.isnan(f) or np.isinf(f) for f in swipe_features):
                        features['swiping'] = swipe_features
            
            # Minimal typing processing
            if 'typing' in data:
                typing_data = data['typing']
                hold_times = self.safe_extract_array(typing_data, 'holdTimes')
                if hold_times and len(hold_times) >= 2:
                    flight_times = self.safe_extract_array(typing_data, 'flightTimes')
                    backspace_rates = self.safe_extract_array(typing_data, 'backspaceRates')
                    typing_speeds = self.safe_extract_array(typing_data, 'typingSpeeds')
                    
                    # Use only most recent 8 samples for speed
                    if len(hold_times) > 8:
                        hold_times = hold_times[-8:]
                        if flight_times:
                            flight_times = flight_times[-8:]
                    
                    typing_features = self.calculate_basic_typing_features(
                        hold_times, flight_times, backspace_rates, typing_speeds
                    )
                    if not any(np.isnan(f) or np.isinf(f) for f in typing_features):
                        features['typing'] = typing_features
            
            if not features:
                return {'error': 'No valid features extracted'}
            
            return {
                'user_id': user_id,
                'features': features,
                'timestamp': datetime.now().isoformat(),
                'processing_mode': 'lightweight'
            }
            
        except Exception as e:
            logger.error(f"Error in lightweight processing: {str(e)}")
            return {'error': f'Lightweight processing failed: {str(e)}'}
    
    def batch_process_features(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple requests efficiently
        Useful for batch prediction scenarios
        """
        results = []
        
        for request in requests:
            try:
                result = self.process_lightweight(request)
                results.append(result)
            except Exception as e:
                results.append({
                    'error': f'Batch processing failed: {str(e)}',
                    'user_id': request.get('user_id', 'unknown')
                })
        
        return results