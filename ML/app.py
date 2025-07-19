# app.py - Complete Flask Server with Training AND Prediction
from flask import Flask, request, jsonify
import sys
import os
import logging
from datetime import datetime

# Add the current directory to Python path to find local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Try to import the training utility with error handling
try:
    # Try different possible import paths
    try:
        from ML.util_training import get_model
        from ML.util_predict import predict_with_model
        logger.info("✅ Successfully imported from ML.util_training and ML.util_predict")
    except ImportError:
        try:
            from util_training import get_model
            from util_predict import predict_with_model
            logger.info("✅ Successfully imported from util_training and util_predict")
        except ImportError:
            # If both fail, create a fallback function
            logger.warning("⚠️ Could not import training/prediction utilities, using fallback")
            def get_model(user_id, features):
                return {
                    "error": "Training service not available",
                    "message": "util_training module not found. Please ensure ML utilities are properly installed.",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
            def predict_with_model(user_id, features):
                return {
                    "error": "Prediction service not available",
                    "message": "util_predict module not found. Please ensure ML utilities are properly installed.",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
except Exception as e:
    logger.error(f"❌ Error importing utilities: {str(e)}")
    def get_model(user_id, features):
        return {
            "error": "Training service initialization failed",
            "message": str(e),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    def predict_with_model(user_id, features):
        return {
            "error": "Prediction service initialization failed",
            "message": str(e),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }

def flatten_nested_data(nested_data):
    """
    Flatten nested data structure to match expected preprocessing format
    
    Input: {"typing": {"holdTimesNew": [...]}, "swiping": {"swipeSpeedsNew": [...]}}
    Output: {"holdTimesNew": [...], "swipeSpeedsNew": [...]}
    """
    flattened = {}
    
    if isinstance(nested_data, dict):
        for modality, modality_data in nested_data.items():
            if isinstance(modality_data, dict):
                # If it's nested (typing/swiping structure), flatten it
                for field, values in modality_data.items():
                    flattened[field] = values
                    logger.debug(f"Flattened {modality}.{field} -> {field}")
            else:
                # If it's already flat, keep as is
                flattened[modality] = modality_data
    else:
        # If it's not a dict, return as is
        return nested_data
    
    return flattened

def validate_and_debug_data(data, user_id):
    """
    Validate data and provide detailed debugging information
    """
    logger.info(f"🔍 Debugging data for user: {user_id}")
    logger.info(f"📊 Raw data type: {type(data)}")
    logger.info(f"📊 Raw data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    
    # Check if data is nested
    if isinstance(data, dict):
        for key, value in data.items():
            logger.info(f"   {key}: {type(value)} - {list(value.keys()) if isinstance(value, dict) else f'Length: {len(value) if hasattr(value, "__len__") else "N/A"}'}")
            
            # If it's nested, show the inner structure
            if isinstance(value, dict):
                for inner_key, inner_value in value.items():
                    sample_data = inner_value[:3] if isinstance(inner_value, list) and len(inner_value) > 3 else inner_value
                    logger.info(f"     {inner_key}: {type(inner_value)} - Sample: {sample_data}")
    
    return True

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "message": "ML Training & Prediction API is up and running!",
        "status": "healthy",
        "endpoints": {
            "training": "/train_model",
            "prediction": "/predict_model",
            "health": "/health",
            "debug": "/debug_prediction_data"
        },
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/health')
def health_check():
    """Detailed health check"""
    try:
        # Test if training function is available
        test_result = get_model("health_check", {"holdTimesNew": [100, 120, 95]})
        training_available = "error" not in test_result or "not available" not in test_result.get("error", "")
        
        # Test if prediction function is available
        pred_result = predict_with_model("health_check", {"holdTimesNew": [100, 120, 95]})
        prediction_available = "error" not in pred_result or "not available" not in pred_result.get("error", "")
    except:
        training_available = False
        prediction_available = False
    
    return jsonify({
        "status": "healthy",
        "training_service": "available" if training_available else "unavailable",
        "prediction_service": "available" if prediction_available else "unavailable",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/train_model', methods=['POST'])
def train_model():
    """Train behavioral authentication model for a user"""
    try:
        logger.info("📥 Received training request")
        
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "code": "INVALID_CONTENT_TYPE"
            }), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "code": "NO_DATA"
            }), 400

        # Extract required fields
        user_id = data.get("user_id")
        raw_features = data.get("data")
        print(raw_features)

        # Validate required fields
        if not user_id:
            logger.warning("⚠️ Training request missing user_id")
            return jsonify({
                "error": "Missing user_id in request",
                "code": "MISSING_USER_ID"
            }), 400

        if not raw_features:
            logger.warning("⚠️ Training request missing data")
            return jsonify({
                "error": "Missing data in request", 
                "code": "MISSING_DATA"
            }), 400

        # Debug the received data
        validate_and_debug_data(raw_features, user_id)
        
        # **CRITICAL FIX**: Flatten nested data structure
        logger.info("🔧 Flattening nested data structure...")
        flattened_features = flatten_nested_data(raw_features)
        
        logger.info(f"📊 Original structure: {list(raw_features.keys()) if isinstance(raw_features, dict) else 'Not a dict'}")
        logger.info(f"📊 Flattened structure: {list(flattened_features.keys()) if isinstance(flattened_features, dict) else 'Not a dict'}")
        
        # Log data samples for debugging
        if isinstance(flattened_features, dict):
            for field, values in flattened_features.items():
                if isinstance(values, list):
                    sample = values[:3] if len(values) > 3 else values
                    logger.info(f"   {field}: {len(values)} samples, example: {sample}")
                else:
                    logger.info(f"   {field}: {type(values)} = {values}")

        # Log what we're sending to training
        logger.info(f"🔧 Processing training for user: {user_id}")
        logger.info(f"📊 Features being sent to training: {list(flattened_features.keys())}")

        # Call the training function with flattened data
        try:
            model_result = get_model(user_id, flattened_features)
            logger.info(f"✅ Training call completed for user: {user_id}")

            # Check if training was successful
            if isinstance(model_result, dict) and "error" in model_result:
                logger.error(f"❌ Training failed for user {user_id}: {model_result.get('error')}")
                
                # Provide more detailed error information
                error_details = {
                    "error": model_result.get("error"),
                    "message": model_result.get("message", "Training failed"),
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "debug_info": {
                        "received_fields": list(raw_features.keys()) if isinstance(raw_features, dict) else "Not a dict",
                        "flattened_fields": list(flattened_features.keys()) if isinstance(flattened_features, dict) else "Not a dict",
                        "data_samples": {
                            field: len(values) if isinstance(values, list) else type(values).__name__
                            for field, values in (flattened_features.items() if isinstance(flattened_features, dict) else [])
                        }
                    }
                }
                
                return jsonify(error_details), 500
            else:
                logger.info(f"✅ Training completed successfully for user: {user_id}")
                return jsonify({
                    "message": "Model training completed successfully",
                    "user_id": user_id,
                    "model_info": model_result,
                    "timestamp": datetime.now().isoformat(),
                    "data_processed": {
                        "original_structure": list(raw_features.keys()) if isinstance(raw_features, dict) else "Not a dict",
                        "flattened_fields": list(flattened_features.keys()) if isinstance(flattened_features, dict) else "Not a dict"
                    }
                }), 200
                
        except Exception as training_error:
            logger.error(f"❌ Training error for user {user_id}: {str(training_error)}")
            return jsonify({
                "error": "Training process failed",
                "details": str(training_error),
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "debug_info": {
                    "flattened_data_fields": list(flattened_features.keys()) if isinstance(flattened_features, dict) else "Not a dict"
                }
            }), 500

    except Exception as e:
        logger.error(f"❌ Unexpected error in training endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/predict_model', methods=['POST'])
def predict_model():
    """Make predictions using trained behavioral authentication models"""
    try:
        logger.info("📥 Received prediction request")
        
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                "error": "Content-Type must be application/json",
                "code": "INVALID_CONTENT_TYPE"
            }), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "code": "NO_DATA"
            }), 400

        # Extract required fields
        user_id = data.get("user_id")
        raw_features = data.get("data")

        # Validate required fields
        if not user_id:
            logger.warning("⚠️ Prediction request missing user_id")
            return jsonify({
                "error": "Missing user_id in request",
                "code": "MISSING_USER_ID"
            }), 400

        if not raw_features:
            logger.warning("⚠️ Prediction request missing data")
            return jsonify({
                "error": "Missing data in request", 
                "code": "MISSING_DATA"
            }), 400

        # Flatten nested data structure (same as training)
        logger.info("🔧 Flattening nested data structure for prediction...")
        flattened_features = flatten_nested_data(raw_features)
        
        logger.info(f"📊 Prediction data for user: {user_id}")
        logger.info(f"📊 Flattened fields: {list(flattened_features.keys())}")

        # Make prediction
        try:
            prediction_result = predict_with_model(user_id, flattened_features)
            logger.info(f"✅ Prediction completed for user: {user_id}")

            if 'error' in prediction_result:
                logger.error(f"❌ Prediction failed for user {user_id}: {prediction_result.get('error')}")
                return jsonify({
                    "result": prediction_result,
                    "timestamp": datetime.now().isoformat()
                }), 200  # Return 200 but with error in result
            else:
                logger.info(f"✅ Prediction successful for user: {user_id}")
                return jsonify({
                    "result": prediction_result,
                    "timestamp": datetime.now().isoformat()
                }), 200
                
        except Exception as prediction_error:
            logger.error(f"❌ Prediction error for user {user_id}: {str(prediction_error)}")
            return jsonify({
                "result": {
                    "error": "Prediction process failed",
                    "details": str(prediction_error),
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
            }), 200

    except Exception as e:
        logger.error(f"❌ Unexpected error in prediction endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/debug_prediction_data', methods=['POST'])
def debug_prediction_data():
    """Debug prediction data processing"""
    try:
        data = request.get_json()
        user_id = data.get("user_id", "debug_user")
        raw_features = data.get("data", {})
        
        # Step 1: Flatten
        flattened = flatten_nested_data(raw_features)
        
        # Step 2: Check if preprocessor is available
        try:
            from preprocessing.improved_data_preprocessor import ImprovedDataPreprocessor
            preprocessor = ImprovedDataPreprocessor()
            
            # Step 3: Standardize
            standardized = preprocessor.standardize_input_data(flattened)
            
            # Step 4: Quick feature check
            feature_check = preprocessor.quick_feature_check(standardized)
            
            # Step 5: Check for trained models
            import os
            models_dir = './models'
            user_models = []
            if os.path.exists(models_dir):
                for file in os.listdir(models_dir):
                    if file.startswith(f"{user_id}_") and file.endswith("_model.pkl"):
                        user_models.append(file)
            
            return jsonify({
                "user_id": user_id,
                "debug_steps": {
                    "1_original_data": {
                        "structure": list(raw_features.keys()) if isinstance(raw_features, dict) else "Not a dict",
                        "sample_lengths": {
                            key: len(value) if hasattr(value, '__len__') else type(value).__name__
                            for key, value in raw_features.items()
                        } if isinstance(raw_features, dict) else {}
                    },
                    "2_flattened_data": {
                        "keys": list(flattened.keys()),
                        "sample_lengths": {
                            key: len(value) if hasattr(value, '__len__') else type(value).__name__
                            for key, value in flattened.items()
                        }
                    },
                    "3_standardized_data": {
                        "keys": list(standardized.keys()),
                        "sample_lengths": {
                            key: len(value) if hasattr(value, '__len__') else type(value).__name__
                            for key, value in standardized.items()
                        }
                    },
                    "4_feature_availability": feature_check,
                    "5_trained_models": {
                        "available_models": user_models,
                        "models_directory_exists": os.path.exists(models_dir),
                        "has_typing_model": f"{user_id}_typing_model.pkl" in user_models,
                        "has_swipe_model": f"{user_id}_swipe_model.pkl" in user_models
                    }
                },
                "timestamp": datetime.now().isoformat()
            }), 200
            
        except Exception as prep_error:
            return jsonify({
                "error": "Preprocessor debug failed",
                "details": str(prep_error),
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": "Debug endpoint failed",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test_data_format', methods=['POST'])
def test_data_format():
    """
    Test endpoint to debug data format issues
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id", "test_user")
        raw_features = data.get("data", {})
        
        # Debug the data
        validate_and_debug_data(raw_features, user_id)
        flattened_features = flatten_nested_data(raw_features)
        
        # Check data with preprocessor
        try:
            from preprocessing.improved_data_preprocessor import ImprovedDataPreprocessor
            preprocessor = ImprovedDataPreprocessor()
            
            # Test quick feature check
            feature_check = preprocessor.quick_feature_check(flattened_features)
            
            return jsonify({
                "user_id": user_id,
                "original_data": {
                    "type": type(raw_features).__name__,
                    "keys": list(raw_features.keys()) if isinstance(raw_features, dict) else "Not a dict"
                },
                "flattened_data": {
                    "type": type(flattened_features).__name__,
                    "keys": list(flattened_features.keys()) if isinstance(flattened_features, dict) else "Not a dict"
                },
                "feature_availability": feature_check,
                "timestamp": datetime.now().isoformat()
            }), 200
            
        except Exception as prep_error:
            return jsonify({
                "error": "Preprocessor test failed",
                "details": str(prep_error),
                "flattened_data": flattened_features,
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": "Test endpoint failed",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "Available endpoints: /, /health, /train_model, /predict_model, /debug_prediction_data, /test_data_format",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    print("🚀 Starting ML Training & Prediction Server...")
    print("🌐 Training endpoint: http://localhost:5000/train_model")
    print("🔮 Prediction endpoint: http://localhost:5000/predict_model")
    print("🧪 Debug endpoint: http://localhost:5000/debug_prediction_data")
    print("🩺 Health check: http://localhost:5000/health")
    print("📝 Send POST requests with JSON data to endpoints")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )