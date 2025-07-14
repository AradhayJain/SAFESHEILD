# app_web_socket.py
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

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Behavioral Authentication Prediction API is running!",
        "status": "healthy",
        "websocket_endpoint": "/predict"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test if prediction function is available
        test_result = predict_with_model("health_check", {"typing": {"holdTimes": [100]}})
        prediction_available = "error" not in test_result or "not available" not in test_result.get("error", "")
    except:
        prediction_available = False
    
    return {
        "status": "healthy",
        "prediction_service": "available" if prediction_available else "unavailable",
        "websocket_endpoint": "/predict"
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
                logger.info(f"📥 Received message from client")

                # Extract user_id and features
                user_id = message.get("user_id")
                features = message.get("data")

                # Validate required fields
                if not user_id:
                    error_response = {"error": "Missing user_id in request"}
                    await websocket.send_text(json.dumps(error_response))
                    logger.warning("⚠️ Request missing user_id")
                    continue

                if not features:
                    error_response = {"error": "Missing data in request"}
                    await websocket.send_text(json.dumps(error_response))
                    logger.warning("⚠️ Request missing data")
                    continue

                # Log what we received (without sensitive data)
                logger.info(f"Processing prediction for user: {user_id}")
                logger.debug(f"Features received: {list(features.keys()) if isinstance(features, dict) else type(features)}")

                # Make prediction
                try:
                    prediction = predict_with_model(user_id, features)
                    logger.info(f"✅ Prediction completed for user: {user_id}")
                    
                    # Send successful response
                    response = {"result": prediction}
                    await websocket.send_text(json.dumps(response))
                    
                except Exception as pred_error:
                    logger.error(f"❌ Prediction error for user {user_id}: {str(pred_error)}")
                    error_response = {
                        "error": "Prediction failed",
                        "details": str(pred_error),
                        "user_id": user_id
                    }
                    await websocket.send_text(json.dumps(error_response))

            except json.JSONDecodeError as json_error:
                logger.error(f"❌ Invalid JSON received: {str(json_error)}")
                error_response = {"error": "Invalid JSON format"}
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

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Behavioral Authentication Prediction Server...")
    print("📡 WebSocket endpoint: ws://localhost:8000/predict")
    print("🌐 Health check: http://localhost:8000/health")
    print("📚 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "app_web_socket:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

"""
To run this server:
1. Make sure you have the required dependencies:
   pip install fastapi uvicorn

2. Run the server:
   python app_web_socket.py
   
   OR
   
   uvicorn app_web_socket:app --host 0.0.0.0 --port 8000 --reload

3. Test the WebSocket connection:
   WebSocket URL: ws://localhost:8000/predict

4. Test message format:
   {
     "user_id": "test_user",
     "data": {
       "typing": {"holdTimes": [100, 120, 95]},
       "swiping": {"swipeSpeeds": [1.2, 1.5]}
     }
   }
"""