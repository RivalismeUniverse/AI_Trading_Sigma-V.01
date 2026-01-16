/**
 * API Service
 * Centralized API calls to backend
 * Fixed: Dynamic URL for Railway & Vercel
 */

import axios from 'axios';

// Pencarian URL Backend otomatis:
// 1. Cek Environment Variable Vercel (REACT_APP_API_URL)
// 2. Kalau gak ada, pakai link Railway kamu langsung
const API_URL = process.env.REACT_APP_API_URL || 'http://3.236.117.108:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 
    'Content-Type': 'application/json'
  }
});

// Response interceptor untuk menangani data dan error
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error.response?.data || error.message);
  }
);

/** --- ENDPOINTS --- **/

// Health & Status
export const getHealth = () => api.get('/api/health');
export const getTradingStatus = () => api.get('/api/trading/status');

// Trading Control
export const startTrading = () => api.post('/api/trading/start');
export const stopTrading = () => api.post('/api/trading/stop');

// AI Chat
export const sendChatMessage = (message, history = []) => 
  api.post('/api/chat', { message, history });

// Strategy
export const createStrategy = (prompt) => 
  api.post('/api/strategy/create', { prompt });

export const applyStrategy = (strategyId) => 
  api.post('/api/strategy/apply', { strategy_id: strategyId });

export const listStrategies = () => api.get('/api/strategy/list');
export const getActiveStrategy = () => api.get('/api/strategy/active');

// Performance
export const getPerformance = () => api.get('/api/performance');
export const getPerformanceHistory = (days = 7) => 
  api.get(`/api/performance/history?days=${days}`);

// Trades
export const getTrades = (limit = 50, offset = 0) => 
  api.get(`/api/trades?limit=${limit}&offset=${offset}`);

export const getOpenPositions = () => api.get('/api/trades/open');

// Balance
export const getBalance = () => api.get('/api/balance');

// Circuit Breaker
export const getCircuitBreakerStatus = () => 
  api.get('/api/circuit-breaker/status');

export const getCircuitBreakerIssues = (minutes = 5) => 
  api.get(`/api/circuit-breaker/issues?minutes=${minutes}`);

export const forceCircuitBreakerRecovery = () => 
  api.post('/api/circuit-breaker/recover');

export const toggleCircuitBreakerOverride = (enabled, reason = '') => 
  api.post('/api/circuit-breaker/override', { enabled, reason });

// Notifications
export const getNotifications = (limit = 20) => 
  api.get(`/api/notifications?limit=${limit}`);

export const markNotificationRead = (notificationId) => 
  api.post(`/api/notifications/${notificationId}/read`);

export const clearNotifications = () => 
  api.delete('/api/notifications');

// Compliance
export const getComplianceReport = () => 
  api.get('/api/compliance/report');

export default api;
