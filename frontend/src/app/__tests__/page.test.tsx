import React from 'react';
import { render, waitFor } from '@testing-library/react';
import Home from '../page';
import { useColiseumStore } from '@/lib/store';
import { agentsApi } from '@/lib/api';

// Mock child components to isolate Home testing
jest.mock('@/components/ChatStream', () => ({ ChatStream: () => <div data-testid="chat-stream" /> }));
jest.mock('@/components/AgentGrid', () => ({ AgentGrid: () => <div data-testid="agent-grid" /> }));
jest.mock('@/components/VotingPanel', () => ({ VotingPanel: () => <div data-testid="voting-panel" /> }));
jest.mock('@/components/WalletConnectCustom', () => ({ WalletConnectCustom: () => <div data-testid="wallet-connect" /> }));
jest.mock('@/components/EventTicker', () => ({ EventTicker: () => <div data-testid="event-ticker" /> }));
jest.mock('@/components/Arena3D', () => ({ Arena3D: () => <div data-testid="arena-3d" /> }));
jest.mock('@/components/BattleScene', () => ({ BattleScene: () => <div data-testid="battle-scene" /> }));

// Mock the store
jest.mock('@/lib/store', () => ({
  useColiseumStore: jest.fn(),
}));

// Mock API
jest.mock('@/lib/api', () => ({
  agentsApi: {
    list: jest.fn().mockResolvedValue({ data: [] }),
  },
}));

describe('Home Page', () => {
  beforeEach(() => {
    (useColiseumStore as unknown as jest.Mock).mockImplementation((selector) => {
      // Return a dummy function for setAgents and addMessage
      return jest.fn();
    });
  });

  it('renders the main layout correctly', async () => {
    const { getByText, getByTestId } = render(<Home />);
    
    expect(getByText('Active Council')).toBeInTheDocument();
    expect(getByTestId('agent-grid')).toBeInTheDocument();
    expect(getByTestId('arena-3d')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(agentsApi.list).toHaveBeenCalled();
    });
  });
});
