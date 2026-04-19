/**
 * useChatStream — WebSocket hook for Claude AI chat.
 *
 * Manages connection, message streaming, session persistence,
 * and replay loading.
 */
import { useState, useCallback, useRef, useEffect } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export type ChatRole = 'user' | 'assistant' | 'system';
export type ChatMode = 'simple' | 'advanced' | 'auto';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface ReplayInfo {
  id: string;
  name: string;
  description: string;
  period: string;
  frame_count: number;
}

export function useChatStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [replays, setReplays] = useState<ReplayInfo[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string>('');
  const streamBufferRef = useRef<string>('');

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_URL}/ws/chat`);

      ws.onopen = () => {
        setIsConnected(true);
        // Send init with session ID if we have one
        ws.send(JSON.stringify({
          type: 'init',
          session_id: sessionIdRef.current || undefined,
        }));
        // Request replay list
        ws.send(JSON.stringify({ type: 'list_replays' }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'session':
            sessionIdRef.current = data.session_id;
            break;

          case 'token':
            streamBufferRef.current += data.content;
            setMessages(prev => {
              const last = prev[prev.length - 1];
              if (last && last.isStreaming) {
                return [
                  ...prev.slice(0, -1),
                  { ...last, content: streamBufferRef.current },
                ];
              }
              return [
                ...prev,
                {
                  id: `asst-${Date.now()}`,
                  role: 'assistant',
                  content: streamBufferRef.current,
                  timestamp: new Date(),
                  isStreaming: true,
                },
              ];
            });
            break;

          case 'done':
            setIsStreaming(false);
            streamBufferRef.current = '';
            setMessages(prev => prev.map(m =>
              m.isStreaming ? { ...m, isStreaming: false } : m
            ));
            break;

          case 'system':
            setMessages(prev => [
              ...prev,
              {
                id: `sys-${Date.now()}`,
                role: 'system',
                content: data.message,
                timestamp: new Date(),
              },
            ]);
            break;

          case 'replays':
            setReplays(data.data || []);
            break;

          case 'replay_data':
            setMessages(prev => [
              ...prev,
              {
                id: `replay-${Date.now()}`,
                role: 'system',
                content: `📜 Crisis replay loaded: ${data.replay_id.replace(/_/g, ' ').toUpperCase()} (${data.frames.length} frames)`,
                timestamp: new Date(),
              },
            ]);
            break;
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsStreaming(false);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch {
      setIsConnected(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((content: string, mode: ChatMode = 'auto') => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connect();
      // Retry after short delay
      setTimeout(() => {
        wsRef.current?.send(JSON.stringify({
          type: 'message',
          content,
          mode,
        }));
      }, 500);
    } else {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        content,
        mode,
      }));
    }

    // Add user message immediately
    setMessages(prev => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date(),
      },
    ]);
    setIsStreaming(true);
    streamBufferRef.current = '';
  }, [connect]);

  const loadReplay = useCallback((replayId: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connect();
      setTimeout(() => {
        wsRef.current?.send(JSON.stringify({ type: 'replay', replay_id: replayId }));
      }, 500);
    } else {
      wsRef.current.send(JSON.stringify({ type: 'replay', replay_id: replayId }));
    }
    setIsStreaming(true);
    streamBufferRef.current = '';
  }, [connect]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    streamBufferRef.current = '';
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return {
    messages,
    isConnected,
    isStreaming,
    replays,
    sendMessage,
    loadReplay,
    clearMessages,
    connect,
  };
}
