// socket.ts
import { io, Socket } from 'socket.io-client';

let socket: Socket | null = null;

export const initiateSocket = (serverUrl: string): void => {
  if (!socket) {
    socket = io(serverUrl, {
      transports: ['websocket'],
      forceNew: true,
    });
    console.log('🔌 Socket initialized');
  }
};

export const getSocket = (): Socket => {
  if (!socket) {
    throw new Error("Socket not initialized. Call initiateSocket first.");
  }
  return socket;
};

export const closeSocket = (): void => {
  if (socket) {
    socket.disconnect();
    console.log('❌ Socket disconnected');
    socket = null;
  }
};