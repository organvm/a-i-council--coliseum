import React from 'react';
import { act, render, waitFor } from '@testing-library/react';

import Home from '../page';
import { useColiseumStore } from '@/lib/store';
import { agentsApi, isColiseumSocketEvent, stateApi } from '@/lib/api';

// Mock child components to isolate Home testing.
jest.mock('@/components/ChatStream', () => ({ ChatStream: () => <div data-testid="chat-stream" /> }));
jest.mock('@/components/AgentGrid', () => ({ AgentGrid: () => <div data-testid="agent-grid" /> }));
jest.mock('@/components/VotingPanel', () => ({ VotingPanel: () => <div data-testid="voting-panel" /> }));
jest.mock('@/components/WalletConnectCustom', () => ({ WalletConnectCustom: () => <div data-testid="wallet-connect" /> }));
jest.mock('@/components/EventTicker', () => ({ EventTicker: () => <div data-testid="event-ticker" /> }));
jest.mock('@/components/Arena3D', () => ({ Arena3D: () => <div data-testid="arena-3d" /> }));
jest.mock('@/components/BattleScene', () => ({ BattleScene: () => <div data-testid="battle-scene" /> }));
jest.mock('@/components/DemoOverlay', () => ({ DemoOverlay: () => <div data-testid="demo-overlay" /> }));

jest.mock('@/lib/store', () => ({
  useColiseumStore: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  agentsApi: {
    list: jest.fn().mockResolvedValue({ data: [] }),
  },
  stateApi: {
    bootstrap: jest.fn().mockResolvedValue({
      data: {
        meta: { timestamp: '2026-02-25T00:00:00Z' },
        runtime: { orchestrator_running: true },
        agents: [],
        events: [],
        voting: { sessions: [] },
      },
    }),
  },
  isColiseumSocketEvent: jest.fn(),
}));

type MockSocketHandler = ((event?: unknown) => void) | null;

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  onopen: MockSocketHandler = null;
  onclose: MockSocketHandler = null;
  onerror: MockSocketHandler = null;
  onmessage: MockSocketHandler = null;
  url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.onclose?.();
  }
}

type MockStoreState = {
  [key: string]: unknown;
};

function createMockStoreState(): MockStoreState {
  return {
    setAgents: jest.fn(),
    setEvents: jest.fn(),
    setSessions: jest.fn(),
    addMessage: jest.fn(),
    addChatMessage: jest.fn(),
    addCombatLog: jest.fn(),
    addDemoMarker: jest.fn(),
    upsertEvent: jest.fn(),
    upsertVoteUpdate: jest.fn(),
    setSystemStatus: jest.fn(),
    setWsConnectionStatus: jest.fn(),
    wsConnectionStatus: 'connected',
    systemStatus: null,
    activeSessions: [],
    voteUpdatesBySession: {},
  };
}

describe('Home Page', () => {
  let mockStoreState: MockStoreState;

  beforeEach(() => {
    MockWebSocket.instances = [];
    mockStoreState = createMockStoreState();

    (useColiseumStore as unknown as jest.Mock).mockImplementation(
      (selector: (state: MockStoreState) => unknown) => selector(mockStoreState)
    );

    (isColiseumSocketEvent as unknown as jest.Mock).mockImplementation((value: unknown) => {
      if (!value || typeof value !== 'object') {
        return false;
      }
      const candidate = value as { type?: string; data?: unknown };
      if (typeof candidate.type !== 'string') {
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
      ].includes(candidate.type) && typeof candidate.data === 'object';
    });

    (global as unknown as { WebSocket: typeof MockWebSocket }).WebSocket = MockWebSocket as never;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the main layout and bootstraps state', async () => {
    const { getByText, getByTestId } = render(<Home />);

    expect(getByText('Active Council')).toBeInTheDocument();
    expect(getByTestId('agent-grid')).toBeInTheDocument();

    await waitFor(() => {
      expect(getByTestId('arena-3d')).toBeInTheDocument();
      expect(stateApi.bootstrap).toHaveBeenCalled();
    });

    expect((mockStoreState.setAgents as jest.Mock)).toHaveBeenCalled();
    expect((mockStoreState.setEvents as jest.Mock)).toHaveBeenCalled();
    expect((mockStoreState.setSessions as jest.Mock)).toHaveBeenCalled();
    expect(agentsApi.list).not.toHaveBeenCalled();
  });

  it('applies event_update and vote_update messages and ignores unsupported WS types', async () => {
    render(<Home />);

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    });
    const socket = MockWebSocket.instances[0];

    await act(async () => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: 'event_update',
          data: {
            event_id: 'evt_1',
            source: 'api',
            title: 'New Event',
            description: 'Event body',
            category: 'technology',
            timestamp: '2026-02-25T00:00:00Z',
          },
        }),
      });
    });

    expect((mockStoreState.upsertEvent as jest.Mock)).toHaveBeenCalledWith(
      expect.objectContaining({ event_id: 'evt_1', title: 'New Event' })
    );

    await act(async () => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: 'vote_update',
          data: {
            session_id: 'sess_1',
            title: 'Choose',
            status: 'active',
            options: ['a', 'b'],
            total_votes: 2,
            choice_weights: { a: 1, b: 1 },
            simulated: false,
          },
        }),
      });
    });

    expect((mockStoreState.upsertVoteUpdate as jest.Mock)).toHaveBeenCalledWith(
      expect.objectContaining({ session_id: 'sess_1', total_votes: 2 })
    );

    const upsertEventCallsBefore = (mockStoreState.upsertEvent as jest.Mock).mock.calls.length;
    const upsertVoteCallsBefore = (mockStoreState.upsertVoteUpdate as jest.Mock).mock.calls.length;

    await act(async () => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: 'unsupported_event',
          data: { ignored: true },
        }),
      });
    });

    expect((mockStoreState.upsertEvent as jest.Mock).mock.calls.length).toBe(upsertEventCallsBefore);
    expect((mockStoreState.upsertVoteUpdate as jest.Mock).mock.calls.length).toBe(upsertVoteCallsBefore);
  });
});
