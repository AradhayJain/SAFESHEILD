import mongoose from "mongoose";

const dataSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },

  // Swiping raw data
  swipeDistances: { type: [Number], required: true },
  swipeDurations: { type: [Number], required: true },
  swipeSpeeds: { type: [Number], required: true },
  swipeDirections: { type: [Number], required: true },
  swipeAccelerations: { type: [Number], required: true },

  // Typing raw data
  holdTimes: { type: [Number], required: true },
  flightTimes: { type: [Number], required: true },
  backspaceRates: { type: [Number], required: true },
  typingSpeeds: { type: [Number], required: true },
  
}, { timestamps: true });

const UserBehaviorData = mongoose.model("UserBehaviorData", dataSchema);

export default UserBehaviorData;
