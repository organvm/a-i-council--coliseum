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

describe('Arena3D', () => {
  it('renders correctly with agents', () => {
    (useColiseumStore as unknown as jest.Mock).mockReturnValue([
      { agent_id: '1', name: 'Alpha', role: 'debater' },
      { agent_id: '2', name: 'Beta', role: 'moderator' },
    ]);

    const { getByTestId, getByText } = render(<Arena3D />);
    
    expect(getByTestId('mock-canvas')).toBeInTheDocument();
    expect(getByText('Alpha')).toBeInTheDocument();
    expect(getByText('Beta')).toBeInTheDocument();
  });
});
