import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Arena3D } from '../Arena3D';
import { useColiseumStore } from '@/lib/store';

// Mock the React Three Fiber Canvas and Text to prevent WebGL errors in JSDOM
jest.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: any) => <div data-testid="mock-canvas">{children}</div>,
  useFrame: jest.fn(),
  useLoader: jest.fn(() => ({})), // mock texture
}));

jest.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
  Text: ({ children }: any) => <div>{children}</div>,
}));

// Mock the store
jest.mock('@/lib/store', () => ({
  useColiseumStore: jest.fn(),
}));

const originalConsoleError = console.error;

describe('Arena3D', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation((...args) => {
      const first = args[0];
      if (
        typeof first === 'string' &&
        (first.includes('incorrect casing') || first.includes('unrecognized in this browser'))
      ) {
        return;
      }
      originalConsoleError(...args);
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders correctly with agents', () => {
    (useColiseumStore as unknown as jest.Mock).mockImplementation((selector: any) =>
      selector({
        agents: [
          { agent_id: '1', name: 'Alpha', role: 'debater' },
          { agent_id: '2', name: 'Beta', role: 'moderator' },
        ],
        latestCombatEvent: null,
      })
    );

    const { getByTestId, getByText } = render(<Arena3D />);
    
    expect(getByTestId('mock-canvas')).toBeInTheDocument();
    expect(getByText('Alpha')).toBeInTheDocument();
    expect(getByText('Beta')).toBeInTheDocument();
  });
});
