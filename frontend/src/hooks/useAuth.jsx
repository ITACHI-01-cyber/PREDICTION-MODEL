import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(authService.getStoredUser());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const autoLoginOrLoad = async () => {
      // Auto-authenticate as default admin/officer if not already logged in
      if (!authService.isAuthenticated()) {
        try {
          const data = await authService.login('admin', 'admin123');
          setUser(data.user || authService.getStoredUser());
          setLoading(false);
          return;
        } catch (e) {
          console.warn('Auto-login with default credentials failed:', e);
        }
      } else {
        try {
          const userData = await authService.getMe();
          setUser(userData);
        } catch {
          // If token expired, auto-relogin
          try {
            const data = await authService.login('admin', 'admin123');
            setUser(data.user || authService.getStoredUser());
          } catch {
            authService.logout();
            setUser(null);
          }
        }
      }
      setLoading(false);
    };

    autoLoginOrLoad();
  }, []);

  const login = useCallback(async (username, password) => {
    const data = await authService.login(username, password);
    setUser(data.user || authService.getStoredUser());
    return data;
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, []);

  const hasRole = useCallback(
    (role) => {
      if (!user) return false;
      return user.role === role;
    },
    [user]
  );

  const isAuthenticated = !!user && authService.isAuthenticated();

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasRole, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
