import express from "express"
import { allUsers, loginUser, registerUser } from "../controllers/user.controller.js";



const router = express.Router();

router.post("/register",registerUser);
router.post('/login',loginUser);
router.get('/all',allUsers);


export default router;