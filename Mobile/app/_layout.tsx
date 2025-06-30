import { Stack } from 'expo-router';
import { UserProvider } from './context/context'; // adjust if path differs

export default function Layout() {


  return (
    <UserProvider>
      <Stack screenOptions={{ headerShown: false }} />
    </UserProvider>
  );
}