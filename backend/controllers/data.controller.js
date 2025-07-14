import WebSocket from 'ws';
import axios from 'axios';

let ws = null;

/**
 * Standardize data from frontend to match backend expectations
 * Handles both 'New' suffixed and regular field names
 */
const standardizeDataForBackend = (data) => {
  const standardized = {
    swiping: {},
    typing: {}
  };

  // Swipe data mapping (remove 'New' suffix and standardize names)
  const swipeMapping = {
    'swipeDistancesNew': 'swipeDistances',
    'swipeDistances': 'swipeDistances',
    'swipeDurationsNew': 'swipeDurations', 
    'swipeDurations': 'swipeDurations',
    'swipeSpeedsNew': 'swipeSpeeds',
    'swipeSpeeds': 'swipeSpeeds',
    'swipeDirectionsNew': 'swipeDirections',
    'swipeDirections': 'swipeDirections',
    'swipeAccelerationsNew': 'swipeAccelerations',
    'swipeAccelerations': 'swipeAccelerations'
  };

  // Typing data mapping (remove 'New' suffix and standardize names)
  const typingMapping = {
    'holdTimesNew': 'holdTimes',
    'holdTimes': 'holdTimes',
    'HoldTimes': 'holdTimes',  // Handle inconsistent casing
    'flightTimesNew': 'flightTimes',
    'flightTimes': 'flightTimes',
    'FlightTimes': 'flightTimes',
    'backspaceRatesNew': 'backspaceRates',
    'backspaceRates': 'backspaceRates',
    'typingSpeedsNew': 'typingSpeeds',
    'typingSpeeds': 'typingSpeeds'
  };

  // Process swipe data
  let hasSwipeData = false;
  for (const [frontendKey, backendKey] of Object.entries(swipeMapping)) {
    if (data[frontendKey] && Array.isArray(data[frontendKey]) && data[frontendKey].length > 0) {
      standardized.swiping[backendKey] = data[frontendKey];
      hasSwipeData = true;
    }
  }

  // Process typing data
  let hasTypingData = false;
  for (const [frontendKey, backendKey] of Object.entries(typingMapping)) {
    if (data[frontendKey] !== undefined) {
      // Handle both arrays and single values
      if (Array.isArray(data[frontendKey])) {
        if (data[frontendKey].length > 0) {
          standardized.typing[backendKey] = data[frontendKey];
          hasTypingData = true;
        }
      } else if (data[frontendKey] !== null && data[frontendKey] !== 0) {
        standardized.typing[backendKey] = [data[frontendKey]]; // Convert single value to array
        hasTypingData = true;
      }
    }
  }

  // Remove empty sections
  if (!hasSwipeData) delete standardized.swiping;
  if (!hasTypingData) delete standardized.typing;

  return standardized;
};

/**
 * Validate data before sending to backend
 */
const validateData = (data) => {
  const errors = [];
  const warnings = [];

  // Check if we have any data at all
  if (!data.swiping && !data.typing) {
    errors.push("No valid behavioral data provided");
    return { isValid: false, errors, warnings };
  }

  // Validate swipe data
  if (data.swiping) {
    const requiredSwipeFields = ['swipeSpeeds', 'swipeDirections', 'swipeAccelerations'];
    const missingSwipeFields = requiredSwipeFields.filter(field => 
      !data.swiping[field] || !Array.isArray(data.swiping[field]) || data.swiping[field].length === 0
    );

    if (missingSwipeFields.length > 0) {
      warnings.push(`Missing or empty swipe fields: ${missingSwipeFields.join(', ')}`);
    }

    // Check for minimum swipe data
    if (data.swiping.swipeSpeeds && data.swiping.swipeSpeeds.length < 3) {
      warnings.push(`Insufficient swipe data: ${data.swiping.swipeSpeeds.length} samples (minimum: 3)`);
    }
  }

  // Validate typing data
  if (data.typing) {
    const requiredTypingFields = ['holdTimes', 'flightTimes', 'backspaceRates', 'typingSpeeds'];
    const missingTypingFields = requiredTypingFields.filter(field => 
      !data.typing[field] || (Array.isArray(data.typing[field]) && data.typing[field].length === 0)
    );

    if (missingTypingFields.length > 0) {
      warnings.push(`Missing or empty typing fields: ${missingTypingFields.join(', ')}`);
    }

    // Check for minimum typing data
    if (data.typing.holdTimes && data.typing.holdTimes.length < 5) {
      warnings.push(`Insufficient typing data: ${data.typing.holdTimes.length} samples (minimum: 5)`);
    }
  }

  return { isValid: errors.length === 0, errors, warnings };
};

export const predictWithWebSocket = (data, userId, onMessageCallback, onErrorCallback) => {
  if (!userId) {
    const error = new Error("No user ID provided");
    if (onErrorCallback) onErrorCallback(error);
    return;
  }

  // Standardize the data format
  const standardizedData = standardizeDataForBackend(data);
  
  // Validate the data
  const validation = validateData(standardizedData);
  if (!validation.isValid) {
    const error = new Error(`Data validation failed: ${validation.errors.join(', ')}`);
    if (onErrorCallback) onErrorCallback(error);
    return;
  }

  // Log warnings if any
  if (validation.warnings.length > 0) {
    console.warn("Data validation warnings:", validation.warnings);
  }

  // Create request payload
  const requestData = {
    user_id: userId,
    data: standardizedData
  };

  if (!ws || ws.readyState === WebSocket.CLOSED) {
    ws = new WebSocket("ws://localhost:8000/predict");

    ws.onopen = () => {
      console.log("WebSocket connected");
      console.log("Sending to prediction WS:", requestData);
      ws.send(JSON.stringify(requestData));
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        console.log("📥 Received prediction result:", parsed.result?.predictions);
        
        if (parsed.result?.predictions && onMessageCallback) {
          onMessageCallback(parsed.result.predictions);
        } else if (parsed.error && onErrorCallback) {
          onErrorCallback(new Error(parsed.error));
        }
      } catch (err) {
        console.error("❌ Failed to parse WebSocket message:", err);
        if (onErrorCallback) onErrorCallback(err);
      }
    };

    ws.onerror = (err) => {
      console.error(" WebSocket error:", err.message);
      if (onErrorCallback) onErrorCallback(err);
    };

    ws.onclose = (event) => {
      console.log(" WebSocket connection closed", event.code, event.reason);
      // Attempt to reconnect if connection was closed unexpectedly
      if (event.code !== 1000 && event.code !== 1001) {
        console.log("🔄 Attempting to reconnect in 3 seconds...");
        setTimeout(() => {
          if ((!ws || ws.readyState === WebSocket.CLOSED) && userId) {
            predictWithWebSocket(data, userId, onMessageCallback, onErrorCallback);
          }
        }, 3000);
      }
    };
  } else if (ws.readyState === WebSocket.OPEN) {
    // Connection already open, send data directly
    console.log("Sending to prediction WS (existing connection):", requestData);
    ws.send(JSON.stringify(requestData));
  } else if (ws.readyState === WebSocket.CONNECTING) {
    // Connection is being established, wait for it to open
    console.log("⏳ WebSocket connecting, queuing message...");
    ws.addEventListener('open', () => {
      console.log("Sending queued message:", requestData);
      ws.send(JSON.stringify(requestData));
    }, { once: true });
  }
};

/**
 * Close WebSocket connection (call this when component unmounts)
 */
export const closeWebSocket = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close(1000, "Component unmounting");
    ws = null;
  }
};

/**
 * Enhanced training data submission with proper validation and error handling
 */
export const sendTrainingData = async (req, res) => {
  console.log("Training data submission received");

  const { userId, data2 } = req.body;

  if (!userId) {
    return res.status(401).json({ 
      error: "Unauthorized: No user ID provided.",
      code: "MISSING_USER_ID"
    });
  }

  if (!data2) {
    return res.status(400).json({ 
      error: "Bad Request: No training data provided.",
      code: "MISSING_DATA"
    });
  }

  try {
    // Standardize the training data
    const standardizedData = standardizeDataForBackend(data2);
    
    // Validate the data
    const validation = validateData(standardizedData);
    if (!validation.isValid) {
      return res.status(400).json({
        error: "Data validation failed",
        details: validation.errors,
        warnings: validation.warnings,
        code: "VALIDATION_FAILED"
      });
    }

    // Prepare training request
    const trainingRequest = {
      user_id: userId,
      data: standardizedData
    };

    console.log("Sending training request:", {
      user_id: userId,
      data_summary: {
        swiping: standardizedData.swiping ? Object.keys(standardizedData.swiping) : [],
        typing: standardizedData.typing ? Object.keys(standardizedData.typing) : []
      }
    });

    // Send to training endpoint
    const response = await axios.post('http://localhost:5000/train_model', trainingRequest, {
      timeout: 30000, // 30 second timeout
      headers: {
        'Content-Type': 'application/json',
      }
    });

    // Log validation warnings if any
    if (validation.warnings.length > 0) {
      console.warn("Data validation warnings:", validation.warnings);
    }

    res.status(200).json({
      message: 'Training data sent successfully to ML server.',
      user_id: userId,
      data_quality: {
        validation_warnings: validation.warnings,
        modalities_trained: Object.keys(standardizedData)
      },
      training_response: response.data,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error("Training API error:", error.message);
    
    // Extract meaningful error information
    let errorMessage = "Internal server error";
    let errorCode = "TRAINING_FAILED";
    let statusCode = 500;

    if (error.response) {
      // Server responded with error status
      statusCode = error.response.status;
      errorMessage = error.response.data?.error || error.response.data?.message || error.message;
      errorCode = error.response.data?.code || "SERVER_ERROR";
    } else if (error.request) {
      // Request was made but no response received
      errorMessage = "Training server is not responding";
      errorCode = "SERVER_UNAVAILABLE";
      statusCode = 503;
    } else {
      // Something else happened
      errorMessage = error.message;
      errorCode = "REQUEST_FAILED";
    }

    res.status(statusCode).json({ 
      error: errorMessage,
      code: errorCode,
      user_id: userId,
      timestamp: new Date().toISOString(),
      details: error.response?.data
    });
  }
};

/**
 * Real-time prediction data submission (lighter version for frequent calls)
 */
export const sendPredictionData = async (req, res) => {
  const { userId, data } = req.body;

  if (!userId) {
    return res.status(401).json({ 
      error: "No user ID provided",
      code: "MISSING_USER_ID"
    });
  }

  try {
    // Standardize and validate data
    const standardizedData = standardizeDataForBackend(data);
    const validation = validateData(standardizedData);

    if (!validation.isValid) {
      return res.status(400).json({
        error: "Invalid prediction data",
        details: validation.errors,
        code: "VALIDATION_FAILED"
      });
    }

    const predictionRequest = {
      user_id: userId,
      data: standardizedData
    };

    // Send to prediction endpoint
    const response = await axios.post('http://localhost:8000/predict', predictionRequest, {
      timeout: 10000, // 10 second timeout for predictions
      headers: {
        'Content-Type': 'application/json',
      }
    });

    res.status(200).json({
      predictions: response.data,
      user_id: userId,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error("Prediction API error:", error.message);
    
    const statusCode = error.response?.status || 500;
    const errorMessage = error.response?.data?.error || error.message;

    res.status(statusCode).json({ 
      error: errorMessage,
      code: "PREDICTION_FAILED",
      user_id: userId,
      timestamp: new Date().toISOString()
    });
  }
};

/**
 * Legacy function for backward compatibility
 * @deprecated Use sendTrainingData instead
 */
export const sendData = sendTrainingData;

/**
 * Utility function to get data quality metrics
 */
export const getDataQualityMetrics = (data) => {
  const standardizedData = standardizeDataForBackend(data);
  const validation = validateData(standardizedData);
  
  const metrics = {
    isValid: validation.isValid,
    errors: validation.errors,
    warnings: validation.warnings,
    modalities: {
      swiping: {
        available: !!standardizedData.swiping,
        fields: standardizedData.swiping ? Object.keys(standardizedData.swiping) : [],
        sample_count: standardizedData.swiping?.swipeSpeeds?.length || 0
      },
      typing: {
        available: !!standardizedData.typing,
        fields: standardizedData.typing ? Object.keys(standardizedData.typing) : [],
        sample_count: standardizedData.typing?.holdTimes?.length || 0
      }
    },
    overall_quality: validation.isValid ? 
      (validation.warnings.length === 0 ? 'good' : 'acceptable') : 'poor'
  };

  return metrics;
};

/**
 * Health check function for WebSocket connection
 */
export const checkWebSocketHealth = () => {
  return {
    connected: ws?.readyState === WebSocket.OPEN,
    state: ws?.readyState,
    states: {
      0: 'CONNECTING',
      1: 'OPEN', 
      2: 'CLOSING',
      3: 'CLOSED'
    }
  };
};
