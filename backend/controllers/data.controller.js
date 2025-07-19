import WebSocket from 'ws';
import axios from 'axios';
import UserBehaviorData from "../models/data.model.js";

let ws = null;

export const predictWithWebSocket = (data, userId, onMessageCallback, onErrorCallback) => {
  if (!userId) throw new Error("No user ID provided");

  if (!ws || ws.readyState === WebSocket.CLOSED) {
    ws = new WebSocket("ws://localhost:8000/predict");

    ws.onopen = () => {
      console.log("âœ… WebSocket connected");

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
          ...(data.holdTimesNew && { holdTimes: data.holdTimesNew }),
          ...(data.flightTimesNew && { flightTimes: data.flightTimesNew }),
          ...(data.backspaceRatesNew && { backspaceRates: data.backspaceRatesNew }),
          ...(data.typingSpeedsNew && { typingSpeeds: data.typingSpeedsNew }),
        };
      }

      console.log("ðŸ“¤ Sending to prediction WS:", requestData);
      ws.send(JSON.stringify(requestData));
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        console.log("ðŸ“¥ Received:", parsed.result.predictions);
        if (onMessageCallback) onMessageCallback(parsed.result.predictions);
      } catch (err) {
        console.error("âŒ Failed to parse message:", err);
        if (onErrorCallback) onErrorCallback(err);
      }
    };

    ws.onerror = (err) => {
      console.error("âŒ WebSocket error:", err.message);
      if (onErrorCallback) onErrorCallback(err);
    };

    ws.onclose = () => {
      console.log("ðŸ”Œ WebSocket connection closed");
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
        ...(data.holdTimesNew && { holdTimes: data.holdTimesNew }),
        ...(data.flightTimesNew && { flightTimes: data.flightTimesNew }),
        ...(data.backspaceRatesNew && { backspaceRates: data.backspaceRatesNew }),
        ...(data.typingSpeedsNew && { typingSpeeds: data.typingSpeedsNew }),
      };
    }

    console.log(" Sending to prediction WS (reused socket):", requestData);
    ws.send(JSON.stringify(requestData));
  }
};


  

export const sendData = async (req, res) => {
  console.log("added");

  const { userId, data2 } = req.body;

  if (!userId) {
    return res.status(401).json({ error: "Unauthorized: No user ID found." });
  }

  // Construct raw data for local DB save
  const dbData = {
    userId: userId,
    swipeDistances: data2.swipeDistances,
    swipeDurations: data2.swipeDurations,
    swipeSpeeds: data2.swipeSpeeds,
    swipeDirections: data2.swipeDirections,
    swipeAccelerations: data2.swipeAccelerations,
    holdTimes: data2.holdTimes,
    flightTimes: data2.flightTimes,
    backspaceRates: data2.backspaceRates,
    typingSpeeds: data2.typingSpeeds
  };

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

  console.log(data1);

  try {
    // Save to MongoDB
    const savedEntry = await UserBehaviorData.create(dbData);
    await savedEntry.save();

    // Send to prediction server
    console.log(savedEntry)
    const response = await axios.post('http://localhost:5001/train_model', data1);

    res.status(200).json({
      message: 'Data saved and sent successfully to prediction server.',
      dbEntry: savedEntry,
      predictionResponse: response.data
    });

  } catch (error) {
    console.error("Error:", error.message);
    const status = error.response?.status || 500;
    const message = error.response?.data?.error || "Internal server error";
    res.status(status).json({ error: message });
  }
};