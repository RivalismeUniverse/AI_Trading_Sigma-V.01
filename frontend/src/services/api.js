/**
 * API Service for AI TRADING SIGMA 
 * Handles all HTTP requests to backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if exists
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message;
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);

// ===== API METHODS =====

const api = {
  // ===== HEALTH & STATUS =====
  async getHealth() {
    return apiClient.get('/health');
  },

  // ===== CHAT =====
  async sendChatMessage(message, context = {}) {
    return apiClient.post('/api/chat', {
      message,
      context,
    });
  },

  // ===== STRATEGY =====
  async createStrategy(userPrompt) {
    return apiClient.post('/api/strategy/create', {
      user_prompt: userPrompt,
    });
  },

  async applyStrategy(strategyConfig) {
    return apiClient.post('/api/strategy/apply', {
      strategy_config: strategyConfig,
    });
  },

  async listStrategies() {
    return apiClient.get('/api/strategy/list');
  },

  async getActiveStrategy() {
    return apiClient.get('/api/strategy/active');
  },

  // ===== TRADING CONTROL =====
  async startTrading() {
    return apiClient.post('/api/trading/start');
  },

  async stopTrading() {
    return apiClient.post('/api/trading/stop');
  },

  async getTradingStatus() {
    return apiClient.get('/api/trading/status');
  },

  // ===== PERFORMANCE =====
  async getPerformance() {
    return apiClient.get('/api/performance');
  },

  async getPerformanceHistory(hours = 24) {
    return apiClient.get(`/api/performance/history?hours=${hours}`);
  },

  // ===== TRADES =====
  async getTrades(limit = 50, symbol = null) {
    const params = new URLSearchParams({ limit });
    if (symbol) params.append('symbol', symbol);
    return apiClient.get(`/api/trades?${params}`);
  },

  async getOpenTrades(symbol = null) {
    const params = symbol ? `?symbol=${symbol}` : '';
    return apiClient.get(`/api/trades/open${params}`);
  },

  // ===== COMPLIANCE =====
  async getComplianceReport() {
    return apiClient.get('/api/compliance/report');
  },

  async getComplianceLogs(limit = 100) {
    return apiClient.get(`/api/compliance/logs?limit=${limit}`);
  },
};

export default api;

// ===== HELPER FUNCTIONS =====

/**
 * Format API error for display
 */
export const formatApiError = (error) => {
  if (error.response) {
    return error.response.data?.detail || 'Server error occurred';
  } else if (error.request) {
    return 'No response from server. Please check your connection.';
  } else {
    return error.message || 'An unexpected error occurred';
  }
};

/**
 * Check if API is available
 */
export const checkApiHealth = async () => {
  try {
    await api.getHealth();
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Retry failed request
 */
export const retryRequest = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
};
