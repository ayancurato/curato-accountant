import React, { createContext, useContext, useEffect, useState } from 'react';
import { login as apiLogin, getMe } from '../api/client';

export interface UserData {
  id: string;
  name: string;
  email: string;
  company_id: string;
  role: string;
  is_active: boolean;
}

interface AuthContextType {
  token: string | null;
  user: UserData | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
}

export function isJwtTokenValid(token: string | null | undefined): boolean {
  if (!token || typeof token !== 'string') return false;
  const trimmed = token.trim();
  if (trimmed === '' || trimmed === 'undefined' || trimmed === 'null') return false;

  const parts = trimmed.split('.');
  if (parts.length !== 3) return false;

  try {
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      window
        .atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    const decoded = JSON.parse(jsonPayload);
    if (decoded.exp && typeof decoded.exp === 'number') {
      const nowInSeconds = Math.floor(Date.now() / 1000);
      if (decoded.exp <= nowInSeconds) {
        return false;
      }
    }
    return true;
  } catch {
    return false;
  }
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  user: null,
  isLoading: true,
  error: null,
  login: async () => {},
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('curato_token');
  };

  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      const storedToken = localStorage.getItem('curato_token');
      if (!storedToken || !isJwtTokenValid(storedToken)) {
        localStorage.removeItem('curato_token');
        if (isMounted) {
          setToken(null);
          setUser(null);
          setIsLoading(false);
        }
        return;
      }

      try {
        const userData = await getMe(storedToken);
        if (isMounted) {
          setToken(storedToken);
          setUser(userData);
        }
      } catch {
        // Backend rejected token (e.g. 401 or invalid signature or user removed)
        localStorage.removeItem('curato_token');
        if (isMounted) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initAuth();

    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      isMounted = false;
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (email: string, pass: string) => {
    try {
      setError(null);
      const data = await apiLogin(email, pass);
      localStorage.setItem('curato_token', data.access_token);
      setToken(data.access_token);
      try {
        const userData = await getMe(data.access_token);
        setUser(userData);
      } catch {
        // If /me fails temporarily, token is already valid
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
      throw err;
    }
  };

  return (
    <AuthContext.Provider value={{ token, user, isLoading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
