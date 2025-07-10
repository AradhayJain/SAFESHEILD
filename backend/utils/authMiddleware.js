import jwt from "jsonwebtoken"
import { User } from "../models/user.model.js";
import asyncHandler from "express-async-handler"

export const protect = asyncHandler(async (req, res, next) => {
  let token;

  if (
    req.headers.authorization &&
    req.headers.authorization.startsWith("Bearer")
  ) {
    try {
      token = req.headers.authorization.split(" ")[1];

      //decodes token id
      
      const decoded = jwt.verify(token, process.env.SECRET_KEY);

      req.user = await User.findById(decoded.id).select("-password");

      next();
    } catch (error) {
        res.status(401);
        throw new Error("Not authorized, token failed");
    }
  }

  if (!token) {
    res.status(401);
    throw new Error("Not authorized, no token");
  }
});


