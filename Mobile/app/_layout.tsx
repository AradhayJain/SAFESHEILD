// app/_layout.tsx
import { Stack } from 'expo-router';
import { SocketProvider } from '../context/SocketContext'; // adjust path as needed

export default function Layout() {
  return (
    <SocketProvider>
      <Stack screenOptions={{ headerShown: false }} />
    </SocketProvider>
  );
}