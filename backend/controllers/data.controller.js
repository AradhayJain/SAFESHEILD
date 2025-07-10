import WebSocket from 'ws';
import axios from 'axios';

export const predictWithWebSocket = async (data, userId) => {
  if (!userId) throw new Error("No user ID provided");

  const ws = new WebSocket("ws://localhost:8000/predict");

  const requestData = {
    user_id: userId,
    data: {}
  };

  if (
    data.swipeDistances || data.swipeDurations || data.swipeSpeeds ||
    data.swipeDirections || data.swipeAccelerations
  ) {
    requestData.data.swiping = {
      ...(data.swipeDistances && { swipeDistances: data.swipeDistances }),
      ...(data.swipeDurations && { swipeDurations: data.swipeDurations }),
      ...(data.swipeSpeeds && { swipeSpeeds: data.swipeSpeeds }),
      ...(data.swipeDirections && { swipeDirections: data.swipeDirections }),
      ...(data.swipeAccelerations && { swipeAccelerations: data.swipeAccelerations }),
    };
  }

  if (
    data.holdTimes || data.flightTimes || data.backspaceRates || data.typingSpeeds
  ) {
    requestData.data.typing = {
      ...(data.holdTimes && { keyHoldTimes: data.holdTimes }),
      ...(data.flightTimes && { keyFlightTimes: data.flightTimes }),
      ...(data.backspaceRates && { backspaceRates: data.backspaceRates }),
      ...(data.typingSpeeds && { typingSpeeds: data.typingSpeeds }),
    };
  }

  const result = await new Promise((resolve, reject) => {
    ws.onopen = () => {
      ws.send(JSON.stringify(requestData));
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        resolve(parsed);
      } catch (err) {
        reject(new Error("Invalid response from prediction server"));
      } finally {
        ws.close();
      }
    };

    ws.onerror = (err) => {
      reject(new Error(`WebSocket connection error: ${err.message}`));
    };
  });

  return result;
};

  

export const sendData = async (req, res) => {
    const userId = 8;
    console.log("added")
  
    const {
        swipeDistances,
        swipeDurations,
        swipeSpeeds,
        swipeDirections,
        swipeAccelerations,
        holdTimes,
        flightTimes,
        backspaceRates,
        typingSpeeds,      
    } = req.body;
  
    if (!userId) {
      return res.status(401).json({ error: "Unauthorized: No user ID found." });
    }
  
    const data = {
      user_id: userId,
      data: {
        swiping: {
          swipeDistances,
          swipeDurations,
          swipeSpeeds,
          swipeDirections,
          swipeAccelerations,
        },
        typing: {
          holdTimes,
          flightTimes,
          backspaceRates,
          typingSpeeds, 
        }
      }
    };
    console.log(data)
  
    try {
      const response = await axios.post('http://localhost:5000/train_model', data);
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
