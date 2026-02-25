import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add auth token
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token'); // allow-secret
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export interface AgentState {
  agent_id: string;
  role: string;
  is_active: boolean;
  memory?: {
    portrait_url?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface Agent {
  agent_id: string;
  name: string;
  role: string;
  is_active: boolean;
  state: AgentState;
}

export interface Message {
  sender_id: string;
  recipient_id: string | null;
  content: string;
  timestamp: string;
  message_id: string;
  metadata?: any;
}

export interface ArenaEvent {
  event_id: string;
  source: string;
  title: string;
  description: string;
  category?: string | null;
  tags?: string[];
  timestamp: string;
}

export type VoteChoice =
  | string
  | number
  | boolean
  | null
  | Record<string, unknown>;

export interface VotingSessionSummary {
  session_id: string;
  title: string;
  description: string;
  status: string;
  vote_type: string;
  options: VoteChoice[];
  total_votes: number;
  starts_at: string;
  ends_at?: string | null;
}

export interface VoteSubmissionResponse {
  vote_id: string;
  session_id: string;
  user_id: string;
  status: string;
}

export interface ChatMessageEnvelope {
  user: string;
  message: string;
}

export interface CombatUpdateEvent {
  attacker_id?: string;
  defender_id?: string;
  attacker_name?: string;
  defender_name?: string;
  is_hit?: boolean;
  is_fatality?: boolean;
  damage?: number;
  log?: string;
  timestamp?: string;
  [key: string]: unknown;
}

export interface DemoMarkerEvent {
  marker: string;
  title: string;
  subtitle?: string | null;
  severity?: 'info' | 'warning' | 'success' | 'error' | string;
  director_mode?: boolean;
  scenario?: string | null;
  run_id?: string | null;
  beat_index?: number;
  timestamp?: string;
}

export interface VoteUpdateEvent {
  session_id: string;
  title: string;
  status: string;
  options?: string[];
  total_votes: number;
  choice_weights?: Record<string, number>;
  results?: Record<string, unknown> | null;
  simulated?: boolean;
  director_mode?: boolean;
  timestamp?: string;
}

export interface EventUpdateEvent extends ArenaEvent {}

export interface SystemStatusEvent {
  phase: string;
  timestamp: string;
  mode?: 'director' | 'autonomous' | string;
  orchestrator_running?: boolean;
  arena_worker_running?: boolean;
  twitch_listener_running?: boolean;
  director?: Record<string, unknown> | null;
  websocket?: Record<string, unknown>;
}

export interface ColiseumSocketEnvelopeBase {
  version?: string;
  source?: string;
  timestamp?: string;
  event_id?: string;
  sequence?: number;
}

export type ColiseumSocketEvent =
  | ({ type: 'agent_message'; data: Message } & ColiseumSocketEnvelopeBase)
  | ({ type: 'chat_message'; data: ChatMessageEnvelope } & ColiseumSocketEnvelopeBase)
  | ({ type: 'combat_update'; data: CombatUpdateEvent } & ColiseumSocketEnvelopeBase)
  | ({ type: 'demo_marker'; data: DemoMarkerEvent } & ColiseumSocketEnvelopeBase)
  | ({ type: 'event_update'; data: EventUpdateEvent } & ColiseumSocketEnvelopeBase)
  | ({ type: 'vote_update'; data: VoteUpdateEvent } & ColiseumSocketEnvelopeBase)
  | ({ type: 'system_status'; data: SystemStatusEvent } & ColiseumSocketEnvelopeBase);

function isObject(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object';
}

export function isColiseumSocketEvent(value: unknown): value is ColiseumSocketEvent {
  if (!isObject(value) || typeof value.type !== 'string' || !isObject(value.data)) {
    return false;
  }
  return [
    'agent_message',
    'chat_message',
    'combat_update',
    'demo_marker',
    'event_update',
    'vote_update',
    'system_status',
  ].includes(value.type);
}

export const agentsApi = {
  list: () => api.get<Agent[]>('/api/agents'),
  get: (id: string) => api.get<Agent>(`/api/agents/${id}`),
};

export const votingApi = {
  listSessions: () => api.get<VotingSessionSummary[]>('/api/voting/sessions'),
  castVote: (sessionId: string, choice: VoteChoice) =>
    api.post<VoteSubmissionResponse>(`/api/voting/sessions/${sessionId}/vote`, { choice }),
};

export const eventsApi = {
  list: (limit = 10) => api.get<ArenaEvent[]>(`/api/events?limit=${limit}`),
};

export interface BootstrapStateResponse {
  meta: {
    timestamp: string;
    frontend_url?: string;
    director_enabled?: boolean;
  };
  runtime?: {
    orchestrator_running?: boolean;
    director?: Record<string, unknown> | null;
  };
  agents?: Agent[];
  events?: ArenaEvent[];
  voting?: {
    sessions?: VotingSessionSummary[];
  };
}

export const stateApi = {
  bootstrap: () => api.get<BootstrapStateResponse>('/api/state/bootstrap'),
};
