// utils/socket.ts
import { io, Socket } from 'socket.io-client';

let socket: Socket | null = null;

export const initiateSocket = (url: string): void => {
  if (!socket) {
    socket = io(url, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true, // ensure reconnection
    });
  }
};

export const getSocket = (): Socket => {
  if (!socket) throw new Error("Socket not initialized");
  return socket;
};

export const closeSocket = (): void => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};
