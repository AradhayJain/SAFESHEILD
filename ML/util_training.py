from typing import Dict, Any
import logging
import sys
import os

# Add the ML directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced model trainers and preprocessor with correct paths
try:
    from swiping.enhanced_swipe_model_trainer import EnhancedSwipeModelTrainer
    from typing.enhanced_typing_model_trainer import EnhancedTypingModelTrainer
    from preprocessing.improved_data_preprocessor import ImprovedDataPreprocessor
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required files are in the correct ML subdirectories")
    sys.exit(1)

logger = logging.getLogger(__name__)

def get_model(user_id: Any, data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced training function with standardized variable handling and cross-validation
    
    Args:
        user_id: User identifier
        data_dict: Raw data from frontend with standardized format
    
    Returns:
        Comprehensive training results with model quality metrics
    """
    try:
        logger.info(f"Starting model training for user {user_id}")
        
        # Initialize preprocessor
        preprocessor = ImprovedDataPreprocessor()
        
        # Process the onboarding data
        processing_result = preprocessor.process_onboarding_data(str(user_id), data_dict)
        
        if 'error' in processing_result:
            return {
                'error': processing_result['error'],
                'user_id': str(user_id),
                'details': processing_result.get('data_quality', {})
            }
        
        user_id_str = str(processing_result['user_id'])
        training_data = processing_result.get('training_data', {})
        data_quality = processing_result.get('data_quality', {})
        
        response = {
            'user_id': user_id_str,
            'training_results': {},
            'data_quality': data_quality,
            'preprocessing_metadata': {
                'timestamp': processing_result['timestamp'],
                'warnings': data_quality.get('warnings', [])
            }
        }
        
        # Train swipe model if data is available
        if 'swiping' in training_data:
            logger.info(f"Training swipe model for user {user_id_str}")
            
            swipe_trainer = EnhancedSwipeModelTrainer()
            swipe_df = training_data['swiping']
            
            swipe_result = swipe_trainer.train_swipe_model_from_dataframe(
                user_id_str, swipe_df, is_onboarding=True
            )
            
            response['training_results']['swiping'] = swipe_result
            
            if swipe_result.get('success'):
                logger.info(f"Successfully trained swipe model for user {user_id_str}")
                logger.info(f"   - Training samples: {swipe_result['metadata']['training_samples']}")
                logger.info(f"   - Outlier rate: {swipe_result['metadata']['outlier_rate']}")
                logger.info(f"   - CV score: {swipe_result['metadata']['cv_score_mean']}")
            else:
                logger.error(f"Failed to train swipe model for user {user_id_str}: {swipe_result.get('error')}")
        
        # Train typing model if data is available
        if 'typing' in training_data:
            logger.info(f"Training typing model for user {user_id_str}")
            
            typing_trainer = EnhancedTypingModelTrainer()
            typing_df = training_data['typing']
            
            typing_result = typing_trainer.train_typing_model_from_dataframe(
                user_id_str, typing_df, is_onboarding=True
            )
            
            response['training_results']['typing'] = typing_result
            
            if typing_result.get('success'):
                logger.info(f"Successfully trained typing model for user {user_id_str}")
                logger.info(f"   - Training samples: {typing_result['metadata']['training_samples']}")
                logger.info(f"   - Outlier rate: {typing_result['metadata']['outlier_rate']}")
                logger.info(f"   - CV score: {typing_result['metadata']['cv_score_mean']}")
                logger.info(f"   - Model quality: {typing_result.get('model_quality', {}).get('confidence', 'unknown')}")
            else:
                logger.error(f"❌ Failed to train typing model for user {user_id_str}: {typing_result.get('error')}")
        
        # Calculate training summary
        successful_models = [modality for modality, result in response['training_results'].items() 
                           if result.get('success')]
        failed_models = [modality for modality, result in response['training_results'].items() 
                        if not result.get('success')]
        
        response['training_summary'] = {
            'successful_models': successful_models,
            'failed_models': failed_models,
            'total_models_attempted': len(response['training_results']),
            'success_rate': len(successful_models) / len(response['training_results']) if response['training_results'] else 0,
            'overall_status': 'success' if successful_models else 'failed',
            'recommendations': _generate_training_recommendations(response)
        }
        
        # Log final summary
        logger.info(f"Training completed for user {user_id_str}:")
        logger.info(f"Successful: {', '.join(successful_models) if successful_models else 'None'}")
        logger.info(f"Failed: {', '.join(failed_models) if failed_models else 'None'}")
        logger.info(f"Success rate: {response['training_summary']['success_rate']:.1%}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_model for user {user_id}: {str(e)}")
        return {
            'error': f'Training process failed: {str(e)}',
            'user_id': str(user_id),
            'training_summary': {
                'successful_models': [],
                'failed_models': [],
                'overall_status': 'error'
            }
        }

def _generate_training_recommendations(training_response: Dict[str, Any]) -> list[str]:
    """Generate recommendations based on training results"""
    recommendations = []
    
    # Check data quality
    data_quality = training_response.get('data_quality', {})
    warnings = data_quality.get('warnings', [])
    
    if warnings:
        recommendations.append("Consider collecting more consistent behavioral data to improve model accuracy")
    
    # Check training results
    training_results = training_response.get('training_results', {})
    
    for modality, result in training_results.items():
        if result.get('success'):
            metadata = result.get('metadata', {})
            cv_score = metadata.get('cv_score_mean', 0)
            outlier_rate = metadata.get('outlier_rate', 0)
            
            if cv_score < -0.3:
                recommendations.append(f"Consider retraining {modality} model with more data for better performance")
            
            if outlier_rate > 0.2:
                recommendations.append(f"{modality.capitalize()} model has high outlier rate - may produce false positives")
            
            if metadata.get('training_samples', 0) < 20:
                recommendations.append(f"Consider collecting more {modality} data for improved model stability")
        else:
            error = result.get('error', '')
            if 'Insufficient data' in error:
                recommendations.append(f"Collect more {modality} behavioral data before training")
            elif 'validation failed' in error:
                recommendations.append(f"Review {modality} data quality - model validation failed")
    
    # Overall recommendations
    successful_models = training_response.get('training_summary', {}).get('successful_models', [])
    
    if len(successful_models) == 0:
        recommendations.append("Unable to train any models - consider extending data collection period")
    elif len(successful_models) == 1:
        recommendations.append("Single modality authentication available - consider collecting additional behavioral data for multi-modal authentication")
    
    return recommendations if recommendations else ["Models trained successfully - ready for behavioral authentication"]

def validate_onboarding_data(user_id: Any, data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced validation function with detailed quality assessment
    """
    try:
        preprocessor = ImprovedDataPreprocessor()
        
        # Process and validate the data
        processing_result = preprocessor.process_onboarding_data(str(user_id), data_dict)
        
        if 'error' in processing_result:
            return {
                'valid': False,
                'error': processing_result['error'],
                'user_id': str(user_id),
                'details': processing_result.get('data_quality', {})
            }
        
        training_data = processing_result.get('training_data', {})
        data_quality = processing_result.get('data_quality', {})
        
        # Calculate readiness metrics
        readiness_metrics = {}
        
        if 'swiping' in training_data:
            swipe_df = training_data['swiping']
            readiness_metrics['swiping'] = {
                'sample_count': len(swipe_df),
                'readiness': 'ready' if len(swipe_df) >= 10 else 'insufficient',
                'quality_score': min(1.0, len(swipe_df) / 20.0)  # Score out of 1.0
            }
        
        if 'typing' in training_data:
            typing_df = training_data['typing']
            readiness_metrics['typing'] = {
                'sample_count': len(typing_df),
                'readiness': 'ready' if len(typing_df) >= 15 else 'insufficient',
                'quality_score': min(1.0, len(typing_df) / 30.0)  # Score out of 1.0
            }
        
        # Overall readiness assessment
        ready_modalities = [mod for mod, metrics in readiness_metrics.items() 
                          if metrics['readiness'] == 'ready']
        
        overall_readiness = 'ready' if ready_modalities else 'insufficient'
        
        return {
            'valid': True,
            'user_id': str(user_id),
            'readiness': overall_readiness,
            'readiness_metrics': readiness_metrics,
            'data_quality': data_quality,
            'recommendations': _generate_validation_recommendations(readiness_metrics, data_quality),
            'estimated_accuracy': _estimate_model_accuracy(readiness_metrics)
        }
        
    except Exception as e:
        logger.error(f"Error validating onboarding data for user {user_id}: {str(e)}")
        return {
            'valid': False,
            'error': f'Validation failed: {str(e)}',
            'user_id': str(user_id)
        }

def _generate_validation_recommendations(readiness_metrics: Dict[str, Any], data_quality: Dict[str, Any]) -> list[str]:
    """Generate recommendations based on validation results"""
    recommendations = []
    
    # Check individual modalities
    for modality, metrics in readiness_metrics.items():
        sample_count = metrics['sample_count']
        quality_score = metrics['quality_score']
        
        if metrics['readiness'] == 'insufficient':
            if modality == 'swiping':
                needed = max(0, 10 - sample_count)
                recommendations.append(f"Need {needed} more swipe samples for {modality} model training")
            elif modality == 'typing':
                needed = max(0, 15 - sample_count)
                recommendations.append(f"Need {needed} more typing samples for {modality} model training")
        
        elif quality_score < 0.7:
            recommendations.append(f"Consider collecting more {modality} data for improved model accuracy")
    
    # Check data quality warnings
    warnings = data_quality.get('warnings', [])
    if warnings:
        recommendations.append("Review data collection process to reduce inconsistencies")
    
    # Overall recommendations
    ready_count = sum(1 for metrics in readiness_metrics.values() if metrics['readiness'] == 'ready')
    
    if ready_count == 0:
        recommendations.append("Continue data collection - no models ready for training yet")
    elif ready_count == 1:
        recommendations.append("One behavioral modality ready - consider collecting additional data for multi-modal authentication")
    else:
        recommendations.append("Multiple behavioral modalities ready - proceed with model training")
    
    return recommendations

def _estimate_model_accuracy(readiness_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate expected model accuracy based on data quantity and quality"""
    accuracy_estimates = {}
    
    for modality, metrics in readiness_metrics.items():
        sample_count = metrics['sample_count']
        quality_score = metrics['quality_score']
        
        # Base accuracy estimation (simplified model)
        if metrics['readiness'] == 'ready':
            # Estimate based on sample count and quality
            base_accuracy = 0.7 + (quality_score * 0.2)  # 70-90% range
            
            # Adjust for sample count
            if sample_count >= 30:
                sample_bonus = 0.05
            elif sample_count >= 20:
                sample_bonus = 0.03
            else:
                sample_bonus = 0.0
            
            estimated_accuracy = min(0.95, base_accuracy + sample_bonus)
            confidence = 'high' if quality_score > 0.8 else 'medium' if quality_score > 0.6 else 'low'
            
            accuracy_estimates[modality] = {
                'estimated_accuracy': round(estimated_accuracy, 3),
                'confidence': confidence,
                'false_positive_rate': round((1 - estimated_accuracy) * 0.3, 3),  # Rough estimate
                'false_negative_rate': round((1 - estimated_accuracy) * 0.7, 3)   # Rough estimate
            }
        else:
            accuracy_estimates[modality] = {
                'estimated_accuracy': None,
                'confidence': 'insufficient_data',
                'false_positive_rate': None,
                'false_negative_rate': None
            }
    
    return accuracy_estimates

def create_test_training_data():
    """Create test data for validating the training pipeline"""
    # This matches the format from your provided sample data
    test_data = {
        "swipeAccelerationsNew": [834.579, 800.845, 670.761, 490.622, 1441.899, 697.718, 557.531, 912.978, 2355.663, 401.021, 1483.464, 1105.083, 1215.515, 1666.873, 734.480, 1673.304, 1076.329, 1569.193, 1194.192, 1187.186, 751.246, 748.514, 1396.704, 1567.123, 1074.371, 2500.717, 4007.878, 2749.018, 1867.806, 2977.871, 208.325, 39.783],
        "swipeDirectionsNew": [79.344, 79.853, 75.492, 332.987, 114.382, 100.574, 339.513, 34.548, 97.125, 326.607, 91.675, 201.970, 12.435, 289.278, 47.956, 99.866, 292.443, 317.065, 353.184, 296.604, 289.348, 316.608, 253.881, 250.729, 326.256, 79.763, 254.337, 289.019, 247.479, 288.222, 283.961, 174.511],
        "swipeDistancesNew": [97.345, 119.198, 127.740, 133.572, 101.740, 127.159, 97.144, 24.687, 32.249, 89.031, 57.024, 126.521, 66.562, 150.435, 100.543, 147.853, 199.078, 124.296, 84.262, 219.582, 92.561, 134.403, 211.307, 144.426, 99.014, 202.558, 139.514, 175.937, 147.949, 141.776, 183.761, 334.534],
        "swipeDurationsNew": [108, 122, 138, 165, 84, 135, 132, 52, 37, 149, 62, 107, 74, 95, 117, 94, 136, 89, 84, 136, 111, 134, 123, 96, 96, 90, 59, 80, 89, 69, 297, 917],
        "swipeSpeedsNew": [0.901, 0.977, 0.926, 0.810, 1.211, 0.942, 0.736, 0.475, 0.872, 0.598, 0.920, 1.182, 0.899, 1.584, 0.859, 1.573, 1.464, 1.397, 1.003, 1.615, 0.834, 1.003, 1.718, 1.504, 1.031, 2.251, 2.365, 2.199, 1.662, 2.055, 0.619, 0.365],
        "backspaceRatesNew": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.053, 0.1, 0.143, 0.182, 0.217, 0.25, 0.28, 0.308, 0.333, 0.357, 0.379, 0.367, 0.355, 0.344, 0.333, 0.324, 0.314, 0.306, 0.297, 0.289, 0.282, 0.275, 0.293, 0.310, 0.326, 0.341, 0.356, 0.370, 0.383, 0.396, 0.408, 0.420, 0.431, 0.442, 0.453, 0.463, 0.473, 0.464, 0.456, 0.448, 0.441],
        "flightTimesNew": [156, 199, 182, 212, 202, 160, 236, 164, 211, 148, 182, 129, 199, 142, 133, 367, 145, 354, 190, 194, 179, 147, 174, 167, 194, 177, 181, 181, 218, 162, 144, 234, 241, 250, 198, 173, 125, 333, 246, 746, 177, 193, 183, 213, 167, 179, 194, 171, 217, 199, 183, 191, 175, 196, 1911, 153, 187, 416],
        "holdTimesNew": [183, 218, 199, 231, 217, 182, 252, 181, 236, 163, 202, 148, 217, 167, 149, 383, 167, 376, 206, 217, 199, 167, 200, 182, 217, 199, 201, 199, 236, 181, 166, 250, 266, 266, 218, 199, 151, 349, 265, 767, 200, 216, 200, 233, 183, 200, 216, 200, 233, 216, 200, 217, 200, 216, 168, 214, 433],
        "typingSpeedsNew": [444.444, 118.812, 86.124, 77.544, 70.922, 67.290, 67.416, 64.043, 63.981, 62.696, 63.401, 63.075, 64.198, 63.301, 64.011, 64.843, 60.896, 61.416, 58.657, 58.537, 58.414, 58.498, 58.899, 59.077, 59.230, 59.080, 59.146, 59.186, 59.224, 58.891, 59.076, 59.470, 58.964, 58.511, 57.987, 57.855, 57.918, 58.409, 57.360, 56.967, 53.507, 53.646, 53.722, 53.834, 53.801, 53.985, 54.096, 54.090, 54.264, 54.201, 54.226, 54.284, 54.308, 54.426, 54.442, 47.833, 48.071, 48.223, 47.609]
    }
    
    return test_data

def test_enhanced_training_pipeline():
    """Test the complete enhanced training pipeline"""
    print("Testing Enhanced Training Pipeline with Cross-Validation")
    print("=" * 70)
    
    # Create test data
    test_data = create_test_training_data()
    test_user_id = "test_user_enhanced_001"
    
    print(f"\nTest data summary:")
    for key, values in test_data.items():
        if isinstance(values, list):
            print(f"  {key}: {len(values)} samples")
    
    # Test validation
    print(f"\nStep 1: Validating training data...")
    validation_result = validate_onboarding_data(test_user_id, test_data)
    
    if validation_result['valid']:
        print(f"Data validation passed")
        print(f"   Readiness: {validation_result['readiness']}")
        print(f"   Available modalities: {list(validation_result['readiness_metrics'].keys())}")
        
        for modality, metrics in validation_result['readiness_metrics'].items():
            print(f"   {modality}: {metrics['sample_count']} samples, quality: {metrics['quality_score']:.2f}")
    else:
        print(f"Data validation failed: {validation_result['error']}")
        return
    
    # Test training
    print(f"\nStep 2: Training models...")
    training_result = get_model(test_user_id, test_data)
    
    if 'error' not in training_result:
        print(f"Training completed")
        print(f"   User ID: {training_result['user_id']}")
        print(f"   Overall status: {training_result['training_summary']['overall_status']}")
        print(f"   Success rate: {training_result['training_summary']['success_rate']:.1%}")
        
        # Show detailed results
        for modality, result in training_result['training_results'].items():
            if result.get('success'):
                metadata = result['metadata']
                print(f" {modality.capitalize()}: Trained successfully")
                print(f"      - Samples: {metadata['training_samples']}")
                print(f"      - Outlier rate: {metadata['outlier_rate']:.3f}")
                print(f"      - CV score: {metadata['cv_score_mean']:.3f} ± {metadata['cv_score_std']:.3f}")
                if 'model_quality' in result:
                    quality = result['model_quality']
                    print(f"      - Quality: {quality.get('confidence', 'unknown')}")
            else:
                print(f"   ❌ {modality.capitalize()}: {result.get('error', 'Unknown error')}")
        
        # Show recommendations
        recommendations = training_result['training_summary'].get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
    else:
        print(f"❌ Training failed: {training_result['error']}")
    
    print(f"\n" + "=" * 70)
    return training_result

if __name__ == "__main__":
    # Run the test
    test_enhanced_training_pipeline()
