/**
 * WebSocket hook — connects to the CrisisLens dashboard stream.
 *
 * Features:
 * - Exponential backoff reconnect (1s → 2s → 4s → max 30s)
 * - Auto-dispatches to Zustand store on message
 * - Returns connection status and last message
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useRiskStore } from '../store/useRiskStore';
import type { ConnectionStatus, WSMessage } from '../lib/types';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
const WS_URL = `${WS_BASE}/ws/dashboard`;

const MIN_BACKOFF_MS = 1_000;
const MAX_BACKOFF_MS = 30_000;

interface UseRiskStreamReturn {
  status: ConnectionStatus;
  lastMessage: WSMessage | null;
}

export function useRiskStream(): UseRiskStreamReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const backoffRef = useRef(MIN_BACKOFF_MS);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const setScores = useRiskStore((s) => s.setScores);
  const addAlert = useRiskStore((s) => s.addAlert);
  const setConnectionStatus = useRiskStore((s) => s.setConnectionStatus);
  const setLastUpdated = useRiskStore((s) => s.setLastUpdated);

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to', WS_URL);
        setConnectionStatus('live');
        backoffRef.current = MIN_BACKOFF_MS; // Reset backoff on success
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);
          setLastMessage(msg);
          setLastUpdated(new Date().toISOString());

          // Dispatch to store based on message type
          switch (msg.type) {
            case 'score_update':
              if (Array.isArray(msg.data)) {
                setScores(msg.data);
              }
              break;
            case 'alert':
              addAlert(msg.data as any);
              break;
            default:
              break;
          }
        } catch (e) {
          console.warn('[WS] Failed to parse message:', e);
        }
      };

      ws.onclose = (event) => {
        console.log('[WS] Disconnected, code:', event.code);
        setConnectionStatus('reconnecting');
        scheduleReconnect();
      };

      ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        ws.close();
      };
    } catch (e) {
      console.error('[WS] Connection failed:', e);
      setConnectionStatus('offline');
      scheduleReconnect();
    }
  }, [setScores, addAlert, setConnectionStatus, setLastUpdated]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }

    const delay = backoffRef.current;
    console.log(`[WS] Reconnecting in ${delay}ms...`);

    reconnectTimerRef.current = setTimeout(() => {
      // Exponential backoff: 1s → 2s → 4s → ... → max 30s
      backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF_MS);
      connect();
    }, delay);
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const status = useRiskStore((s) => s.connectionStatus);

  return { status, lastMessage };
}
