
from Swiping.model import SwipeModelTrainer
from Typing.model import TypingModelTrainer
from preprocessing.onboarding_preprocessor import OnboardingPreprocessor
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_model(user_id: Any, data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trains models for the given user using onboarding data (15-20 samples)
    
    Args:
        user_id: User identifier
        data_dict: Nested data structure:
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
        Training results for each modality
    """
    try:
        if isinstance(data_dict, dict) and 'swiping' in data_dict:
            # New nested format
            request_data = {
                'user_id': user_id,
                'data': data_dict
            }
        else:
            logger.warning("Using legacy data format, consider updating to nested format")
            request_data = {
                'user_id': user_id,
                'data': data_dict
            }
        
        preprocessor = OnboardingPreprocessor()
        
        preprocessing_result = preprocessor.process_request(request_data)
        
        if 'error' in preprocessing_result:
            return {
                'error': preprocessing_result['error'],
                'user_id': str(user_id),
                'details': preprocessing_result.get('metadata', {})
            }
        
        user_id_str = str(preprocessing_result['user_id'])
        training_data = preprocessing_result['training_data']
        metadata = preprocessing_result['metadata']
        readiness = preprocessing_result['readiness']
        
        response = {
            'user_id': user_id_str,
            'training_results': {},
            'readiness_assessment': readiness,
            'preprocessing_metadata': metadata
        }
        
        if 'swiping' in training_data:
            logger.info(f"Training swipe model for user {user_id_str}")
            
            swipe_trainer = SwipeModelTrainer()
            swipe_df = training_data['swiping']
            
            # Check if we have the new method
            if hasattr(swipe_trainer, 'train_swipe_model_from_dataframe'):
                swipe_result = swipe_trainer.train_swipe_model_from_dataframe(user_id_str, swipe_df)
            else:
                # Fallback: save DataFrame and use old method
                logger.warning("Using fallback training method for swipe model")
                swipe_result = _train_swipe_model_fallback(swipe_trainer, user_id_str, swipe_df, metadata['swiping'])
            
            response['training_results']['swiping'] = swipe_result
            
            if swipe_result.get('success'):
                logger.info(f"Successfully trained swipe model for user {user_id_str}")
            else:
                logger.error(f"Failed to train swipe model for user {user_id_str}: {swipe_result.get('error')}")
        
        # Train typing model if data is available
        if 'typing' in training_data:
            logger.info(f"Training typing model for user {user_id_str}")
            
            typing_trainer = TypingModelTrainer()
            typing_df = training_data['typing']
            
            # Check if we have the new method
            if hasattr(typing_trainer, 'train_typing_model_from_dataframe'):
                typing_result = typing_trainer.train_typing_model_from_dataframe(user_id_str, typing_df)
            else:
                # Fallback: save DataFrame and use old method
                logger.warning("Using fallback training method for typing model")
                typing_result = _train_typing_model_fallback(typing_trainer, user_id_str, typing_df, metadata['typing'])
            
            response['training_results']['typing'] = typing_result
            
            if typing_result.get('success'):
                logger.info(f"Successfully trained typing model for user {user_id_str}")
            else:
                logger.error(f"Failed to train typing model for user {user_id_str}: {typing_result.get('error')}")
        
        # Add overall training summary
        successful_models = [modality for modality, result in response['training_results'].items() 
                           if result.get('success')]
        failed_models = [modality for modality, result in response['training_results'].items() 
                        if not result.get('success')]
        
        response['training_summary'] = {
            'successful_models': successful_models,
            'failed_models': failed_models,
            'total_models_attempted': len(response['training_results']),
            'success_rate': len(successful_models) / len(response['training_results']) if response['training_results'] else 0
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_model for user {user_id}: {str(e)}")
        return {
            'error': f'Training process failed: {str(e)}',
            'user_id': str(user_id)
        }

# QUICK FIX 1: In util_training.py, replace the fallback methods:

def _train_typing_model_fallback(trainer: TypingModelTrainer, user_id: str, df, metadata: Dict) -> Dict:
    """Fixed fallback method for training typing model"""
    try:
        # Just use the DataFrame method directly - no data_dir needed
        result = trainer.train_typing_model_from_dataframe(user_id, df)
        return result
    except Exception as e:
        logger.error(f"Error in typing model fallback training: {str(e)}")
        return {'error': f'Fallback training failed: {str(e)}'}

def _train_swipe_model_fallback(trainer: SwipeModelTrainer, user_id: str, df, metadata: Dict) -> Dict:
    """Fixed fallback method for training swipe model"""
    try:
        # Just use the DataFrame method directly - no data_dir needed  
        result = trainer.train_swipe_model_from_dataframe(user_id, df)
        return result
    except Exception as e:
        logger.error(f"Error in swipe model fallback training: {str(e)}")
        return {'error': f'Fallback training failed: {str(e)}'}

def validate_onboarding_data(user_id: Any, data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate onboarding data without training models
    Useful for checking data quality before training
    """
    try:
        request_data = {
            'user_id': user_id,
            'data': data_dict
        }
        
        preprocessor = OnboardingPreprocessor()
        result = preprocessor.process_request(request_data)
        
        if 'error' in result:
            return {
                'valid': False,
                'error': result['error'],
                'user_id': str(user_id)
            }
        
        return {
            'valid': True,
            'user_id': str(result['user_id']),
            'readiness': result['readiness'],
            'metadata': result['metadata'],
            'sample_counts': {
                modality: data['sample_count'] 
                for modality, data in result['metadata'].items() 
                if isinstance(data, dict) and 'sample_count' in data
            }
        }
        
    except Exception as e:
        logger.error(f"Error validating onboarding data for user {user_id}: {str(e)}")
        return {
            'valid': False,
            'error': f'Validation failed: {str(e)}',
            'user_id': str(user_id)
        }