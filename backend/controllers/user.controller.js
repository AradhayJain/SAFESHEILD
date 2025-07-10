import asyncHandler from "express-async-handler";
import generateToken from "../utils/generateToken.js";
import { User } from "../models/user.model.js";

// Register User
export const registerUser = asyncHandler(async (req, res) => {
  const { username, AccountNumber, password, PhoneNumber } = req.body;

  if (!username || !AccountNumber || !password) {
    res.status(400);
    throw new Error("Please fill in all fields");
  }

  const userExists = await User.findOne({ AccountNumber });
  if (userExists) {
    res.status(400);
    throw new Error("User already exists");
  }

  const user = await User.create({
    username,
    AccountNumber,
    password,
    PhoneNumber
  });

  if (user) {
    res.status(201).json({
      _id: user._id,
      username: user.username,
      AccountNumber: user.AccountNumber,
      PhoneNumber: user.PhoneNumber
      
    });
  } else {
    res.status(400);
    throw new Error("Invalid user data");
  }
});

// Login User
export const loginUser = asyncHandler(async (req, res) => {
  const { AccountNumber, password } = req.body;

  const user = await User.findOne({ AccountNumber });

  if (user && (await user.matchPassword(password))) {
    const token = generateToken(user._id);
    res.status(200).json({
      user:{
        _id: user._id,
        username: user.username,
        AccountNumber: user.AccountNumber,
        PhoneNumber: user.PhoneNumber,
        
      },
      token: token,
    });
  } else {
    res.status(401);
    throw new Error("Invalid credentials");
  }
});

// Get All Users (Search)
export const allUsers = asyncHandler(async (req, res) => {
  const keyword = req.query.search
    ? {
        $or: [
          { username: { $regex: req.query.search, $options: "i" } },
          { AccountNumber: { $regex: req.query.search, $options: "i" } },
        ],
      }
    : {};

  const users = await User.find(keyword).find({ _id: { $ne: req.user._id } });
  res.send(users);
});
