import { create } from 'zustand';
import type {
  Agent,
  ArenaEvent,
  ChatMessageEnvelope,
  CombatUpdateEvent,
  DemoMarkerEvent,
  Message,
  SystemStatusEvent,
  VoteUpdateEvent,
  VotingSessionSummary,
} from './api';

export type WsConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'disconnected'
  | 'error';

export interface ColiseumState {
  agents: Agent[];
  events: ArenaEvent[];
  messages: Message[];
  activeSessions: VotingSessionSummary[];
  chatMessages: ChatMessageEnvelope[];
  combatLogs: CombatUpdateEvent[];
  latestCombatEvent: CombatUpdateEvent | null;
  latestDemoMarker: DemoMarkerEvent | null;
  voteUpdatesBySession: Record<string, VoteUpdateEvent>;
  systemStatus: SystemStatusEvent | null;
  wsConnectionStatus: WsConnectionStatus;
  
  setAgents: (agents: Agent[]) => void;
  setEvents: (events: ArenaEvent[]) => void;
  upsertEvent: (event: ArenaEvent) => void;
  addMessage: (message: Message) => void;
  setSessions: (sessions: VotingSessionSummary[]) => void;
  addChatMessage: (msg: ChatMessageEnvelope) => void;
  addCombatLog: (log: CombatUpdateEvent) => void;
  addDemoMarker: (marker: DemoMarkerEvent) => void;
  upsertVoteUpdate: (update: VoteUpdateEvent) => void;
  setSystemStatus: (status: SystemStatusEvent) => void;
  setWsConnectionStatus: (status: WsConnectionStatus) => void;
}

export const useColiseumStore = create<ColiseumState>((set) => ({
  agents: [],
  events: [],
  messages: [],
  activeSessions: [],
  chatMessages: [],
  combatLogs: [],
  latestCombatEvent: null,
  latestDemoMarker: null,
  voteUpdatesBySession: {},
  systemStatus: null,
  wsConnectionStatus: 'connecting',
  
  setAgents: (agents) => set({ agents }),
  setEvents: (events) => set({ events }),
  upsertEvent: (event) =>
    set((state) => {
      const existing = state.events.filter((item) => item.event_id !== event.event_id);
      return {
        events: [event, ...existing].slice(0, 50),
      };
    }),
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages.slice(-49), message] 
  })),
  setSessions: (sessions) => set({ activeSessions: sessions }),
  addChatMessage: (msg) => set((state) => ({
    chatMessages: [...state.chatMessages.slice(-49), msg]
  })),
  addCombatLog: (log) => set((state) => ({
    combatLogs: [...state.combatLogs.slice(-19), log],
    latestCombatEvent: log
  })),
  addDemoMarker: (marker) => set({ latestDemoMarker: marker }),
  upsertVoteUpdate: (update) => set((state) => ({
    voteUpdatesBySession: {
      ...state.voteUpdatesBySession,
      [update.session_id]: update,
    },
  })),
  setSystemStatus: (status) => set({ systemStatus: status }),
  setWsConnectionStatus: (status) => set({ wsConnectionStatus: status }),
}));
