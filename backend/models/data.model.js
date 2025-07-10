import mongoose from "mongoose";

const dataSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },

  // Swiping features
  speed_mean: { type: [Number], required: true },
  speed_std: { type: [Number], required: true },
  direction_mean: { type: [Number], required: true },
  direction_std: { type: [Number], required: true },
  acceleration_mean: { type: [Number], required: true },
  acceleration_std: { type: [Number], required: true },

  // Typing features
  typing_speed_mean: { type: [Number], required: true },
  typing_speed_std: { type: [Number], required: true },

  // Optional metadata
  deviceId: { type: String },
  sessionId: { type: String }
}, { timestamps: true });

const UserBehaviorData = mongoose.model("UserBehaviorData", dataSchema);

export default UserBehaviorData;
