import axios from 'axios';

export const api = axios.create({
    baseURL: 'http://localhost:8000/api',
});

// Auth Interceptor
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const STATIC_URL = 'http://localhost:8000/static';
