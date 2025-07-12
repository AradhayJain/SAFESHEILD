import WebSocket from 'ws';
import axios from 'axios';

let ws = null;

export const predictWithWebSocket = (data, userId, onMessageCallback, onErrorCallback) => {
  if (!userId) throw new Error("No user ID provided");

  if (!ws || ws.readyState === WebSocket.CLOSED) {
    ws = new WebSocket("ws://localhost:8000/predict");

    ws.onopen = () => {
      console.log("✅ WebSocket connected");

      const requestData = {
        user_id: userId,
        data: {}
      };

      if (
        data.swipeDistancesNew || data.swipeDurationsNew || data.swipeSpeedsNew ||
        data.swipeDirectionsNew || data.swipeAccelerationsNew
      ) {
        requestData.data.swiping = {
          ...(data.swipeDistancesNew && { swipeDistances: data.swipeDistancesNew }),
          ...(data.swipeDurationsNew && { swipeDurations: data.swipeDurationsNew }),
          ...(data.swipeSpeedsNew && { swipeSpeeds: data.swipeSpeedsNew }),
          ...(data.swipeDirectionsNew && { swipeDirections: data.swipeDirectionsNew }),
          ...(data.swipeAccelerationsNew && { swipeAccelerations: data.swipeAccelerationsNew }),
        };
      }

      if (
        data.holdTimesNew || data.flightTimesNew || data.backspaceRatesNew || data.typingSpeedsNew
      ) {
        requestData.data.typing = {
          ...(data.holdTimesNew && { HoldTimes: data.holdTimesNew }),
          ...(data.flightTimesNew && { FlightTimes: data.flightTimesNew }),
          ...(data.backspaceRatesNew && { backspaceRates: data.backspaceRatesNew }),
          ...(data.typingSpeedsNew && { typingSpeeds: data.typingSpeedsNew }),
        };
      }

      console.log("📤 Sending to prediction WS:", requestData);
      ws.send(JSON.stringify(requestData));
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        console.log("📥 Received:", parsed.result.predictions);
        if (onMessageCallback) onMessageCallback(parsed.result.predictions);
      } catch (err) {
        console.error("❌ Failed to parse message:", err);
        if (onErrorCallback) onErrorCallback(err);
      }
    };

    ws.onerror = (err) => {
      console.error("❌ WebSocket error:", err.message);
      if (onErrorCallback) onErrorCallback(err);
    };

    ws.onclose = () => {
      console.log("🔌 WebSocket connection closed");
    };
  } else if (ws.readyState === WebSocket.OPEN) {
    // If already open, send the new data directly
    const requestData = {
      user_id: userId,
      data: {}
    };

    if (
      data.swipeDistancesNew || data.swipeDurationsNew || data.swipeSpeedsNew ||
      data.swipeDirectionsNew || data.swipeAccelerationsNew
    ) {
      requestData.data.swiping = {
        ...(data.swipeDistancesNew && { swipeDistances: data.swipeDistancesNew }),
        ...(data.swipeDurationsNew && { swipeDurations: data.swipeDurationsNew }),
        ...(data.swipeSpeedsNew && { swipeSpeeds: data.swipeSpeedsNew }),
        ...(data.swipeDirectionsNew && { swipeDirections: data.swipeDirectionsNew }),
        ...(data.swipeAccelerationsNew && { swipeAccelerations: data.swipeAccelerationsNew }),
      };
    }

    if (
      data.holdTimesNew || data.flightTimesNew || data.backspaceRatesNew || data.typingSpeedsNew
    ) {
      requestData.data.typing = {
        ...(data.holdTimesNew && { HoldTimes: data.holdTimesNew }),
        ...(data.flightTimesNew && { FlightTimes: data.flightTimesNew }),
        ...(data.backspaceRatesNew && { backspaceRates: data.backspaceRatesNew }),
        ...(data.typingSpeedsNew && { typingSpeeds: data.typingSpeedsNew }),
      };
    }

    console.log("📤 Sending to prediction WS (reused socket):", requestData);
    ws.send(JSON.stringify(requestData));
  }
};


  

export const sendData = async (req, res) => {
    
    console.log("added")
  
    const {userId,data2} = req.body;
  
    if (!userId) {
      return res.status(401).json({ error: "Unauthorized: No user ID found." });
    }
  
    const data1 = {
      user_id: userId,
      data: {
        swiping: {
          swipeDistances: data2.swipeDistances,
          swipeDurations: data2.swipeDurations,
          swipeSpeeds: data2.swipeSpeeds,
          swipeDirections: data2.swipeDirections,
          swipeAccelerations: data2.swipeAccelerations,
        },
        typing: {
          holdTimes: data2.holdTimes,
          flightTimes: data2.flightTimes,
          backspaceRates: data2.backspaceRates,
          typingSpeeds: data2.typingSpeeds,
        },
      },
    };
    
    console.log(data1)
  
    try {
      const response = await axios.post('http://localhost:5000/train_model', data1);
      res.status(200).json({
        message: 'Data sent successfully to prediction server.',
        response:response.data
    });
    } catch (error) {
      console.error("Prediction API error:", error.message);
      const status = error.response?.status || 500;
      const message = error.response?.data?.error || "Internal server error";
      res.status(status).json({ error: message });
    }
  };
