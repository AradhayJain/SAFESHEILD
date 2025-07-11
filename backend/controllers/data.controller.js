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
      ...(data.holdTimesNew && { keyHoldTimes: data.holdTimesNew }),
      ...(data.flightTimesNew && { keyFlightTimes: data.flightTimesNew }),
      ...(data.backspaceRatesNew && { backspaceRates: data.backspaceRatesNew }),
      ...(data.typingSpeedsNew && { typingSpeeds: data.typingSpeedsNew }),
    };
  }
  console.log("📤 Sending to prediction WS:", requestData);


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
