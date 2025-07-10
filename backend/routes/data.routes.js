import express from "express"
import { sendData } from "../controllers/data.controller.js";

const router=express.Router();

router.post('/getData',sendData);

export default router;