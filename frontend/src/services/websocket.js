/**
 * WebSocket Service for Real-time Updates
 * Handles live data streaming from backend
 */

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000;
    this.listeners = new Map();
    this.isConnecting = false;
    this.shouldReconnect = true;
    this.pingInterval = null;
  }

  /**
   * Connect to WebSocket
   */
  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      console.log('WebSocket already connected or connecting');
      return;
    }

    this.isConnecting = true;
    const wsUrl = `${WS_BASE_URL}/ws/live-feed`;
    
    console.log('Connecting to WebSocket:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.emit('connected', { timestamp: new Date() });
        this.startPingInterval();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message:', data.type);
          
          // Emit to specific listeners
          this.emit(data.type, data);
          
          // Emit to general message listeners
          this.emit('message', data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.emit('error', error);
      };

      this.ws.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason);
        this.isConnecting = false;
        this.stopPingInterval();
        this.emit('disconnected', { code: event.code, reason: event.reason });

        // Attempt reconnection
        if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`Reconnecting... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
          setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.isConnecting = false;
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    this.shouldReconnect = false;
    this.stopPingInterval();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    console.log('WebSocket disconnected');
  }

  /**
   * Send message to server
   */
  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected. Cannot send message.');
    }
  }

  /**
   * Subscribe to event
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => this.off(event, callback);
  }

  /**
   * Unsubscribe from event
   */
  off(event, callback) {
    if (!this.listeners.has(event)) return;

    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    
    if (index > -1) {
      callbacks.splice(index, 1);
    }

    if (callbacks.length === 0) {
      this.listeners.delete(event);
    }
  }

  /**
   * Emit event to listeners
   */
  emit(event, data) {
    if (!this.listeners.has(event)) return;

    this.listeners.get(event).forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in ${event} listener:`, error);
      }
    });
  }

  /**
   * Start ping interval to keep connection alive
   */
  startPingInterval() {
    this.stopPingInterval();
    
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send('ping');
      }
    }, 30000); // Ping every 30 seconds
  }

  /**
   * Stop ping interval
   */
  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Get connection state
   */
  getState() {
    if (!this.ws) return 'CLOSED';
    
    const states = {
      [WebSocket.CONNECTING]: 'CONNECTING',
      [WebSocket.OPEN]: 'OPEN',
      [WebSocket.CLOSING]: 'CLOSING',
      [WebSocket.CLOSED]: 'CLOSED',
    };
    
    return states[this.ws.readyState] || 'UNKNOWN';
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Force reconnect
   */
  reconnect() {
    this.disconnect();
    this.shouldReconnect = true;
    this.reconnectAttempts = 0;
    setTimeout(() => this.connect(), 1000);
  }
}

// Create singleton instance
const wsService = new WebSocketService();

export default wsService;

// ===== HOOK FOR REACT COMPONENTS =====

/**
 * React hook for WebSocket subscriptions
 * Usage:
 * 
 * const { data, isConnected } = useWebSocketEvent('status_update', (data) => {
 *   console.log('Status:', data);
 * });
 */
export const useWebSocketEvent = (event, callback, deps = []) => {
  const [data, setData] = React.useState(null);
  const [isConnected, setIsConnected] = React.useState(wsService.isConnected());

  React.useEffect(() => {
    // Subscribe to event
    const unsubscribe = wsService.on(event, (eventData) => {
      setData(eventData);
      if (callback) callback(eventData);
    });

    // Subscribe to connection status
    const unsubscribeConnected = wsService.on('connected', () => {
      setIsConnected(true);
    });

    const unsubscribeDisconnected = wsService.on('disconnected', () => {
      setIsConnected(false);
    });

    return () => {
      unsubscribe();
      unsubscribeConnected();
      unsubscribeDisconnected();
    };
  }, [event, ...deps]);

  return { data, isConnected };
};
