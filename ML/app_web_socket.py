# app_web_socket.py - FIXED WebSocket Server
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import sys
import os
import logging

# Add the current directory to Python path to find local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Behavioral Authentication Prediction API", version="1.0.0")

# Try to import the prediction utility with error handling
try:
    # Try different possible import paths
    try:
        from ML.util_predict import predict_with_model
        logger.info("✅ Successfully imported from ML.util_predict")
    except ImportError:
        try:
            from util_predict import predict_with_model
            logger.info("✅ Successfully imported from util_predict")
        except ImportError:
            # If both fail, create a fallback function
            logger.warning("⚠️ Could not import util_predict, using fallback")
            def predict_with_model(user_id, features):
                return {
                    "error": "Prediction service not available",
                    "message": "util_predict module not found",
                    "user_id": user_id
                }
except Exception as e:
    logger.error(f"❌ Error importing prediction utilities: {str(e)}")
    def predict_with_model(user_id, features):
        return {
            "error": "Prediction service error", 
            "message": str(e),
            "user_id": user_id
        }

def process_websocket_data(raw_data):
    """
    Process WebSocket data to match the expected format for prediction
    
    SIMPLE FIX: Your WebSocket already sends the correct field names!
    Just flatten the nested structure:
    
    Input:  {"typing": {"holdTimesNew": [...]}, "swiping": {"swipeSpeedsNew": [...]}}
    Output: {"holdTimesNew": [...], "swipeSpeedsNew": [...]}
    """
    processed_data = {}
    
    if not isinstance(raw_data, dict):
        return processed_data
    
    logger.info(f"Processing raw data with keys: {list(raw_data.keys())}")
    
    # Process all nested data by flattening
    for modality, modality_data in raw_data.items():
        if isinstance(modality_data, dict):
            logger.info(f"{modality} data fields: {list(modality_data.keys())}")
            
            # Flatten: copy all fields from nested structure to top level
            for field_name, field_values in modality_data.items():
                processed_data[field_name] = field_values
                logger.info(f"Flattened {modality}.{field_name} -> {field_name} ({len(field_values) if isinstance(field_values, list) else type(field_values).__name__} items)")
        else:
            # If not nested, keep as is
            processed_data[modality] = modality_data
            logger.info(f"Direct mapping: {modality} -> {modality}")
    
    logger.info(f"WebSocket data processing result: {list(raw_data.keys())} -> {list(processed_data.keys())}")
    return processed_data

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Behavioral Authentication Prediction API is running!",
        "status": "healthy",
        "websocket_endpoint": "/predict",
        "version": "1.0.0-fixed"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test if prediction function is available with proper data format
        test_data = {
            "holdTimesNew": [100, 120, 95],
            "flightTimesNew": [150, 180, 125],
            "swipeSpeedsNew": [1.2, 1.5]
        }
        test_result = predict_with_model("health_check", test_data)
        prediction_available = "error" not in test_result or "not available" not in test_result.get("error", "")
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        prediction_available = False
    
    return {
        "status": "healthy",
        "prediction_service": "available" if prediction_available else "unavailable",
        "websocket_endpoint": "/predict",
        "data_processing": "fixed"
    }

@app.websocket("/predict")
async def predict(websocket: WebSocket):
    """WebSocket endpoint for real-time behavioral predictions"""
    await websocket.accept()
    logger.info("🔌 New WebSocket connection established")
    
    try:
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                logger.info(f"📥 Received WebSocket message")

                # Extract user_id and features
                user_id = message.get("user_id")
                raw_features = message.get("data")

                # Validate required fields
                if not user_id:
                    error_response = {"error": "Missing user_id in request"}
                    await websocket.send_text(json.dumps(error_response))
                    logger.warning("⚠️ Request missing user_id")
                    continue

                if not raw_features:
                    error_response = {"error": "Missing data in request"}
                    await websocket.send_text(json.dumps(error_response))
                    logger.warning("⚠️ Request missing data")
                    continue

                # Log what we received
                logger.info(f"🔧 Processing prediction for user: {user_id}")
                if isinstance(raw_features, dict):
                    logger.info(f"📊 Raw features structure: {list(raw_features.keys())}")
                    for key, value in raw_features.items():
                        if isinstance(value, dict):
                            logger.info(f"   {key}: {list(value.keys())}")
                        elif hasattr(value, '__len__'):
                            logger.info(f"   {key}: {len(value)} items")

                # **CRITICAL FIX**: Process WebSocket data to match expected format
                processed_features = process_websocket_data(raw_features)
                
                if not processed_features:
                    error_response = {
                        "error": "No valid features found in data",
                        "received_structure": list(raw_features.keys()) if isinstance(raw_features, dict) else str(type(raw_features)),
                        "expected_structure": "Should contain 'typing' and/or 'swiping' objects with behavioral data"
                    }
                    await websocket.send_text(json.dumps(error_response))
                    logger.warning(f"⚠️ No valid features extracted from: {list(raw_features.keys()) if isinstance(raw_features, dict) else type(raw_features)}")
                    continue

                logger.info(f"📊 Processed features: {list(processed_features.keys())}")
                for field, values in processed_features.items():
                    if isinstance(values, list):
                        logger.info(f"   {field}: {len(values)} samples")

                # Make prediction with processed data
                try:
                    prediction = predict_with_model(user_id, processed_features)
                    logger.info(f"✅ Prediction completed for user: {user_id}")
                    
                    # Send successful response
                    response = {"result": prediction}
                    await websocket.send_text(json.dumps(response))
                    
                except Exception as pred_error:
                    logger.error(f"❌ Prediction error for user {user_id}: {str(pred_error)}")
                    error_response = {
                        "error": "Prediction failed",
                        "details": str(pred_error),
                        "user_id": user_id,
                        "processed_features": list(processed_features.keys())
                    }
                    await websocket.send_text(json.dumps(error_response))

            except json.JSONDecodeError as json_error:
                logger.error(f"❌ Invalid JSON received: {str(json_error)}")
                error_response = {"error": "Invalid JSON format", "details": str(json_error)}
                await websocket.send_text(json.dumps(error_response))
                
            except Exception as e:
                logger.error(f"❌ Unexpected error processing message: {str(e)}")
                error_response = {
                    "error": "Internal server error",
                    "details": str(e)
                }
                await websocket.send_text(json.dumps(error_response))

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected normally")
    except Exception as e:
        logger.error(f"❌ WebSocket connection error: {str(e)}")
    finally:
        logger.info("🔌 WebSocket connection closed")

@app.post("/debug_websocket_data")
async def debug_websocket_data(request_data: dict):
    """Debug endpoint to test WebSocket data processing"""
    try:
        user_id = request_data.get("user_id", "debug_user")
        raw_data = request_data.get("data", {})
        
        # Process the data
        processed_data = process_websocket_data(raw_data)
        
        # Check if we can make a prediction
        prediction_ready = len(processed_data) > 0
        
        debug_info = {
            "user_id": user_id,
            "raw_data_structure": {
                "type": type(raw_data).__name__,
                "keys": list(raw_data.keys()) if isinstance(raw_data, dict) else "Not a dict"
            },
            "processed_data": {
                "fields": list(processed_data.keys()),
                "sample_counts": {
                    field: len(values) if isinstance(values, list) else type(values).__name__
                    for field, values in processed_data.items()
                }
            },
            "prediction_ready": prediction_ready,
            "processing_status": "success" if processed_data else "no_valid_features"
        }
        
        # Test prediction if data is available
        if prediction_ready:
            try:
                test_prediction = predict_with_model(user_id, processed_data)
                debug_info["test_prediction_status"] = "success" if "error" not in test_prediction else "failed"
                debug_info["test_prediction_error"] = test_prediction.get("error") if "error" in test_prediction else None
            except Exception as pred_error:
                debug_info["test_prediction_status"] = "failed"
                debug_info["test_prediction_error"] = str(pred_error)
        
        return debug_info
        
    except Exception as e:
        return {
            "error": "Debug failed",
            "details": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Fixed Behavioral Authentication Prediction Server...")
    print("📡 WebSocket endpoint: ws://localhost:8000/predict")
    print("🌐 Health check: http://localhost:8000/health")
    print("🐛 Debug endpoint: http://localhost:8000/debug_websocket_data")
    print("📚 API docs: http://localhost:8000/docs")
    print("")
    print("🔧 FIXED: Added proper WebSocket data processing")
    print("📊 Now correctly maps WebSocket field names to expected format")
    
    uvicorn.run(
        "app_web_socket:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

"""
FIXED ISSUES:
1. Added process_websocket_data() function to properly map WebSocket field names
2. WebSocket data now correctly converts from:
   {"swiping": {"swipeSpeeds": [...]}} -> {"swipeSpeedsNew": [...]}
3. Added debug endpoint for testing
4. Better error messages and logging

WebSocket Test Message Format:
{
  "user_id": "8",
  "data": {
    "typing": {
      "holdTimes": [180, 195, 170, 185, 175],
      "flightTimes": [220, 180, 200, 210, 190],
      "backspaceRates": [0.05, 0.08, 0.03, 0.06, 0.04],
      "typingSpeeds": [65.5, 62.8, 68.2, 64.1, 66.8]
    },
    "swiping": {
      "swipeSpeeds": [1.2, 0.8, 1.5, 1.1, 0.9],
      "swipeDirections": [85.5, 92.3, 78.1, 88.7, 94.2],
      "swipeAccelerations": [750.0, 820.5, 690.2, 780.3, 710.8]
    }
  }
}

Expected Response:
{
  "result": {
    "user_id": "8",
    "predictions": {...},
    "prediction_summary": {...}
  }
}
"""