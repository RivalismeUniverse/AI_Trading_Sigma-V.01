/**
 * WebSocket Service
 * Real-time updates from backend
 * Fixed: Automatic protocol switching and dynamic URL
 */

// Fungsi untuk mengubah URL HTTPS Railway menjadi WSS secara otomatis
const getWsUrl = () => {
  const envUrl = process.env.REACT_APP_WS_URL || process.env.REACT_APP_API_URL || 'ws://3.236.117.108:8000';
  
  // Jika URL mengandung http/https, ganti jadi ws/wss
  if (envUrl.startsWith('http')) {
    return envUrl.replace(/^http/, 'ws');
  }
  return envUrl;
};

const WS_BASE_URL = getWsUrl();

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.listeners = new Map();
    this.isConnected = false;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      // Menambahkan /ws/live-feed sesuai endpoint backend kamu
      const fullWsUrl = `${WS_BASE_URL}/ws/live-feed`;
      console.log('Connecting to WebSocket:', fullWsUrl);
      
      this.ws = new WebSocket(fullWsUrl);
      
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.notifyListeners('connection', { status: 'connected' });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.notifyListeners('error', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.notifyListeners('connection', { status: 'disconnected' });
        this.attemptReconnect();
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  handleMessage(data) {
    const { type, data: payload } = data;
    this.notifyListeners(type, payload);
    this.notifyListeners('all', data);
  }

  notifyListeners(eventType, data) {
    const listeners = this.listeners.get(eventType) || [];
    listeners.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in ${eventType} listener:`, error);
      }
    });
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
    return () => this.off(eventType, callback);
  }

  off(eventType, callback) {
    const listeners = this.listeners.get(eventType) || [];
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }

  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, cannot send data');
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  getConnectionStatus() {
    return this.isConnected;
  }
}

const websocketService = new WebSocketService();
export default websocketService;
