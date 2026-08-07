/**
 * WebSocket client with auto-reconnect and event subscription.
 * Connects to /ws/runtime/{clientId} and /ws/execution/{clientId}.
 */

import { WS_BASE } from './client';
import type { WSEvent, RuntimeWSEvent, ExecutionWSEvent } from './types';

type WSCallback = (event: WSEvent) => void;
type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

class WSConnection {
  private url: string;
  private ws: WebSocket | null = null;
  private callbacks: Set<WSCallback> = new Set();
  private statusCallbacks: Set<(status: WSStatus) => void> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 50;
  private _status: WSStatus = 'disconnected';
  private subscribeMessage: Record<string, unknown> | null = null;

  constructor(path: string) {
    this.url = `${WS_BASE}${path}`;
  }

  get status(): WSStatus {
    return this._status;
  }

  connect(subscribeMsg?: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.subscribeMessage = subscribeMsg || null;
    this.setStatus('connecting');

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.setStatus('connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;

        if (this.subscribeMessage) {
          this.ws?.send(JSON.stringify(this.subscribeMessage));
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WSEvent = JSON.parse(event.data);
          this.callbacks.forEach((cb) => cb(data));
        } catch {
          // Ignore malformed messages
        }
      };

      this.ws.onclose = () => {
        this.setStatus('disconnected');
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      this.setStatus('disconnected');
      this.scheduleReconnect();
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
    this.ws?.close();
    this.ws = null;
    this.setStatus('disconnected');
  }

  send(data: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  subscribe(callback: WSCallback): () => void {
    this.callbacks.add(callback);
    return () => this.callbacks.delete(callback);
  }

  onStatusChange(callback: (status: WSStatus) => void): () => void {
    this.statusCallbacks.add(callback);
    return () => this.statusCallbacks.delete(callback);
  }

  private setStatus(status: WSStatus) {
    this._status = status;
    this.statusCallbacks.forEach((cb) => cb(status));
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;

    this.setStatus('reconnecting');
    this.reconnectAttempts++;
    this.reconnectDelay = Math.min(
      this.reconnectDelay * 2,
      this.maxReconnectDelay,
    );

    this.reconnectTimer = setTimeout(() => {
      this.connect(this.subscribeMessage || undefined);
    }, this.reconnectDelay);
  }
}

// Singleton connections
let runtimeWs: WSConnection | null = null;
let executionWs: WSConnection | null = null;

export function getRuntimeWs(): WSConnection {
  if (!runtimeWs) {
    const clientId = `desktop-${Date.now().toString(36)}`;
    runtimeWs = new WSConnection(`/ws/runtime/${clientId}`);
  }
  return runtimeWs;
}

export function getExecutionWs(): WSConnection {
  if (!executionWs) {
    const clientId = `desktop-${Date.now().toString(36)}`;
    executionWs = new WSConnection(`/ws/execution/${clientId}`);
  }
  return executionWs;
}

export type { WSStatus, RuntimeWSEvent, ExecutionWSEvent };
