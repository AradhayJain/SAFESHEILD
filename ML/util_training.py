# util_training.py - TRAINING utilities (NOT prediction)
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required modules with error handling
try:
    from preprocessing.improved_data_preprocessor import ImprovedDataPreprocessor
    from swiping.enhanced_swipe_model_trainer import EnhancedSwipeModelTrainer
    from typing_models.enhanced_typing_model_trainer import EnhancedTypingModelTrainer
    logger.info("✅ All training modules imported successfully")
except ImportError as e:
    logger.error(f"❌ Error importing training modules: {e}")
    raise

def validate_onboarding_data(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate onboarding data and assess readiness for training
    
    Args:
        user_id: User identifier
        data: Raw behavioral data
    
    Returns:
        Dictionary with validation results and readiness assessment
    """
    try:
        logger.info(f"🔍 Validating onboarding data for user: {user_id}")
        
        preprocessor = ImprovedDataPreprocessor()
        
        # Process the data for training
        result = preprocessor.process_onboarding_data(user_id, data)
        
        if 'error' in result:
            return {
                'valid': False,
                'error': result['error'],
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
        
        # Extract readiness assessment
        readiness = result.get('readiness_assessment', {})
        training_data = result.get('training_data', {})
        
        # Determine overall readiness
        ready_modalities = []
        readiness_metrics = {}
        
        for modality, assessment in readiness.get('modalities', {}).items():
            readiness_level = assessment.get('readiness', 'insufficient')
            readiness_metrics[modality] = {
                'readiness': readiness_level,
                'sample_count': assessment.get('sample_count', 0),
                'available': assessment.get('available', False)
            }
            
            if readiness_level in ['minimal', 'good', 'excellent']:
                ready_modalities.append(modality)
        
        overall_readiness = 'ready' if ready_modalities else 'insufficient'
        processing_mode = readiness.get('processing_mode', 'onboarding')
        
        return {
            'valid': True,
            'readiness': overall_readiness,
            'processing_mode': processing_mode,
            'ready_modalities': ready_modalities,
            'readiness_metrics': readiness_metrics,
            'training_data_available': bool(training_data),
            'recommendations': readiness.get('recommendations', []),
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error validating onboarding data for {user_id}: {str(e)}")
        return {
            'valid': False,
            'error': f'Validation failed: {str(e)}',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }

def get_model(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main training function - processes data and trains behavioral models
    
    Args:
        user_id: User identifier  
        data: Raw behavioral data from frontend
    
    Returns:
        Dictionary with training results and model information
    """
    try:
        logger.info(f"🚀 Starting model training for user: {user_id}")
        
        # Initialize preprocessor
        preprocessor = ImprovedDataPreprocessor()
        
        # Process the data for training
        processed_result = preprocessor.process_onboarding_data(user_id, data)
        
        if 'error' in processed_result:
            logger.error(f"❌ Preprocessing failed for user {user_id}: {processed_result['error']}")
            return {
                'error': processed_result['error'],
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
        
        training_data = processed_result.get('training_data', {})
        readiness_assessment = processed_result.get('readiness_assessment', {})
        
        if not training_data:
            return {
                'error': 'No training data available after preprocessing',
                'readiness_assessment': readiness_assessment,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
        
        logger.info(f"📊 Training data available for user {user_id}: {list(training_data.keys())}")
        
        # Initialize trainers
        swipe_trainer = EnhancedSwipeModelTrainer()
        typing_trainer = EnhancedTypingModelTrainer()
        
        # Track training results
        training_results = {}
        successful_models = []
        failed_models = []
        
        # Train swipe model if data is available
        if 'swiping' in training_data:
            logger.info(f"🎯 Training swipe model for user: {user_id}")
            
            try:
                swipe_df = training_data['swiping']
                is_onboarding = readiness_assessment.get('processing_mode') in ['onboarding', 'minimal_onboarding']
                
                logger.info(f"   Swipe training data shape: {swipe_df.shape}")
                logger.info(f"   Swipe training mode: {'onboarding' if is_onboarding else 'full'}")
                
                swipe_result = swipe_trainer.train_swipe_model_from_dataframe(
                    user_id, swipe_df, is_onboarding=is_onboarding
                )
                
                training_results['swiping'] = swipe_result
                
                if swipe_result.get('success'):
                    successful_models.append('swiping')
                    logger.info(f"✅ Swipe model training successful for user: {user_id}")
                else:
                    failed_models.append('swiping')
                    logger.warning(f"⚠️ Swipe model training failed for user {user_id}: {swipe_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ Swipe model training error for user {user_id}: {str(e)}")
                training_results['swiping'] = {'error': str(e)}
                failed_models.append('swiping')
        
        # Train typing model if data is available
        if 'typing' in training_data:
            logger.info(f"⌨️ Training typing model for user: {user_id}")
            
            try:
                typing_df = training_data['typing']
                is_onboarding = readiness_assessment.get('processing_mode') in ['onboarding', 'minimal_onboarding']
                
                logger.info(f"   Typing training data shape: {typing_df.shape}")
                logger.info(f"   Typing training mode: {'onboarding' if is_onboarding else 'full'}")
                
                typing_result = typing_trainer.train_typing_model_from_dataframe(
                    user_id, typing_df, is_onboarding=is_onboarding
                )
                
                training_results['typing'] = typing_result
                
                if typing_result.get('success'):
                    successful_models.append('typing')
                    logger.info(f"✅ Typing model training successful for user: {user_id}")
                else:
                    failed_models.append('typing')
                    logger.warning(f"⚠️ Typing model training failed for user {user_id}: {typing_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ Typing model training error for user {user_id}: {str(e)}")
                training_results['typing'] = {'error': str(e)}
                failed_models.append('typing')
        
        # Compile final results
        success_rate = len(successful_models) / len(training_results) if training_results else 0
        overall_status = 'success' if successful_models else 'failed'
        
        if successful_models and failed_models:
            overall_status = 'partial_success'
        
        final_result = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'training_summary': {
                'overall_status': overall_status,
                'successful_models': successful_models,
                'failed_models': failed_models,
                'success_rate': success_rate,
                'total_models_attempted': len(training_results)
            },
            'training_results': training_results,
            'readiness_assessment': readiness_assessment,
            'data_quality': processed_result.get('data_quality', {}),
        }
        
        # Add model paths if successful
        if successful_models:
            model_paths = {}
            for modality in successful_models:
                result = training_results[modality]
                if 'model_path' in result:
                    model_paths[modality] = result['model_path']
            
            if model_paths:
                final_result['model_paths'] = model_paths
        
        logger.info(f"🎉 Training completed for user {user_id}: {overall_status} ({len(successful_models)}/{len(training_results)} models)")
        
        return final_result
        
    except Exception as e:
        logger.error(f"❌ Critical error in model training for user {user_id}: {str(e)}")
        return {
            'error': f'Training pipeline failed: {str(e)}',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }

def train_individual_models(user_id: str, processed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Train individual models from already processed data
    
    Args:
        user_id: User identifier
        processed_data: Already processed training data (DataFrames)
    
    Returns:
        Dictionary with training results
    """
    try:
        swipe_trainer = EnhancedSwipeModelTrainer()
        typing_trainer = EnhancedTypingModelTrainer()
        
        results = {}
        
        if 'swiping' in processed_data:
            results['swiping'] = swipe_trainer.train_swipe_model_from_dataframe(
                user_id, processed_data['swiping']
            )
        
        if 'typing' in processed_data:
            results['typing'] = typing_trainer.train_typing_model_from_dataframe(
                user_id, processed_data['typing']
            )
        
        return {
            'user_id': user_id,
            'training_results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in individual model training for user {user_id}: {str(e)}")
        return {
            'error': str(e),
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }

def check_training_prerequisites() -> Dict[str, Any]:
    """
    Check if all training prerequisites are met
    
    Returns:
        Dictionary with prerequisite check results
    """
    try:
        checks = {
            'models_directory': os.path.exists('./models'),
            'preprocessor_available': True,
            'swipe_trainer_available': True,
            'typing_trainer_available': True
        }
        
        # Create models directory if it doesn't exist
        if not checks['models_directory']:
            os.makedirs('./models', exist_ok=True)
            checks['models_directory'] = True
            logger.info("📁 Created models directory")
        
        # Test if trainers can be instantiated
        try:
            ImprovedDataPreprocessor()
        except Exception:
            checks['preprocessor_available'] = False
        
        try:
            EnhancedSwipeModelTrainer()
        except Exception:
            checks['swipe_trainer_available'] = False
        
        try:
            EnhancedTypingModelTrainer()
        except Exception:
            checks['typing_trainer_available'] = False
        
        all_checks_passed = all(checks.values())
        
        return {
            'ready': all_checks_passed,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking training prerequisites: {str(e)}")
        return {
            'ready': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Legacy function aliases for backward compatibility
train_model = get_model  # Alias for the main function

if __name__ == "__main__":
    # Test the training utilities
    print("🧪 Testing Training Utilities")
    print("=" * 50)
    
    # Check prerequisites
    prereq_result = check_training_prerequisites()
    print(f"Prerequisites check: {'✅ PASSED' if prereq_result['ready'] else '❌ FAILED'}")
    
    if not prereq_result['ready']:
        print("❌ Prerequisites not met:")
        for check, result in prereq_result['checks'].items():
            print(f"   {check}: {'✅' if result else '❌'}")
    else:
        print("✅ All prerequisites met - training system ready!")
        
        # Test with sample data
        sample_data = {
            "swipeSpeedsNew": [1.2, 0.8, 1.5, 0.9, 1.1],
            "swipeDirectionsNew": [85.5, 92.3, 78.1, 88.2, 95.1],
            "swipeAccelerationsNew": [750.0, 820.5, 690.2, 770.8, 800.1],
            "holdTimesNew": [180, 195, 170, 185, 175, 190, 165],
            "flightTimesNew": [220, 180, 200, 210, 190, 205, 175],
            "backspaceRatesNew": [0.05, 0.08, 0.03, 0.06, 0.04, 0.07, 0.02],
            "typingSpeedsNew": [65.5, 62.8, 68.2, 64.1, 66.3, 63.7, 67.9]
        }
        
        print("\n🔍 Testing data validation...")
        validation_result = validate_onboarding_data("test_user", sample_data)
        print(f"Validation: {'✅ PASSED' if validation_result['valid'] else '❌ FAILED'}")
        
        if validation_result['valid']:
            print(f"   Readiness: {validation_result['readiness']}")
            print(f"   Ready modalities: {validation_result['ready_modalities']}")
            
            print("\n🎯 Testing model training...")
            training_result = get_model("test_user", sample_data)
            
            if 'error' not in training_result:
                print("✅ Training successful!")
                summary = training_result['training_summary']
                print(f"   Status: {summary['overall_status']}")
                print(f"   Successful models: {summary['successful_models']}")
                print(f"   Success rate: {summary['success_rate']:.1%}")
            else:
                print(f"❌ Training failed: {training_result['error']}")
        else:
            print(f"❌ Validation failed: {validation_result['error']}")