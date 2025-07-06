# fastapi_ws.py
from fastapi import FastAPI, WebSocket
from util_predict import predict_with_model
import json

app = FastAPI()

@app.websocket("/predict")
async def predict(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            message = json.loads(data)
            user_id = message.get("user_id")
            features = message.get("data")

            if not user_id or not features:
                await websocket.send_text(json.dumps({"error": "Missing user_id or data"}))
                continue

            prediction = predict_with_model(user_id, features)
            await websocket.send_text(json.dumps({"result": prediction}))
        except Exception as e:
            await websocket.send_text(json.dumps({"error": str(e)}))


"""
uvicorn app_web_socket:app --host 0.0.0.0 --port 8000 :-run on terminal
ws://localhost:8000/predict
{
    "user_id": "user123",
    "data": {
        "typing_speed": [3.1],
        "touch_duration": [105]
    }
}
"""