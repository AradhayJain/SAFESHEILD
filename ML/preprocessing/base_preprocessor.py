# preprocessing/base_preprocessor.py

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseBehavioralPreprocessor(ABC):
    """
    Base class for behavioral data preprocessing
    Contains common functionality shared between onboarding and real-time processors
    """
    
    def __init__(self):
        # Feature definitions (consistent across all processors)
        self.swipe_features = [
            'speed_mean', 'speed_std', 'direction_mean', 
            'direction_std', 'acceleration_mean', 'acceleration_std'
        ]
        
        self.typing_features = [
            'hold_mean', 'hold_std', 'flight_mean', 
            'flight_std', 'backspace_rate', 'typing_speed'
        ]
        
        # Validation ranges
        self.swipe_ranges = {
            'speed_mean': (0, 50),
            'speed_std': (0, 20),
            'direction_mean': (0, 2*np.pi),
            'direction_std': (0, np.pi),
            'acceleration_mean': (0, 2000),
            'acceleration_std': (0, 1000)
        }
        
        self.typing_ranges = {
            'hold_mean': (10, 1000),
            'hold_std': (0, 500),
            'flight_mean': (0, 2000),
            'flight_std': (0, 1000),
            'backspace_rate': (0, 1),
            'typing_speed': (5, 200)
        }
    
    def validate_request_structure(self, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate the basic structure of request data"""
        if not isinstance(request_data, dict):
            return False, "Request data must be a dictionary"
        
        if 'user_id' not in request_data:
            return False, "Missing required field: user_id"
        
        if 'data' not in request_data:
            return False, "Missing required field: data"
        
        data = request_data['data']
        if not isinstance(data, dict):
            return False, "Data field must be a dictionary"
        
        # Check if we have at least one modality
        has_swiping = 'swiping' in data and data['swiping']
        has_typing = 'typing' in data and data['typing']
        
        if not has_swiping and not has_typing:
            return False, "No behavioral data found (swiping or typing)"
        
        return True, "Request structure is valid"
    
    def safe_extract_array(self, data: Dict, key: str) -> Optional[List[float]]:
        """Safely extract and convert array data with comprehensive error handling"""
        try:
            raw_data = data.get(key, [])
            if not raw_data:
                return None
            
            # Handle both single values and arrays
            if not isinstance(raw_data, list):
                try:
                    value = float(raw_data)
                    if not (np.isnan(value) or np.isinf(value)):
                        return [value]
                except (ValueError, TypeError):
                    return None
            
            # Convert list to float and filter out invalid values
            result = []
            for item in raw_data:
                try:
                    value = float(item)
                    if not (np.isnan(value) or np.isinf(value)):
                        result.append(value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value in {key}: {item}")
                    continue
            
            return result if result else None
            
        except Exception as e:
            logger.error(f"Error extracting {key}: {str(e)}")
            return None
    
    def calculate_basic_swipe_features(self, speeds: List[float], directions: Optional[List[float]], 
                                     accelerations: Optional[List[float]]) -> List[float]:
        """Calculate basic swipe features from raw data"""
        # Speed features
        speed_mean = np.mean(speeds)
        speed_std = np.std(speeds) if len(speeds) > 1 else 0.0
        
        # Direction features
        if directions and len(directions) > 0:
            direction_mean = np.mean(directions)
            direction_std = np.std(directions) if len(directions) > 1 else 0.0
        else:
            direction_mean = 0.0
            direction_std = 0.0
        
        # Acceleration features
        if accelerations and len(accelerations) > 0:
            acceleration_mean = np.mean(accelerations)
            acceleration_std = np.std(accelerations) if len(accelerations) > 1 else 0.0
        else:
            acceleration_mean = 0.0
            acceleration_std = 0.0
        
        return [
            float(speed_mean), float(speed_std), float(direction_mean),
            float(direction_std), float(acceleration_mean), float(acceleration_std)
        ]
    
    def calculate_basic_typing_features(self, hold_times: List[float], flight_times: Optional[List[float]],
                                      backspace_rates: Optional[List[float]], 
                                      typing_speeds: Optional[List[float]]) -> List[float]:
        """Calculate basic typing features from raw data"""
        # Hold time features
        hold_mean = np.mean(hold_times)
        hold_std = np.std(hold_times) if len(hold_times) > 1 else 0.0
        
        # Flight time features
        if flight_times and len(flight_times) > 0:
            flight_mean = np.mean(flight_times)
            flight_std = np.std(flight_times) if len(flight_times) > 1 else 0.0
        else:
            flight_mean = 0.0
            flight_std = 0.0
        
        # Backspace rate
        if backspace_rates:
            backspace_rate = np.mean(backspace_rates) if isinstance(backspace_rates, list) else float(backspace_rates[0])
        else:
            backspace_rate = 0.0
        
        # Typing speed
        if typing_speeds:
            typing_speed = np.mean(typing_speeds) if isinstance(typing_speeds, list) else float(typing_speeds[0])
        else:
            typing_speed = self.estimate_typing_speed(hold_times, flight_times)
        
        return [
            float(hold_mean), float(hold_std), float(flight_mean),
            float(flight_std), float(backspace_rate), float(typing_speed)
        ]
    
    def estimate_typing_speed(self, hold_times: List[float], flight_times: Optional[List[float]]) -> float:
        """Estimate typing speed from keystroke timings"""
        try:
            if not hold_times:
                return 30.0  # Default reasonable speed
            
            total_keystrokes = len(hold_times)
            
            # Calculate total time
            if flight_times and len(flight_times) > 0:
                total_time_ms = sum(hold_times) + sum(flight_times)
            else:
                # Estimate flight times if not provided
                estimated_flight_time = len(hold_times) * 100  # 100ms average
                total_time_ms = sum(hold_times) + estimated_flight_time
            
            if total_time_ms <= 0:
                return 30.0
            
            # Convert to words per minute (assuming 5 characters per word)
            chars_per_minute = (total_keystrokes / total_time_ms) * 60000
            wpm = chars_per_minute / 5
            
            # Clamp to reasonable range
            return max(5.0, min(200.0, wpm))
            
        except Exception as e:
            logger.warning(f"Error estimating typing speed: {str(e)}")
            return 30.0
    
    def validate_swipe_features(self, features: List[float]) -> Tuple[bool, str]:
        """Validate swipe features against expected ranges"""
        try:
            if len(features) != 6:
                return False, f"Expected 6 swipe features, got {len(features)}"
            
            feature_names = self.swipe_features
            for i, (feature_name, value) in enumerate(zip(feature_names, features)):
                min_val, max_val = self.swipe_ranges[feature_name]
                if not (min_val <= value <= max_val):
                    return False, f"{feature_name} value {value} outside range [{min_val}, {max_val}]"
            
            return True, "Swipe features validation passed"
            
        except Exception as e:
            return False, f"Swipe validation error: {str(e)}"
    
    def validate_typing_features(self, features: List[float]) -> Tuple[bool, str]:
        """Validate typing features against expected ranges"""
        try:
            if len(features) != 6:
                return False, f"Expected 6 typing features, got {len(features)}"
            
            feature_names = self.typing_features
            for i, (feature_name, value) in enumerate(zip(feature_names, features)):
                min_val, max_val = self.typing_ranges[feature_name]
                if not (min_val <= value <= max_val):
                    return False, f"{feature_name} value {value} outside range [{min_val}, {max_val}]"
            
            return True, "Typing features validation passed"
            
        except Exception as e:
            return False, f"Typing validation error: {str(e)}"
    
    def calculate_data_quality_score(self, values: List[float], modality: str) -> str:
        """Calculate data quality score based on consistency"""
        try:
            if len(values) < 2:
                return 'poor'
            
            # Calculate coefficient of variation
            mean_val = np.mean(values)
            if mean_val == 0:
                return 'poor'
            
            cv = np.std(values) / mean_val
            
            # Different thresholds for different modalities
            if modality == 'swiping':
                if cv < 0.1:
                    return 'excellent'
                elif cv < 0.3:
                    return 'good'
                elif cv < 0.5:
                    return 'fair'
                else:
                    return 'poor'
            else:  # typing
                if cv < 0.2:
                    return 'excellent'
                elif cv < 0.4:
                    return 'good'
                elif cv < 0.6:
                    return 'fair'
                else:
                    return 'poor'
        except:
            return 'poor'
    
    def extract_swipe_data(self, swiping_data: Dict[str, Any]) -> Tuple[Optional[List[float]], 
                                                                       Optional[List[float]], 
                                                                       Optional[List[float]]]:
        """Extract and validate swipe data from nested structure"""
        distances = self.safe_extract_array(swiping_data, 'swipeDistances')
        durations = self.safe_extract_array(swiping_data, 'swipeDurations')
        speeds = self.safe_extract_array(swiping_data, 'swipeSpeeds')
        directions = self.safe_extract_array(swiping_data, 'swipeDirections')
        accelerations = self.safe_extract_array(swiping_data, 'swipeAccelerations')
        
        # Calculate speeds if not provided
        if not speeds and distances and durations:
            speeds = []
            for d, t in zip(distances, durations):
                if t > 0:
                    speeds.append(d / t)
                else:
                    speeds.append(0.0)
        
        return speeds, directions, accelerations
    
    def extract_typing_data(self, typing_data: Dict[str, Any]) -> Tuple[Optional[List[float]], 
                                                                       Optional[List[float]], 
                                                                       Optional[List[float]], 
                                                                       Optional[List[float]]]:
        """Extract and validate typing data from nested structure"""
        hold_times = self.safe_extract_array(typing_data, 'holdTimes')
        flight_times = self.safe_extract_array(typing_data, 'flightTimes')
        backspace_rates = self.safe_extract_array(typing_data, 'backspaceRates')
        typing_speeds = self.safe_extract_array(typing_data, 'typingSpeeds')
        
        return hold_times, flight_times, backspace_rates, typing_speeds
    
    @abstractmethod
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Abstract method to be implemented by subclasses"""
        pass