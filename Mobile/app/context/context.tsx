// app/contexts/UserContext.tsx
import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Type definitions
interface User {
  name: string;
  email: string;
  // add more fields if needed
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (data: { token: string; user: User }) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
}

// Create the context
const UserContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadFromStorage = async () => {
      try {
        const storedToken = await AsyncStorage.getItem('authToken');
        const storedUser = await AsyncStorage.getItem('authUser');

        if (storedToken) {
          setToken(storedToken);
        }
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }
      } catch (e) {
        console.error('Failed to load auth data:', e);
      } finally {
        setLoading(false);
      }
    };

    loadFromStorage();
  }, []);

  const login = async ({ token, user }: { token: string; user: User }) => {
    try {
      setToken(token);
      setUser(user);
      await AsyncStorage.setItem('authToken', token);
      await AsyncStorage.setItem('authUser', JSON.stringify(user));
    } catch (e) {
      console.error('Login failed:', e);
    }
  };

  const logout = async () => {
    try {
      setToken(null);
      setUser(null);
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('authUser');
    } catch (e) {
      console.error('Logout failed:', e);
    }
  };

  return (
    <UserContext.Provider value={{ token, user, login, logout, loading }}>
      {children}
    </UserContext.Provider>
  );
};

// Custom hook
export const useUser = (): AuthContextType => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};