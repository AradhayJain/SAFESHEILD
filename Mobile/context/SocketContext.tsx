// SocketContext.tsx
import React, { createContext, useContext, useEffect, ReactNode, useState } from 'react';
import { initiateSocket, closeSocket, getSocket } from '../utils/socket';
import { Socket } from 'socket.io-client';

const SocketContext = createContext<Socket | null>(null);

interface Props {
  children: ReactNode;
}

export const SocketProvider: React.FC<Props> = ({ children }) => {
  const [socketInstance, setSocketInstance] = useState<Socket | null>(null);

  useEffect(() => {
    initiateSocket('http://192.168.1.6:9001'); // Replace this
    const socket = getSocket();
    socket.on('connect', () => {
      console.log('✅ Socket connected to server:', socket.id);
    });
    setSocketInstance(socket);

    return () => {
      closeSocket();
    };
  }, []);

  return (
    <SocketContext.Provider value={socketInstance}>
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = (): Socket => {
  const socket = useContext(SocketContext);
  if (!socket) throw new Error("Socket not available");
  return socket;
};