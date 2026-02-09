// [Feature: News Management] [Story: NM-ADMIN-001] [Ticket: NM-ADMIN-001-FE-T01]
// Axios HTTP client instance with centralized configuration

import axios, { type AxiosResponse, type InternalAxiosRequestConfig, type AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8005';

export const http = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for auth token injection (when implemented)
http.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        // TODO: Add auth token when User Management is implemented
        // const token = localStorage.getItem('access_token');
        // if (token) {
        //   config.headers.Authorization = `Bearer ${token}`;
        // }
        return config;
    },
    (error: AxiosError) => Promise.reject(error)
);

// Response interceptor for centralized error handling
http.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            // TODO: Handle unauthorized - redirect to login
            console.error('Unauthorized - session expired');
        }
        return Promise.reject(error);
    }
);
