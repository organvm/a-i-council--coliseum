'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';

interface Entry {
  rank: number;
  user_id: string;
  value: number;
  tier: string;
}

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [type, setType] = useState('points');

  useEffect(() => {
    api.get(`/api/users/leaderboard/${type}`).then((res) => setEntries(res.data));
  }, [type]);

  return (
    <div className="min-h-screen bg-gray-950 p-8 text-gray-100">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-black italic uppercase tracking-tighter">
            Arena <span className="text-primary-500">Leaderboard</span>
          </h1>
          <div className="flex gap-4 mt-6">
            {['points', 'votes'].map((t) => (
              <button
                key={t}
                onClick={() => setType(t)}
                className={`px-6 py-2 text-xs font-black uppercase tracking-widest rounded-full border transition-all ${
                  type === t 
                    ? 'bg-primary-600 border-primary-500 text-white' 
                    : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-600'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </header>

        <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-800/50 text-[10px] uppercase tracking-[0.2em] font-black text-gray-500">
                <th className="px-6 py-4">Rank</th>
                <th className="px-6 py-4">Participant</th>
                <th className="px-6 py-4">Tier</th>
                <th className="px-6 py-4 text-right">{type}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {entries.map((entry, i) => (
                <motion.tr 
                  key={entry.user_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="hover:bg-gray-800/30 transition-colors group"
                >
                  <td className="px-6 py-4">
                    <span className={`text-lg font-black italic ${i < 3 ? 'text-primary-500' : 'text-gray-600'}`}>
                      #{entry.rank}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-bold text-gray-300">
                    User_{entry.user_id.slice(0, 6)}
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gray-800 border border-gray-700 text-gray-400">
                      {entry.tier}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right font-mono font-bold text-primary-400">
                    {entry.value.toLocaleString()}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
