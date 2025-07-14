import sys
import os
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add the ML directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from swiping.predict_swipe_risk import SwipeRiskPredictor
    from swiping.update_model import SwipeModelUpdater 
    from typing_models.predict_typing_risk import TypingRiskPredictor  # Updated import
    from typing_models.update_model import TypingModelUpdater  # Updated import
    from preprocessing.improved_data_preprocessor import ImprovedDataPreprocessor
except ImportError as e:
    print(f"Import error in util_predict: {e}")
    print("Please ensure all prediction modules are in the correct ML subdirectories")
    sys.exit(1)

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
        data_dict: Data from frontend with standardized format
    
    Returns:
        Prediction results for each available modality
    """
    try:
        logger.info(f"Starting prediction for user {user_id}")
        
        # Initialize preprocessor
        preprocessor = ImprovedDataPreprocessor()
        
        # Process data for prediction
        processing_result = preprocessor.process_for_realtime_prediction(str(user_id), data_dict)
        
        if 'error' in processing_result:
            return {
                'error': processing_result['error'],
                'user_id': str(user_id),
                'timestamp': processing_result.get('timestamp'),
                'details': processing_result.get('data_quality', {})
            }
        
        user_id_str = str(processing_result['user_id'])
        features = processing_result['features']
        metadata = processing_result['data_quality']
        
        response = {
            'user_id': user_id_str,
            'timestamp': processing_result['timestamp'],
            'predictions': {},
            'processing_metadata': metadata
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
        else:
            response['prediction_summary'] = {
                'overall_risk': 'no_predictions',
                'average_confidence': 0,
                'modalities_analyzed': [],
                'individual_risks': {},
                'message': 'No valid predictions could be made'
            }
        
        logger.info(f"Prediction completed for user {user_id_str}: {response['prediction_summary']['overall_risk']}")
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
        data_dict: Data structure (same as predict_with_model)
    
    Returns:
        Simplified prediction results
    """
    try:
        # Initialize preprocessor
        preprocessor = ImprovedDataPreprocessor()
        
        # Process data for prediction (lightweight mode)
        processing_result = preprocessor.process_for_realtime_prediction(str(user_id), data_dict)
        
        if 'error' in processing_result:
            return {
                'error': processing_result['error'],
                'user_id': str(user_id)
            }
        
        user_id_str = str(processing_result['user_id'])
        features = processing_result['features']
        
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
            'timestamp': processing_result['timestamp'],
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
        results = []
        
        for request in requests:
            user_id = request.get('user_id')
            data_dict = request.get('data', {})
            
            if not user_id:
                results.append({'error': 'Missing user_id in request'})
                continue
            
            # Process each request using lightweight prediction
            result = predict_lightweight(user_id, data_dict)
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch_predict: {str(e)}")
        return [{'error': f'Batch prediction failed: {str(e)}'}]

def create_test_prediction_data():
    """Create test data for prediction testing"""
    return {
        "swipeSpeedsNew": [1.2, 0.8, 1.5],
        "swipeDirectionsNew": [85.5, 92.3, 78.1],
        "swipeAccelerationsNew": [750.0, 820.5, 690.2],
        "holdTimesNew": [180, 195, 170],
        "flightTimesNew": [220, 180, 200],
        "backspaceRatesNew": [0.05, 0.08, 0.03],
        "typingSpeedsNew": [65.5, 62.8, 68.2]
    }

def test_prediction_pipeline():
    """Test the prediction pipeline with sample data"""
    print("Testing Enhanced Prediction Pipeline")
    print("=" * 50)
    
    # Create test data
    test_data = create_test_prediction_data()
    test_user_id = "test_predict_user_001"
    
    print(f"\nTest prediction data:")
    for key, values in test_data.items():
        if isinstance(values, list):
            print(f"  {key}: {len(values)} samples")
    
    # Test full prediction
    print(f"\nTesting full prediction...")
    prediction_result = predict_with_model(test_user_id, test_data)
    
    if 'error' not in prediction_result:
        print(f"✅ Prediction successful")
        print(f"   User ID: {prediction_result['user_id']}")
        
        if 'prediction_summary' in prediction_result:
            summary = prediction_result['prediction_summary']
            print(f"   Overall risk: {summary.get('overall_risk', 'unknown')}")
            print(f"   Confidence: {summary.get('average_confidence', 0):.2f}")
            print(f"   Modalities: {', '.join(summary.get('modalities_analyzed', []))}")
        
        # Show individual predictions
        for modality, result in prediction_result.get('predictions', {}).items():
            if result.get('status') == 'success':
                pred = result['prediction_result']
                print(f"   ✅ {modality.capitalize()}: {pred.get('risk_category', 'unknown')} "
                      f"(confidence: {pred.get('confidence', 0):.2f})")
            else:
                print(f"   ❌ {modality.capitalize()}: {result.get('prediction_result', {}).get('error', 'Unknown error')}")
    else:
        print(f"❌ Prediction failed: {prediction_result['error']}")
    
    # Test lightweight prediction
    print(f"\nTesting lightweight prediction...")
    lightweight_result = predict_lightweight(test_user_id, test_data)
    
    if 'error' not in lightweight_result:
        print(f"✅ Lightweight prediction successful")
        print(f"   Mode: {lightweight_result.get('mode', 'unknown')}")
        for modality, pred in lightweight_result.get('predictions', {}).items():
            print(f"   {modality.capitalize()}: {pred.get('risk_category', 'unknown')} "
                  f"(confidence: {pred.get('confidence', 0):.2f})")
    else:
        print(f"❌ Lightweight prediction failed: {lightweight_result['error']}")
    
    print(f"\n" + "=" * 50)
    return prediction_result, lightweight_result

# Legacy support functions (backward compatibility)
def flatten_swiping_data(data: dict) -> List[float]:
    """Legacy function - kept for backward compatibility"""
    logger.warning("Using deprecated flatten_swiping_data function")
    return [value[0] if isinstance(value, list) else value for value in data.values()]

def flatten_typing_data(data: dict) -> List[float]:
    """Legacy function - kept for backward compatibility"""
    logger.warning("Using deprecated flatten_typing_data function")
    return [value[0] if isinstance(value, list) else value for value in data.values()]

if __name__ == "__main__":
    # Run the test
    test_prediction_pipeline()