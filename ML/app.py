# ek baari yeh app.py test kar @918595132781 
from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime
import traceback

# Import your prediction functions
try:
    from util_predict import (
        predict_with_model, 
        predict_lightweight, 
        batch_predict,
        create_test_prediction_data,
        test_prediction_pipeline
    )
    PREDICTION_MODULES_LOADED = True
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure util_predict.py and all ML modules are in the correct directories")
    PREDICTION_MODULES_LOADED = False

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return jsonify({"message": "ML Prediction API is up and running!"}), 200

@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    Expected JSON format:
    {
        "user_id": "user123",
        "data": {
            "swipeSpeedsNew": [1.2, 0.8, 1.5],
            "swipeDirectionsNew": [85.5, 92.3, 78.1],
            "swipeAccelerationsNew": [750.0, 820.5, 690.2],
            "holdTimesNew": [180, 195, 170],
            "flightTimesNew": [220, 180, 200],
            "backspaceRatesNew": [0.05, 0.08, 0.03],
            "typingSpeedsNew": [65.5, 62.8, 68.2]
        }
    }
    """
    if not PREDICTION_MODULES_LOADED:
        return jsonify({"error": "Prediction modules not loaded. Check server logs."}), 500
    
    try:
        # Validate content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        user_id = data.get("user_id")
        features = data.get("data")
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        if not features:
            return jsonify({"error": "Missing data"}), 400
        
        # Use the full prediction function
        result = predict_with_model(user_id, features)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in predict endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route('/predict_lightweight', methods=['POST'])
def predict_light():
    """
    Lightweight prediction endpoint for high-frequency requests
    Same JSON format as /predict but with faster processing
    """
    if not PREDICTION_MODULES_LOADED:
        return jsonify({"error": "Prediction modules not loaded. Check server logs."}), 500
    
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        user_id = data.get("user_id")
        features = data.get("data")
        
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        if not features:
            return jsonify({"error": "Missing data"}), 400
        
        # Use the lightweight prediction function
        result = predict_lightweight(user_id, features)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in predict_lightweight endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Lightweight prediction failed: {str(e)}"}), 500

@app.route('/batch_predict', methods=['POST'])
def batch_predict_endpoint():
    """
    Batch prediction endpoint for multiple users
    Expected JSON format:
    {
        "requests": [
            {
                "user_id": "user1",
                "data": { ... }
            },
            {
                "user_id": "user2", 
                "data": { ... }
            }
        ]
    }
    """
    try:
        data = request.json
        requests = data.get("requests", [])
        
        if not requests:
            return jsonify({"error": "Missing requests array"}), 400
        
        if not isinstance(requests, list):
            return jsonify({"error": "Requests must be an array"}), 400
        
        # Process batch prediction
        results = batch_predict(requests)
        
        return jsonify({
            "results": results,
            "processed_count": len(results),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch_predict endpoint: {str(e)}")
        return jsonify({"error": f"Batch prediction failed: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if not PREDICTION_MODULES_LOADED:
            return jsonify({
                "status": "unhealthy",
                "error": "Prediction modules not loaded",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # Test if the prediction modules can be imported and are working
        test_data = create_test_prediction_data()
        test_user_id = "health_check_user"
        
        # Try a lightweight prediction to verify everything works
        result = predict_lightweight(test_user_id, test_data)
        
        if 'error' in result:
            return jsonify({
                "status": "unhealthy",
                "error": f"Prediction test failed: {result['error']}",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "prediction_modules": "loaded and functional",
            "test_prediction": "successful"
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test_prediction', methods=['GET'])
def test_prediction():
    """Test endpoint with sample data"""
    if not PREDICTION_MODULES_LOADED:
        return jsonify({"error": "Prediction modules not loaded. Check server logs."}), 500
    
    try:
        test_data = create_test_prediction_data()
        test_user_id = "test_api_user"
        
        result = predict_with_model(test_user_id, test_data)
        
        return jsonify({
            "test_result": result,
            "test_data_used": test_data,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test_prediction endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Test prediction failed: {str(e)}"}), 500

@app.route('/run_full_test', methods=['GET'])
def run_full_test():
    """Run the complete test pipeline from util_predict"""
    if not PREDICTION_MODULES_LOADED:
        return jsonify({"error": "Prediction modules not loaded. Check server logs."}), 500
    
    try:
        # Capture the test output
        import io
        import sys
        from contextlib import redirect_stdout
        
        output_buffer = io.StringIO()
        
        with redirect_stdout(output_buffer):
            prediction_result, lightweight_result = test_prediction_pipeline()
        
        test_output = output_buffer.getvalue()
        
        return jsonify({
            "test_output": test_output,
            "prediction_result": prediction_result,
            "lightweight_result": lightweight_result,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in run_full_test endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Full test failed: {str(e)}"}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Check if required modules are available
    if PREDICTION_MODULES_LOADED:
        print("✅ Prediction modules loaded successfully")
        
        # Optional: Run a quick test to verify everything works
        try:
            test_data = create_test_prediction_data()
            result = predict_lightweight("startup_test_user", test_data)
            if 'error' not in result:
                print("✅ Prediction pipeline test successful")
            else:
                print(f"⚠️  Prediction pipeline test failed: {result['error']}")
        except Exception as e:
            print(f"⚠️  Startup test failed: {e}")
    else:
        print("❌ Failed to load prediction modules")
        print("Please ensure util_predict.py and all ML modules are properly set up")
    
    print("\nStarting Flask server...")
    print("Available endpoints:")
    print("  GET  /               - Home page")
    print("  POST /predict        - Full prediction with model updates")
    print("  POST /predict_lightweight - Fast prediction")
    print("  POST /batch_predict  - Batch predictions")
    print("  GET  /health         - Health check")
    print("  GET  /test_prediction - Test with sample data")
    print("  GET  /run_full_test  - Run complete test pipeline")
    print("\nExample curl command:")
    print("curl -X POST http://localhost:5000/predict -H 'Content-Type: application/json' -d '{\"user_id\":\"test\",\"data\":{\"swipeSpeedsNew\":[1.2,0.8],\"holdTimesNew\":[180,195]}}'")
    
    app.run(debug=True, host='0.0.0.0', port=5000)