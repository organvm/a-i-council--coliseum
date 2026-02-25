'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { votingApi, type VoteChoice, type VotingSessionSummary } from '@/lib/api';
import { useColiseumStore } from '@/lib/store';
import { motion, AnimatePresence } from 'framer-motion';

export const VotingPanel: React.FC = () => {
  const [sessions, setSessions] = useState<VotingSessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [votingFor, setVotingFor] = useState<string | null>(null);
  const voteUpdatesBySession = useColiseumStore((state) => state.voteUpdatesBySession);
  const setStoreSessions = useColiseumStore((state) => state.setSessions);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await votingApi.listSessions();
      const active = res.data.filter((s) => s.status === 'active');
      setSessions(active);
      setStoreSessions(active);
    } catch (err) {
      console.error('Failed to fetch sessions', err);
    } finally {
      setLoading(false);
    }
  }, [setStoreSessions]);

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 10000);
    return () => clearInterval(interval);
  }, [fetchSessions]);

  const handleVote = async (sessionId: string, choice: VoteChoice) => {
    setVotingFor(sessionId);
    try {
      await votingApi.castVote(sessionId, choice);
      // Refresh after vote
      fetchSessions();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Voting failed. Are you logged in?');
    } finally {
      setVotingFor(null);
    }
  };

  const getOptionLabel = (option: VoteChoice) =>
    typeof option === 'string' ? option : JSON.stringify(option);

  const renderSessionCard = (session: VotingSessionSummary) => {
    const liveUpdate = voteUpdatesBySession[session.session_id];
    const liveChoiceWeights = liveUpdate?.choice_weights || {};
    const liveTotalVotes = liveUpdate?.total_votes ?? session.total_votes;
    const liveTotalWeight = Object.values(liveChoiceWeights).reduce(
      (sum, value) => sum + (typeof value === 'number' ? value : 0),
      0
    );

    return (
      <motion.div
        key={session.session_id}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        className="bg-gray-900 border border-gray-800 p-6 rounded-lg shadow-xl"
      >
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h3 className="text-lg font-bold text-white italic">{session.title}</h3>
            <p className="text-xs text-gray-400 mt-1">{session.description}</p>
          </div>
          <span className="px-2 py-0.5 bg-primary-500/20 text-primary-400 text-[10px] font-black uppercase rounded border border-primary-500/30">
            Active Poll
          </span>
        </div>

        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest rounded border border-gray-700 text-gray-300">
            {liveTotalVotes} vote{liveTotalVotes === 1 ? '' : 's'}
          </span>
          {liveUpdate?.simulated && (
            <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest rounded border border-amber-500/30 text-amber-300 bg-amber-500/10">
              Simulated Audience
            </span>
          )}
          {liveUpdate?.results && (
            <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest rounded border border-emerald-500/30 text-emerald-300 bg-emerald-500/10">
              Finalized
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 gap-2">
          {session.options.map((option) => {
            const optionLabel = getOptionLabel(option);
            const weight = liveChoiceWeights[optionLabel] || 0;
            const pct = liveTotalWeight > 0 ? (weight / liveTotalWeight) * 100 : 0;
            const barWidthPct = liveUpdate ? Math.max(2, pct) : 0;
            return (
              <div key={`${session.session_id}-${optionLabel}`} className="space-y-1">
                <button
                  disabled={votingFor === session.session_id}
                  onClick={() => handleVote(session.session_id, option)}
                  className="w-full py-3 px-4 bg-gray-800 hover:bg-primary-600/20 hover:border-primary-500/50 text-left text-sm font-medium rounded border border-gray-700 transition-all group flex items-center justify-between disabled:opacity-50"
                >
                  <span className="group-hover:text-white transition-colors">{optionLabel}</span>
                  <div className="flex items-center gap-3">
                    {liveUpdate && (
                      <span className="text-[10px] font-mono text-gray-400">{pct.toFixed(0)}%</span>
                    )}
                    <div className="w-4 h-4 rounded-full border border-gray-600 group-hover:border-primary-500 flex items-center justify-center">
                      <div className="w-2 h-2 bg-primary-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    </div>
                  </div>
                </button>
                {liveUpdate && (
                  <div className="h-1.5 rounded-full bg-gray-800 overflow-hidden border border-gray-700">
                    <motion.div
                      className="h-full bg-primary-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${barWidthPct}%` }}
                      transition={{ duration: 0.25 }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {votingFor === session.session_id && (
          <p className="text-[10px] text-primary-500 mt-3 animate-pulse font-bold uppercase tracking-widest text-center">
            Transmitting Vote to Council...
          </p>
        )}

        {liveUpdate?.results && typeof liveUpdate.results === 'object' && (
          <div className="mt-4 rounded border border-gray-700 bg-gray-800/50 p-3">
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-gray-400 mb-2">
              Result Snapshot
            </p>
            <pre className="text-[10px] text-gray-300 whitespace-pre-wrap break-words">
              {JSON.stringify(liveUpdate.results, null, 2)}
            </pre>
          </div>
        )}
      </motion.div>
    );
  };

  if (loading) return <div className="animate-pulse bg-gray-800 h-48 rounded-lg"></div>;

  return (
    <div className="space-y-4">
      <AnimatePresence>
        {sessions.map(renderSessionCard)}
      </AnimatePresence>

      {sessions.length === 0 && (
        <div className="bg-gray-900/50 border border-dashed border-gray-800 p-8 rounded-lg text-center">
          <p className="text-gray-500 text-sm italic">No active polls at this time.</p>
        </div>
      )}
    </div>
  );
};
