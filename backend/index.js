import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import http from "http";
import { Server } from "socket.io";

// import WebSocket from "ws";

import MongoDB from "./utils/DB.js";
import userRoutes from "./routes/user.routes.js";
import dataRoutes from "./routes/data.routes.js";
import { predictWithWebSocket } from "./controllers/data.controller.js"; // Your async function

dotenv.config();

const app = express();
const PORT = process.env.PORT || 9001;

// CORS setup
const corsOptions = {
  origin: "*", // Change this to your frontend domain in production
  methods: ["GET", "POST", "PUT", "DELETE"],
};

// Middleware
app.use(cors(corsOptions));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use("/api/users", userRoutes);
app.use("/api/data", dataRoutes);

// Health check
app.get("/", (req, res) => {
  res.send("SAFESHIELD API server is running.");
});

// Create HTTP server and attach Socket.IO
const server = http.createServer(app);
const io = new Server(server, {
  cors: corsOptions,
});

// Socket.IO connection handler
io.on("connection", (socket) => {
  console.log("Socket.IO client connected:", socket.id);

  socket.on("send-features", async (data) => {
    const userId = data.user_id; // You can also pass this via auth/session

    try {
      const result = await predictWithWebSocket(data, userId);
      socket.emit("prediction-result", result);
    } catch (err) {
      socket.emit("prediction-error", { error: err.message });
    }
  });

  socket.on("disconnect", () => {
    console.log("Client disconnected:", socket.id);
  });
});

// Start the server
server.listen(PORT, () => {
  MongoDB(); // Connect to MongoDB
  console.log(`🚀 SAFESHIELD server running on http://localhost:${PORT}`);
});
