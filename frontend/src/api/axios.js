import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8080/api/';

const api = axios.create({
  baseURL: API_URL,
});

const getTokens = () => {
  try {
    return JSON.parse(localStorage.getItem('tokens') || '{}');
  } catch {
    return {};
  }
};

const setTokens = (tokens) => {
  localStorage.setItem('tokens', JSON.stringify(tokens));
};

const clearTokens = () => {
  localStorage.removeItem('tokens');
};

let refreshPromise = null;

const refreshAccessToken = (refresh) => {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${API_URL}auth/token/refresh/`, { refresh })
      .then(res => {
        const tokens = {
          access: res.data.access,
          refresh: res.data.refresh || refresh,
        };
        setTokens(tokens);
        return tokens.access;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

api.interceptors.request.use(config => {
  const { access } = getTokens();
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

api.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config;
    const status = error.response?.status;
    const { refresh } = getTokens();
    const isAuthRequest =
      original?.url?.includes('/auth/login/') ||
      original?.url?.includes('/auth/register/') ||
      original?.url?.includes('/auth/token/refresh/');

    if (status !== 401 || !refresh || original?._retry || isAuthRequest) {
      return Promise.reject(error);
    }

    original._retry = true;
    try {
      const access = await refreshAccessToken(refresh);
      original.headers = original.headers || {};
      original.headers.Authorization = `Bearer ${access}`;
      return api(original);
    } catch (refreshError) {
      clearTokens();
      window.dispatchEvent(new Event('auth:logout'));
      return Promise.reject(refreshError);
    }
  }
);

export default api;
