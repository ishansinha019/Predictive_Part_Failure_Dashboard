import axios from 'axios';
import { store } from '../app/store';

const apiService = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
  });

// Interceptor to add the auth token to every request
apiService.interceptors.request.use(
  (config) => {
    const token = store.getState().auth.token;
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiService;