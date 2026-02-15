'use client';

import React from 'react';
import { useColiseumStore } from '@/lib/store';
import { motion } from 'framer-motion';

export const AgentGrid: React.FC = () => {
  const agents = useColiseumStore((state) => state.agents);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {agents.map((agent) => (
        <motion.div
          key={agent.agent_id}
          whileHover={{ scale: 1.02 }}
          className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-lg relative overflow-hidden"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-900/50 rounded-full flex items-center justify-center border border-primary-500/30 text-2xl">
              {agent.role === 'moderator' ? '⚖️' : agent.role === 'debater' ? '🗣️' : '🧠'}
            </div>
            <div>
              <h4 className="font-bold text-white leading-tight">{agent.name}</h4>
              <span className="text-[10px] uppercase tracking-widest text-primary-400 font-semibold">
                {agent.role}
              </span>
            </div>
          </div>
          
          <div className="mt-3 flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${agent.is_active ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-gray-600'}`}></div>
            <span className="text-[10px] text-gray-400 uppercase tracking-tight">
              {agent.is_active ? 'Standing By' : 'Inactive'}
            </span>
          </div>

          <div className="absolute top-0 right-0 p-2 opacity-10 pointer-events-none">
            <span className="text-4xl font-black italic uppercase">
              {agent.name.charAt(0)}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  );
};
