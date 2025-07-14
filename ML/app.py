# app.py - Flask Training Server
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
        logger.info("✅ Successfully imported from ML.util_training")
    except ImportError:
        try:
            from util_training import get_model
            logger.info("✅ Successfully imported from util_training")
        except ImportError:
            # If both fail, create a fallback function
            logger.warning("⚠️ Could not import util_training, using fallback")
            def get_model(user_id, features):
                return {
                    "error": "Training service not available",
                    "message": "util_training module not found. Please ensure ML utilities are properly installed.",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
except Exception as e:
    logger.error(f"❌ Error importing training utilities: {str(e)}")
    def get_model(user_id, features):
        return {
            "error": "Training service initialization failed",
            "message": str(e),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "message": "ML Training API is up and running!",
        "status": "healthy",
        "endpoints": {
            "training": "/train_model",
            "health": "/health"
        },
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/health')
def health_check():
    """Detailed health check"""
    try:
        # Test if training function is available
        test_result = get_model("health_check", {"typing": {"holdTimes": [100]}})
        training_available = "error" not in test_result or "not available" not in test_result.get("error", "")
    except:
        training_available = False
    
    return jsonify({
        "status": "healthy",
        "training_service": "available" if training_available else "unavailable",
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
        features = data.get("data")

        # Validate required fields
        if not user_id:
            logger.warning("⚠️ Training request missing user_id")
            return jsonify({
                "error": "Missing user_id in request",
                "code": "MISSING_USER_ID"
            }), 400

        if not features:
            logger.warning("⚠️ Training request missing data")
            return jsonify({
                "error": "Missing data in request", 
                "code": "MISSING_DATA"
            }), 400

        # Log what we received (without sensitive data)
        logger.info(f"🔧 Processing training for user: {user_id}")
        
        if isinstance(features, dict):
            modalities = list(features.keys())
            logger.info(f"📊 Modalities received: {modalities}")
            
            # Log data summary
            for modality, data_content in features.items():
                if isinstance(data_content, dict):
                    fields = list(data_content.keys())
                    logger.info(f"   {modality}: {fields}")

        # Call the training function
        try:
            model_result = get_model(user_id, features)
            
            # Check if training was successful
            if isinstance(model_result, dict) and "error" in model_result:
                logger.error(f"❌ Training failed for user {user_id}: {model_result.get('error')}")
                return jsonify({
                    "error": model_result.get("error"),
                    "message": model_result.get("message", "Training failed"),
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }), 500
            else:
                logger.info(f"✅ Training completed successfully for user: {user_id}")
                return jsonify({
                    "message": "Model training completed successfully",
                    "user_id": user_id,
                    "model_info": model_result,
                    "timestamp": datetime.now().isoformat()
                }), 200
                
        except Exception as training_error:
            logger.error(f"❌ Training error for user {user_id}: {str(training_error)}")
            return jsonify({
                "error": "Training process failed",
                "details": str(training_error),
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }), 500

    except Exception as e:
        logger.error(f"❌ Unexpected error in training endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "Available endpoints: /, /health, /train_model",
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
    print("🚀 Starting ML Training Server...")
    print("🌐 Training endpoint: http://localhost:5000/train_model")
    print("🩺 Health check: http://localhost:5000/health")
    print("📝 Send POST requests with JSON data to /train_model")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

"""
To run this server:
1. Make sure you have Flask installed:
   pip install flask

2. Run the server:
   python app.py

3. Test the training endpoint:
   curl -X POST http://localhost:5000/train_model \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_user",
       "data": {
         "typing": {"holdTimes": [100, 120, 95]},
         "swiping": {"swipeSpeeds": [1.2, 1.5]}
       }
     }'

4. Expected request format:
   {
     "user_id": "string",
     "data": {
       "typing": {
         "holdTimes": [numbers],
         "flightTimes": [numbers],
         "backspaceRates": [numbers],
         "typingSpeeds": [numbers]
       },
       "swiping": {
         "swipeDistances": [numbers],
         "swipeDurations": [numbers], 
         "swipeSpeeds": [numbers],
         "swipeDirections": [numbers],
         "swipeAccelerations": [numbers]
       }
     }
   }
"""