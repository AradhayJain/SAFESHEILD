import WebSocket from 'ws';
import axios from 'axios';

export const predictWithWebSocket = async (data, userId) => {
    if (!userId) throw new Error("No user ID provided");
  
    const ws = new WebSocket("ws://localhost:8000/predict");
  
    const requestData = {
      user_id: userId,
      data: {
        swiping: {
          swipeDistances: data.swipeDistances,
          swipeDurations: data.swipeDurations,
          swipeSpeeds: data.swipeSpeeds,
          swipeDirections: data.swipeDirections,
          swipeAccelerations: data.swipeAccelerations
        },
        typing: {
          keyHoldTimes: data.holdTimes,
          keyFlightTimes: data.flightTimes,
          backspaceRates: data.backspaceRates,
          typingSpeeds: data.typingSpeeds
        }
      }
    };
    
  
    // Await the message using Promise inside
    const result = await new Promise((resolve, reject) => {
      ws.on("open", () => {
        ws.send(JSON.stringify(requestData));
      });
  
      ws.on("message", (message) => {
        try {
          const parsed = JSON.parse(message);
          resolve(parsed);
        } catch (err) {
          reject(new Error("Invalid response from prediction server"));
        } finally {
          ws.close();
        }
      });
  
      ws.on("error", (err) => {
        reject(new Error(`WebSocket connection error: ${err.message}`));
      });
    });
  
    return result;
};
  

export const sendData = async (req, res) => {
    const userId = 1;
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
  
    const requestData = {
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
    console.log(requestData)
  
    try {
      // const response = await axios.post('http://localhost:5000/train_model', requestData);
      res.status(200).json({
        message: 'Data sent successfully to prediction server.',
        response:requestData
    });
    } catch (error) {
      console.error("Prediction API error:", error.message);
      const status = error.response?.status || 500;
      const message = error.response?.data?.error || "Internal server error";
      res.status(status).json({ error: message });
    }
  };
