import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import api from '../api/axios';

const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
    if (tokens.access) {
      api.get('/users/me/')
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('tokens');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else setLoading(false);
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await api.get('/messages/');
      const msgs = res.data.results || res.data;
      const count = msgs.filter(m => m.is_read === false && m.recipient_username === user?.username).length;
      setUnreadCount(count);
    } catch { /* ignore */ }
  }, [user]);

  useEffect(() => {
    if (user) fetchUnreadCount();
  }, [user, fetchUnreadCount]);

  const login = async (username, password) => {
    const res = await api.post('/auth/login/', { username, password });
    localStorage.setItem('tokens', JSON.stringify({ access: res.data.access, refresh: res.data.refresh }));
    const userRes = await api.get('/users/me/');
    setUser(userRes.data);
    return res.data;
  };

  const register = (data) => api.post('/auth/register/', data);
  const logout = () => { localStorage.removeItem('tokens'); setUser(null); setUnreadCount(0); };
  const updateUser = (data) => api.patch('/users/me/', data).then(res => setUser(res.data));

  const uploadAvatar = async (file) => {
    const formData = new FormData();
    formData.append('avatar', file);
    const res = await api.patch('/users/me/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    setUser(res.data);
    return res.data;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser, uploadAvatar, unreadCount }}>
      {children}
    </AuthContext.Provider>
  );
};