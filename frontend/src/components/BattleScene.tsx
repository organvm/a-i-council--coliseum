'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface BattleLog {
  message: string;
  timestamp: number;
  type: 'attack' | 'damage' | 'fatality';
}

interface Fighter {
  id: string;
  hp: number;
  maxHp: number;
  isAttacking: boolean;
  isHit: boolean;
}

export const BattleScene: React.FC = () => {
  const [logs, setLogs] = useState<BattleLog[]>([]);
  const [fighters, setFighters] = useState<{ [key: string]: Fighter }>({});

  // Mock WebSocket listener for battle events
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === 'combat_update') {
        handleCombatUpdate(payload.data);
      }
    };

    return () => socket.close();
  }, []);

  const handleCombatUpdate = (data: any) => {
    // Add new fighters to tracking if they don't exist
    setFighters((prev) => {
      const next = { ...prev };
      if (!next[data.attacker_name]) {
        next[data.attacker_name] = { id: data.attacker_name, hp: 100, maxHp: 100, isAttacking: false, isHit: false };
      }
      if (!next[data.defender_name]) {
        next[data.defender_name] = { id: data.defender_name, hp: 100, maxHp: 100, isAttacking: false, isHit: false };
      }

      // Process damage and animation flags
      if (data.is_hit && data.damage > 0) {
        next[data.defender_name].hp = Math.max(0, next[data.defender_name].hp - data.damage);
        next[data.defender_name].isHit = true;
      }
      next[data.attacker_name].isAttacking = true;

      return next;
    });

    // Reset animation flags after 1s
    setTimeout(() => {
      setFighters((prev) => {
        const next = { ...prev };
        if (next[data.attacker_name]) next[data.attacker_name].isAttacking = false;
        if (next[data.defender_name]) next[data.defender_name].isHit = false;
        return next;
      });
    }, 1000);

    const newLog: BattleLog = {
      message: data.log,
      timestamp: Date.now(),
      type: data.is_fatality ? 'fatality' : (data.is_hit ? 'attack' : 'damage') // fallback color
    };
    setLogs(prev => [newLog, ...prev].slice(0, 5));
  };

  return (
    <div className="relative w-full h-96 bg-gray-900 rounded-lg overflow-hidden border-2 border-red-900/50 shadow-[0_0_30px_rgba(127,29,29,0.3)]">
      {/* Arena Background */}
      <div className="absolute inset-0 bg-[url('/arena-bg.png')] bg-cover bg-center opacity-30"></div>
      
      {/* Fighters */}
      <div className="absolute inset-0 flex items-center justify-between px-20">
        {Object.values(fighters).map((fighter, index) => (
          <div key={fighter.id} className="relative group">
            {/* HP Bar */}
            <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-32 h-4 bg-gray-800 rounded-full border border-gray-700 overflow-hidden">
              <motion.div 
                className="h-full bg-green-500"
                initial={{ width: '100%' }}
                animate={{ width: `${(fighter.hp / fighter.maxHp) * 100}%` }}
                transition={{ type: 'spring' }}
              />
            </div>
            
            {/* Avatar */}
            <motion.div
              animate={{ 
                x: fighter.isAttacking ? (index === 0 ? 50 : -50) : 0,
                rotate: fighter.isHit ? (index === 0 ? -10 : 10) : 0
              }}
              className="w-32 h-32 bg-gray-700 rounded-lg border-2 border-gray-500 flex items-center justify-center text-4xl shadow-2xl relative"
            >
              {index === 0 ? '🛡️' : '⚔️'}
              <div className="absolute -bottom-8 font-black uppercase tracking-widest text-sm bg-black/50 px-2 rounded">
                {fighter.id}
              </div>
            </motion.div>
          </div>
        ))}
      </div>

      {/* Battle Log Overlay */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black via-black/80 to-transparent">
        <div className="space-y-1 h-24 overflow-y-auto">
          <AnimatePresence>
            {logs.map((log) => (
              <motion.p
                key={log.timestamp}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className={`text-xs font-mono ${
                  log.type === 'fatality' ? 'text-red-500 font-black animate-pulse' : 'text-gray-300'
                }`}
              >
                <span className="opacity-50">[{new Date(log.timestamp).toLocaleTimeString()}]</span> {log.message}
              </motion.p>
            ))}
          </AnimatePresence>
        </div>
      </div>
      
      {/* VS Badge */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-6xl font-black text-red-600/20 italic select-none">
        VS
      </div>
    </div>
  );
};
