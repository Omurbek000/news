import { createContext, useContext, useEffect, useState } from 'react';
import api from '../api/axios';

const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

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

  const login = async (username, password) => {
    const res = await api.post('/auth/login/', { username, password });
    localStorage.setItem('tokens', JSON.stringify({ access: res.data.access, refresh: res.data.refresh }));
    const userRes = await api.get('/users/me/');
    setUser(userRes.data);
    return res.data;
  };

  const register = (data) => api.post('/auth/register/', data);
  const logout = () => { localStorage.removeItem('tokens'); setUser(null); };
  const updateUser = (data) => api.patch('/users/me/', data).then(res => setUser(res.data));

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};