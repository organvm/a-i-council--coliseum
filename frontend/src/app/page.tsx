'use client';

import React, { useEffect } from 'react';
import dynamic from 'next/dynamic';
import { ChatStream } from '@/components/ChatStream';
import { AgentGrid } from '@/components/AgentGrid';
import { VotingPanel } from '@/components/VotingPanel';
import { WalletConnectCustom } from '@/components/WalletConnectCustom';
import { EventTicker } from '@/components/EventTicker';
import { DemoOverlay } from '@/components/DemoOverlay';
import { useColiseumStore, ColiseumState } from '@/lib/store';
import { agentsApi, isColiseumSocketEvent, stateApi } from '@/lib/api';

const Arena3D = dynamic(
  () => import('@/components/Arena3D').then((mod) => mod.Arena3D),
  { ssr: false }
);
const BattleScene = dynamic(
  () => import('@/components/BattleScene').then((mod) => mod.BattleScene),
  { ssr: false }
);

type Arena3DMode = 'on' | 'off' | 'auto';

function getRuntimeArena3DModeOverride(): Arena3DMode | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const raw = new URLSearchParams(window.location.search).get('arena3d');
  const normalized = (raw || '').toLowerCase();
  if (normalized === 'on' || normalized === 'off' || normalized === 'auto') {
    return normalized;
  }
  return null;
}

function resolveArena3DMode(): Arena3DMode {
  const runtimeOverride = getRuntimeArena3DModeOverride();
  if (runtimeOverride) {
    return runtimeOverride;
  }
  if (process.env.NEXT_PUBLIC_DISABLE_ARENA_3D === 'true') {
    return 'off';
  }
  const raw = (process.env.NEXT_PUBLIC_ARENA_3D_MODE || '').toLowerCase();
  if (raw === 'on' || raw === 'off' || raw === 'auto') {
    return raw;
  }
  return process.env.NEXT_PUBLIC_CAPTURE_PROFILE === 'recording' ? 'auto' : 'on';
}

const arena3DMode = resolveArena3DMode();

function Arena3DFallbackPanel({ reason }: { reason: 'manual' | 'error' }) {
  const title =
    reason === 'error' ? 'Arena Render Auto-Fallback' : 'Arena Render Paused';
  const subtitle =
    reason === 'error'
      ? 'Arena3D encountered a runtime error during capture and was automatically replaced to keep recording stable.'
      : '3D scene is temporarily disabled in demo capture mode to avoid browser/runtime incompatibilities during recording.';

  return (
    <section
      data-testid="arena-3d-fallback"
      className="w-full h-96 rounded-lg border border-gray-800 bg-gradient-to-br from-gray-950 via-gray-900 to-black overflow-hidden relative"
    >
      <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_20%_20%,rgba(239,68,68,0.35),transparent_45%),radial-gradient(circle_at_80%_30%,rgba(59,130,246,0.25),transparent_40%),radial-gradient(circle_at_50%_80%,rgba(16,185,129,0.2),transparent_45%)]" />
      <div className="relative h-full flex items-center justify-center">
        <div className="text-center max-w-xl px-6">
          <p className="text-[11px] tracking-[0.2em] uppercase text-amber-400 font-black">
            Capture Stability Mode
          </p>
          <h3 className="mt-3 text-3xl md:text-4xl font-black italic uppercase tracking-tight">
            {title}
          </h3>
          <p className="mt-4 text-sm text-gray-300 leading-relaxed">
            {subtitle} Combat and governance overlays remain live.
          </p>
          <div className="mt-5 inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-200 text-xs font-bold uppercase tracking-[0.12em]">
            Battle Feed Active
          </div>
        </div>
      </div>
    </section>
  );
}

class Arena3DErrorBoundary extends React.Component<
  { fallback: React.ReactNode; children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { fallback: React.ReactNode; children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    // Prevent recording from dying when the optional 3D layer fails in some browser/runtime combos.
    console.error('Arena3D failed; switching to fallback panel', error);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

export default function Home() {
  const setAgents = useColiseumStore((state: ColiseumState) => state.setAgents);
  const setEvents = useColiseumStore((state: ColiseumState) => state.setEvents);
  const setSessions = useColiseumStore((state: ColiseumState) => state.setSessions);
  const addMessage = useColiseumStore((state: ColiseumState) => state.addMessage);
  const addChatMessage = useColiseumStore((state: ColiseumState) => state.addChatMessage);
  const addCombatLog = useColiseumStore((state: ColiseumState) => state.addCombatLog);
  const addDemoMarker = useColiseumStore((state: ColiseumState) => state.addDemoMarker);
  const upsertEvent = useColiseumStore((state: ColiseumState) => state.upsertEvent);
  const upsertVoteUpdate = useColiseumStore((state: ColiseumState) => state.upsertVoteUpdate);
  const setSystemStatus = useColiseumStore((state: ColiseumState) => state.setSystemStatus);
  const setWsConnectionStatus = useColiseumStore((state: ColiseumState) => state.setWsConnectionStatus);
  const wsConnectionStatusRaw = useColiseumStore((state: ColiseumState) => state.wsConnectionStatus);
  const systemStatusRaw = useColiseumStore((state: ColiseumState) => state.systemStatus);
  const activeSessionsRaw = useColiseumStore((state: ColiseumState) => state.activeSessions);
  const voteUpdatesBySessionRaw = useColiseumStore((state: ColiseumState) => state.voteUpdatesBySession);

  const wsConnectionStatus =
    typeof wsConnectionStatusRaw === 'string' ? wsConnectionStatusRaw : 'connecting';
  const systemStatus =
    systemStatusRaw && typeof systemStatusRaw === 'object' ? systemStatusRaw : null;
  const activeSessions = Array.isArray(activeSessionsRaw) ? activeSessionsRaw : [];
  const voteUpdatesBySession =
    voteUpdatesBySessionRaw && typeof voteUpdatesBySessionRaw === 'object'
      ? voteUpdatesBySessionRaw
      : {};

  const liveVoteTotal = Object.values(voteUpdatesBySession).reduce((sum, update: any) => {
    const totalVotes = typeof update?.total_votes === 'number' ? update.total_votes : 0;
    return sum + totalVotes;
  }, 0);
  const modeLabel = (systemStatus?.mode || 'autonomous').toString();

  useEffect(() => {
    let isDisposed = false;
    let reconnectTimer: number | null = null;
    let reconnectAttempt = 0;
    let socket: WebSocket | null = null;

    const bootstrap = async () => {
      try {
        const res = await stateApi.bootstrap();
        if (isDisposed) return;
        if (Array.isArray(res.data?.agents)) {
          setAgents(res.data.agents);
        }
        if (Array.isArray(res.data?.events)) {
          setEvents(res.data.events);
        }
        if (Array.isArray(res.data?.voting?.sessions)) {
          setSessions(res.data.voting.sessions);
        }
        if (res.data?.runtime?.director || res.data?.runtime?.orchestrator_running !== undefined) {
          setSystemStatus({
            phase: 'bootstrap',
            timestamp: res.data.meta?.timestamp || new Date().toISOString(),
            mode:
              (res.data.runtime?.director &&
                (res.data.runtime.director as any)?.is_running &&
                'director') ||
              'autonomous',
            orchestrator_running: !!res.data.runtime?.orchestrator_running,
            director: res.data.runtime?.director || null,
          });
        }
      } catch {
        // Fallback to legacy endpoint shape for resilience.
        agentsApi.list().then((res: any) => {
          if (!isDisposed) setAgents(res.data);
        });
      }
    };

    const connect = (isReconnect: boolean) => {
      if (isDisposed) return;
      setWsConnectionStatus(isReconnect ? 'reconnecting' : 'connecting');
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        reconnectAttempt = 0;
        setWsConnectionStatus('connected');
      };

      socket.onerror = () => {
        setWsConnectionStatus('error');
      };

      socket.onclose = () => {
        if (isDisposed) {
          setWsConnectionStatus('disconnected');
          return;
        }
        setWsConnectionStatus('reconnecting');
        const delay = Math.min(5000, 500 * 2 ** reconnectAttempt);
        reconnectAttempt += 1;
        reconnectTimer = window.setTimeout(() => connect(true), delay);
      };

      socket.onmessage = (event: MessageEvent) => {
        let parsed: unknown;
        try {
          parsed = JSON.parse(event.data);
        } catch {
          return;
        }

        if (!isColiseumSocketEvent(parsed)) {
          return;
        }

        if (parsed.type === 'agent_message') {
          addMessage(parsed.data);
        } else if (parsed.type === 'chat_message') {
          addChatMessage(parsed.data);
        } else if (parsed.type === 'combat_update') {
          addCombatLog(parsed.data);
        } else if (parsed.type === 'demo_marker') {
          addDemoMarker(parsed.data);
        } else if (parsed.type === 'event_update') {
          upsertEvent(parsed.data);
        } else if (parsed.type === 'vote_update') {
          upsertVoteUpdate(parsed.data);
        } else if (parsed.type === 'system_status') {
          setSystemStatus(parsed.data);
        }
      };
    };

    bootstrap();

    // WebSocket Setup with reconnect
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    connect(false);

    return () => {
      isDisposed = true;
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      socket?.close();
    };
  }, [
    setAgents,
    setEvents,
    setSessions,
    addMessage,
    addChatMessage,
    addCombatLog,
    addDemoMarker,
    upsertEvent,
    upsertVoteUpdate,
    setSystemStatus,
    setWsConnectionStatus,
  ]);

  return (
    <main id="main-content" tabIndex={-1} className="min-h-screen bg-gray-950 p-4 lg:p-8 text-gray-100 outline-none">
      <DemoOverlay />
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
              Arena Telemetry
            </h3>
            <p className="text-[10px] uppercase tracking-[0.18em] text-amber-400 mb-4">
              Simulated for demo capture
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-gray-800 rounded">
                <span className="block text-2xl font-bold">2.4k</span>
                <span className="text-[10px] text-gray-500 uppercase">Viewers</span>
              </div>
              <div className="text-center p-3 bg-gray-800 rounded">
                <span className="block text-2xl font-bold">{liveVoteTotal || 0}</span>
                <span className="text-[10px] text-gray-500 uppercase">Live Votes</span>
              </div>
              <div className="text-center p-3 bg-gray-800 rounded col-span-2">
                <span className="block text-xl font-bold">{activeSessions.length}</span>
                <span className="text-[10px] text-gray-500 uppercase">Active Polls</span>
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
              <span className={`px-2.5 py-1 text-[10px] font-black uppercase rounded border tracking-[0.12em] ${
                wsConnectionStatus === 'connected'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : wsConnectionStatus === 'reconnecting'
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    : wsConnectionStatus === 'error'
                      ? 'bg-red-500/10 text-red-400 border-red-500/30'
                      : 'bg-gray-700/40 text-gray-300 border-gray-600/50'
              }`}>
                WS: {wsConnectionStatus}
              </span>
              <span className={`px-2.5 py-1 text-[10px] font-black uppercase rounded border tracking-[0.12em] ${
                modeLabel === 'director'
                  ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                  : 'bg-slate-500/10 text-slate-300 border-slate-500/30'
              }`}>
                Mode: {modeLabel}
              </span>
              <WalletConnectCustom />
            </div>
          </header>

          <EventTicker />
          {arena3DMode === 'off' ? (
            <Arena3DFallbackPanel reason="manual" />
          ) : arena3DMode === 'auto' ? (
            <Arena3DErrorBoundary fallback={<Arena3DFallbackPanel reason="error" />}>
              <Arena3D />
            </Arena3DErrorBoundary>
          ) : (
            <Arena3D />
          )}
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
                <div className="flex items-center gap-2 pt-2">
                  <span className="px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] rounded border border-cyan-500/30 text-cyan-300 bg-cyan-500/10">
                    {modeLabel === 'director' ? 'Director Mode' : 'Autonomous Mode'}
                  </span>
                  <span className="px-2 py-0.5 text-[10px] uppercase tracking-[0.12em] rounded border border-gray-700 text-gray-400">
                    On-chain writes: Prototype / 501
                  </span>
                </div>
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
