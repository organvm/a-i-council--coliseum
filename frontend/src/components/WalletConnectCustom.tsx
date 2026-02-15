'use client';

import React, { useEffect } from 'react';
import { useWallet } from '@solana/wallet-adapter-react';
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui';
import { api } from '@/lib/api';

export const WalletConnectCustom: React.FC = () => {
  const { publicKey, connected } = useWallet();

  useEffect(() => {
    if (connected && publicKey) {
      // Automatically link wallet to user profile when connected
      linkWallet(publicKey.toBase58());
    }
  }, [connected, publicKey]);

  const linkWallet = async (address: string) => {
    try {
      await api.post('/api/users/link-solana', { solana_address: address });
      console.log('Wallet linked successfully');
      // Trigger tier refresh
      await api.post('/api/users/refresh-tier');
    } catch (err) {
      console.error('Failed to link wallet', err);
    }
  };

  return (
    <div className="custom-wallet-button">
      <WalletMultiButton className="!bg-primary-600 !hover:bg-primary-700 !text-xs !font-bold !uppercase !tracking-widest !rounded !h-9 !px-4" />
    </div>
  );
};
