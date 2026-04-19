/**
 * Zustand risk store — global state for risk scores, alerts, and connection status.
 */

import { create } from 'zustand';
import type { Alert, ConnectionStatus, RiskScore } from '../lib/types';

interface RiskState {
  // State
  scores: RiskScore[];
  alerts: Alert[];
  connectionStatus: ConnectionStatus;
  lastUpdated: string | null;
  isChatOpen: boolean;

  // Actions
  setScores: (scores: RiskScore[]) => void;
  addAlert: (alert: Alert) => void;
  setAlerts: (alerts: Alert[]) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setLastUpdated: (ts: string) => void;
  toggleChat: () => void;
  setChatOpen: (open: boolean) => void;
}

export const useRiskStore = create<RiskState>((set) => ({
  // Initial state
  scores: [],
  alerts: [],
  connectionStatus: 'offline',
  lastUpdated: null,
  isChatOpen: false,

  // Actions
  setScores: (scores) =>
    set({ scores, lastUpdated: new Date().toISOString() }),

  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts].slice(0, 100), // Keep latest 100
    })),

  setAlerts: (alerts) => set({ alerts }),

  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

  setLastUpdated: (lastUpdated) => set({ lastUpdated }),

  toggleChat: () => set((state) => ({ isChatOpen: !state.isChatOpen })),
  
  setChatOpen: (isChatOpen) => set({ isChatOpen }),
}));
