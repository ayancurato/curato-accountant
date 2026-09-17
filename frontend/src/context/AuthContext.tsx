import React, { createContext, useContext, useEffect, useState } from 'react';
import { login as apiLogin } from '../api/client';

interface AuthContextType {
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  isLoading: true,
  error: null,
  login: async () => {},
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem('curato_token');
    if (storedToken) {
      setToken(storedToken);
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, pass: string) => {
    try {
      setError(null);
      const data = await apiLogin(email, pass);
      setToken(data.access_token);
      localStorage.setItem('curato_token', data.access_token);
    } catch (err: any) {
      setError(err.message || 'Login failed');
      throw err;
    }
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem('curato_token');
  };

  return (
    <AuthContext.Provider value={{ token, isLoading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
