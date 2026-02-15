'use client';

import React, { useState, useEffect } from 'react';
import { votingApi, api } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';

interface Session {
  session_id: string;
  title: string;
  description: string;
  options: string[];
  status: string;
}

export const VotingPanel: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [votingFor, setVotingFor] = useState<string | null>(null);

  const fetchSessions = async () => {
    try {
      const res = await votingApi.listSessions();
      setSessions(res.data.filter((s: Session) => s.status === 'active'));
    } catch (err) {
      console.error('Failed to fetch sessions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleVote = async (sessionId: string, choice: string) => {
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

  if (loading) return <div className="animate-pulse bg-gray-800 h-48 rounded-lg"></div>;

  return (
    <div className="space-y-4">
      <AnimatePresence>
        {sessions.map((session) => (
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

            <div className="grid grid-cols-1 gap-2">
              {session.options.map((option) => (
                <button
                  key={option}
                  disabled={votingFor === session.session_id}
                  onClick={() => handleVote(session.session_id, option)}
                  className="w-full py-3 px-4 bg-gray-800 hover:bg-primary-600/20 hover:border-primary-500/50 text-left text-sm font-medium rounded border border-gray-700 transition-all group flex items-center justify-between disabled:opacity-50"
                >
                  <span className="group-hover:text-white transition-colors">{option}</span>
                  <div className="w-4 h-4 rounded-full border border-gray-600 group-hover:border-primary-500 flex items-center justify-center">
                    <div className="w-2 h-2 bg-primary-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  </div>
                </button>
              ))}
            </div>
            
            {votingFor === session.session_id && (
              <p className="text-[10px] text-primary-500 mt-3 animate-pulse font-bold uppercase tracking-widest text-center">
                Transmitting Vote to Council...
              </p>
            )}
          </motion.div>
        ))}
      </AnimatePresence>

      {sessions.length === 0 && (
        <div className="bg-gray-900/50 border border-dashed border-gray-800 p-8 rounded-lg text-center">
          <p className="text-gray-500 text-sm italic">No active polls at this time.</p>
        </div>
      )}
    </div>
  );
};
