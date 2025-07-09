from Swiping.predict_swipe_risk import SwipeRiskPredictor
from Swiping.update_model import SwipeModelUpdater 
from Typing.predict_typing_risk import TypingRiskPredictor
from Typing.update_model import TypingModelUpdater
from preprocessing.realtime_preprocessor import RealtimePreprocessor
from typing import Dict, Any, List
import numpy as np
import logging
import datetime

logger = logging.getLogger(__name__)

def convert_to_native(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native(v) for v in obj]
    elif isinstance(obj, (np.bool_, np.int_, np.float_)):
        return obj.item()
    else:
        return obj

def predict_with_model(user_id: Any, data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main prediction function for real-time behavioral analysis
    
    Args:
        user_id: User identifier
        data_dict: Nested data structure or legacy format:
        {
            "swiping": {
                "swipeDistances": [...],
                "swipeDurations": [...],
                "swipeSpeeds": [...],
                "swipeDirections": [...],
                "swipeAccelerations": [...]
            },
            "typing": {
                "holdTimes": [...],
                "flightTimes": [...],
                "backspaceRates": [...],
                "typingSpeeds": [...]
            }
        }
    
    Returns:
        Prediction results for each available modality
    """
    try:

        if isinstance(data_dict, dict) and ('swiping' in data_dict or 'typing' in data_dict):

            request_data = {
                'user_id': user_id,
                'data': data_dict
            }
        else:

            logger.warning("Received legacy data format, attempting conversion")
            request_data = {
                'user_id': user_id,
                'data': data_dict
            }
        
        # Initialize real-time preprocessor
        preprocessor = RealtimePreprocessor()
        
        # Process data for prediction
        preprocessing_result = preprocessor.process_request(request_data)
        
        if 'error' in preprocessing_result:
            return {
                'error': preprocessing_result['error'],
                'user_id': str(user_id),
                'timestamp': preprocessing_result.get('timestamp'),
                'details': preprocessing_result.get('metadata', {})
            }
        
        user_id_str = str(preprocessing_result['user_id'])
        features = preprocessing_result['features']
        metadata = preprocessing_result['metadata']
        
        response = {
            'user_id': user_id_str,
            'timestamp': preprocessing_result['timestamp'],
            'predictions': {},
            'preprocessing_metadata': metadata
        }
        
        # Process swiping predictions
        if 'swiping' in features:
            logger.info(f"Processing swiping prediction for user {user_id_str}")
            swipe_result = predict_swiping(user_id_str, features['swiping'])
            response['predictions']['swiping'] = swipe_result
        
        # Process typing predictions  
        if 'typing' in features:
            logger.info(f"Processing typing prediction for user {user_id_str}")
            typing_result = predict_typing(user_id_str, features['typing'])
            response['predictions']['typing'] = typing_result
        
        # Add prediction summary
        risk_levels = []
        confidence_scores = []
        
        for modality, result in response['predictions'].items():
            if 'prediction_result' in result and 'error' not in result['prediction_result']:
                pred_result = result['prediction_result']
                risk_levels.append(pred_result.get('risk_category', 'unknown'))
                confidence_scores.append(pred_result.get('confidence', 0))
        
        if risk_levels:
            # Determine overall risk level
            if 'critical_risk' in risk_levels or 'high_risk' in risk_levels:
                overall_risk = 'high_risk'
            elif 'medium_risk' in risk_levels:
                overall_risk = 'medium_risk'
            elif 'low_risk' in risk_levels:
                overall_risk = 'low_risk'
            else:
                overall_risk = 'normal'
            
            response['prediction_summary'] = {
                'overall_risk': overall_risk,
                'average_confidence': round(np.mean(confidence_scores), 2) if confidence_scores else 0,
                'modalities_analyzed': list(response['predictions'].keys()),
                'individual_risks': {mod: result['prediction_result'].get('risk_category', 'unknown') 
                                   for mod, result in response['predictions'].items() 
                                   if 'prediction_result' in result and 'error' not in result['prediction_result']}
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in predict_with_model for user {user_id}: {str(e)}")
        return {
            'error': f'Prediction process failed: {str(e)}',
            'user_id': str(user_id),
            'timestamp': datetime.now().isoformat()
        }

def predict_swiping(user_id: str, swipe_features: List[float]) -> Dict[str, Any]:
    """
    Predict swiping behavior risk
    
    Args:
        user_id: User identifier
        swipe_features: Preprocessed swipe features [speed_mean, speed_std, direction_mean, 
                       direction_std, acceleration_mean, acceleration_std]
    
    Returns:
        Dictionary containing prediction and model update results
    """
    try:
        # Initialize predictors
        srp = SwipeRiskPredictor()
        smu = SwipeModelUpdater()
        
        # Make prediction
        prediction_result = srp.predict_swipe_risk(user_id, swipe_features)
        
        if 'error' in prediction_result:
            return {
                'prediction_result': prediction_result,
                'model_updation': {'error': 'Skipped due to prediction error'},
                'status': 'prediction_failed'
            }
        
        # Update model with new data (for continuous learning)
        model_update_result = smu.update_swipe_model_if_appropriate(
            user_id, swipe_features, prediction_result
        )
        
        return {
            'prediction_result': convert_to_native(prediction_result),
            'model_updation': convert_to_native(model_update_result),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Error in predict_swiping for user {user_id}: {str(e)}")
        return {
            'prediction_result': {'error': f'Swipe prediction failed: {str(e)}'},
            'model_updation': {'error': 'Skipped due to prediction error'},
            'status': 'error'
        }

def predict_typing(user_id: str, typing_features: List[float]) -> Dict[str, Any]:
    """
    Predict typing behavior risk
    
    Args:
        user_id: User identifier
        typing_features: Preprocessed typing features [hold_mean, hold_std, flight_mean, 
                        flight_std, backspace_rate, typing_speed]
    
    Returns:
        Dictionary containing prediction and model update results
    """
    try:
        # Initialize predictors
        trp = TypingRiskPredictor()
        tmu = TypingModelUpdater()
        
        # Make prediction
        prediction_result = trp.predict_risk(user_id, typing_features)
        
        if 'error' in prediction_result:
            return {
                'prediction_result': prediction_result,
                'model_updation': {'error': 'Skipped due to prediction error'},
                'status': 'prediction_failed'
            }
        
        # Update model with new data (for continuous learning)
        model_update_result = tmu.update_model_if_appropriate(
            user_id, typing_features, prediction_result
        )
        
        return {
            'prediction_result': convert_to_native(prediction_result),
            'model_updation': convert_to_native(model_update_result),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Error in predict_typing for user {user_id}: {str(e)}")
        return {
            'prediction_result': {'error': f'Typing prediction failed: {str(e)}'},
            'model_updation': {'error': 'Skipped due to prediction error'},
            'status': 'error'
        }

def predict_lightweight(user_id: Any, data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lightweight prediction function for high-frequency real-time analysis
    Minimal validation and processing for maximum speed
    
    Args:
        user_id: User identifier
        data_dict: Nested data structure (same as predict_with_model)
    
    Returns:
        Simplified prediction results
    """
    try:
        request_data = {
            'user_id': user_id,
            'data': data_dict
        }
        
        # Use lightweight processing
        preprocessor = RealtimePreprocessor()
        preprocessor.enable_performance_mode()  # Maximum speed
        
        preprocessing_result = preprocessor.process_lightweight(request_data)
        
        if 'error' in preprocessing_result:
            return {
                'error': preprocessing_result['error'],
                'user_id': str(user_id)
            }
        
        user_id_str = str(preprocessing_result['user_id'])
        features = preprocessing_result['features']
        
        predictions = {}
        
        # Quick swiping prediction
        if 'swiping' in features:
            try:
                srp = SwipeRiskPredictor()
                swipe_pred = srp.predict_swipe_risk(user_id_str, features['swiping'])
                if 'error' not in swipe_pred:
                    predictions['swiping'] = {
                        'risk_category': swipe_pred.get('risk_category', 'unknown'),
                        'confidence': swipe_pred.get('confidence', 0),
                        'anomaly_score': swipe_pred.get('anomaly_score', 0)
                    }
            except Exception as e:
                logger.warning(f"Lightweight swipe prediction failed: {str(e)}")
        
        # Quick typing prediction
        if 'typing' in features:
            try:
                trp = TypingRiskPredictor()
                typing_pred = trp.predict_risk(user_id_str, features['typing'])
                if 'error' not in typing_pred:
                    predictions['typing'] = {
                        'risk_category': typing_pred.get('risk_category', 'unknown'),
                        'confidence': typing_pred.get('confidence', 0),
                        'anomaly_score': typing_pred.get('anomaly_score', 0)
                    }
            except Exception as e:
                logger.warning(f"Lightweight typing prediction failed: {str(e)}")
        
        return {
            'user_id': user_id_str,
            'predictions': predictions,
            'timestamp': preprocessing_result['timestamp'],
            'mode': 'lightweight'
        }
        
    except Exception as e:
        logger.error(f"Error in predict_lightweight for user {user_id}: {str(e)}")
        return {
            'error': f'Lightweight prediction failed: {str(e)}',
            'user_id': str(user_id)
        }

def batch_predict(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process multiple prediction requests efficiently
    
    Args:
        requests: List of request dictionaries, each containing:
                 {'user_id': ..., 'data': {...}}
    
    Returns:
        List of prediction results
    """
    try:
        preprocessor = RealtimePreprocessor()
        preprocessor.enable_performance_mode()
        
        # Use batch processing
        results = preprocessor.batch_process_features(requests)
        
        # Add predictions to each result
        final_results = []
        for result in results:
            if 'error' not in result and 'features' in result:
                # Add quick predictions
                user_id = result['user_id']
                features = result['features']
                
                predictions = {}
                
                if 'swiping' in features:
                    try:
                        srp = SwipeRiskPredictor()
                        swipe_pred = srp.predict_swipe_risk(user_id, features['swiping'])
                        if 'error' not in swipe_pred:
                            predictions['swiping'] = {
                                'risk_category': swipe_pred.get('risk_category', 'unknown'),
                                'confidence': swipe_pred.get('confidence', 0)
                            }
                    except:
                        pass
                
                if 'typing' in features:
                    try:
                        trp = TypingRiskPredictor()
                        typing_pred = trp.predict_risk(user_id, features['typing'])
                        if 'error' not in typing_pred:
                            predictions['typing'] = {
                                'risk_category': typing_pred.get('risk_category', 'unknown'),
                                'confidence': typing_pred.get('confidence', 0)
                            }
                    except:
                        pass
                
                result['predictions'] = predictions
            
            final_results.append(result)
        
        return final_results
        
    except Exception as e:
        logger.error(f"Error in batch_predict: {str(e)}")
        return [{'error': f'Batch prediction failed: {str(e)}'}]

# Legacy support functions (backward compatibility)
def flatten_swiping_data(data: dict) -> List[float]:
    """Legacy function - kept for backward compatibility"""
    logger.warning("Using deprecated flatten_swiping_data function")
    return [value[0] if isinstance(value, list) else value for value in data.values()]

def flatten_typing_data(data: dict) -> List[float]:
    """Fixed legacy function for typing data"""
    logger.warning("Using deprecated flatten_typing_data function")
    return [value[0] if isinstance(value, list) else value for value in data.values()]