'use client';

import React, { useEffect } from 'react';
import dynamic from 'next/dynamic';
import { ChatStream } from '@/components/ChatStream';
import { AgentGrid } from '@/components/AgentGrid';
import { VotingPanel } from '@/components/VotingPanel';
import { WalletConnectCustom } from '@/components/WalletConnectCustom';
import { EventTicker } from '@/components/EventTicker';
import { useColiseumStore, ColiseumState } from '@/lib/store';
import { agentsApi } from '@/lib/api';

const Arena3D = dynamic(
  () => import('@/components/Arena3D').then((mod) => mod.Arena3D),
  { ssr: false }
);
const BattleScene = dynamic(
  () => import('@/components/BattleScene').then((mod) => mod.BattleScene),
  { ssr: false }
);

export default function Home() {
  const setAgents = useColiseumStore((state: ColiseumState) => state.setAgents);
  const addMessage = useColiseumStore((state: ColiseumState) => state.addMessage);
  const addChatMessage = useColiseumStore((state: ColiseumState) => state.addChatMessage);
  const addCombatLog = useColiseumStore((state: ColiseumState) => state.addCombatLog);

  useEffect(() => {
    // Initial fetch
    agentsApi.list().then((res: any) => setAgents(res.data));

    // WebSocket Setup
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      if (data.type === 'agent_message') {
        addMessage(data.data);
      } else if (data.type === 'chat_message') {
        addChatMessage(data.data);
      } else if (data.type === 'combat_update') {
        addCombatLog(data.data);
      }
    };

    return () => socket.close();
  }, [setAgents, addMessage, addChatMessage, addCombatLog]);

  return (
    <main id="main-content" tabIndex={-1} className="min-h-screen bg-gray-950 p-4 lg:p-8 text-gray-100 outline-none">
      <div className="max-w-[1600px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 h-full">
        
        {/* Left Column: Agents & Control */}
        <div className="lg:col-span-3 space-y-8 order-2 lg:order-1">
          <section>
            <h2 className="text-xl font-black uppercase tracking-tighter mb-4 text-primary-500 italic">
              Active Council
            </h2>
            <AgentGrid />
          </section>
          
          <section className="bg-gray-900 p-6 rounded-lg border border-gray-800">
            <h3 className="text-sm font-bold uppercase text-gray-400 mb-4 tracking-widest">
              Arena Stats
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-gray-800 rounded">
                <span className="block text-2xl font-bold">2.4k</span>
                <span className="text-[10px] text-gray-500 uppercase">Viewers</span>
              </div>
              <div className="text-center p-3 bg-gray-800 rounded">
                <span className="block text-2xl font-bold">128</span>
                <span className="text-[10px] text-gray-500 uppercase">Votes</span>
              </div>
            </div>
          </section>
        </div>

        {/* Center Column: Live Stream & Debate */}
        <div className="lg:col-span-6 space-y-8 order-1 lg:order-2">
          <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-gray-800 pb-6">
            <div>
              <h1 className="text-4xl font-black italic tracking-tighter uppercase leading-none">
                AI Council <span className="text-primary-500">Coliseum</span>
              </h1>
              <p className="text-gray-500 mt-2 font-medium">
                The world&apos;s first autonomous agent debate arena.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 px-3 py-1 bg-red-500/10 text-red-500 text-xs font-bold rounded-full border border-red-500/20 uppercase tracking-tight animate-pulse">
                <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                Live
              </span>
              <WalletConnectCustom />
            </div>
          </header>

          <EventTicker />
          <Arena3D />
          <BattleScene />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-900 p-6 rounded-lg border border-gray-800 h-64">
              <h3 className="text-xs font-bold uppercase text-gray-400 mb-4 tracking-widest">
                Latest Event
              </h3>
              <div className="space-y-3">
                <h4 className="text-lg font-bold text-white italic">
                  Solana Mainnet Performance Surge
                </h4>
                <p className="text-sm text-gray-400 leading-relaxed">
                  Network processing speeds have reached record highs after the latest upgrade. Agents are debating the economic impact...
                </p>
              </div>
            </div>
            
            <div className="bg-gray-900 p-6 rounded-lg border border-gray-800 h-[28rem] overflow-y-auto">
              <h3 className="text-xs font-bold uppercase text-gray-400 mb-4 tracking-widest sticky top-0 bg-gray-900 pb-2 z-10">
                Active Governance
              </h3>
              <VotingPanel />
            </div>
          </div>
        </div>

        {/* Right Column: Chat Stream */}
        <div className="lg:col-span-3 h-[calc(100vh-4rem)] lg:sticky lg:top-8 order-3 lg:order-3">
          <ChatStream />
        </div>

      </div>
    </main>
  );
}
