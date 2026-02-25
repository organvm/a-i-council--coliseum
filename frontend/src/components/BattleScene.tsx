'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useColiseumStore } from '@/lib/store';
import type { CombatUpdateEvent } from '@/lib/api';

interface Fighter {
  id: string;
  hp: number;
  maxHp: number;
  isAttacking: boolean;
  isHit: boolean;
}

export const BattleScene: React.FC = () => {
  const latestCombatEvent = useColiseumStore((state) => state.latestCombatEvent);
  const combatLogs = useColiseumStore((state) => state.combatLogs);
  const [fighters, setFighters] = useState<{ [key: string]: Fighter }>({});
  const [isActive, setIsActive] = useState(false);
  const [impactOverlay, setImpactOverlay] = useState<{
    text: string;
    tone: 'hit' | 'fatality';
  } | null>(null);

  useEffect(() => {
    if (latestCombatEvent) {
      handleCombatUpdate(latestCombatEvent);
      setIsActive(true);
      const timer = setTimeout(() => setIsActive(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [latestCombatEvent]);

  const handleCombatUpdate = (data: CombatUpdateEvent) => {
    const aName = data.attacker_name || data.attacker_id;
    const dName = data.defender_name || data.defender_id;
    if (!aName || !dName) {
      return;
    }

    // Add new fighters to tracking if they don't exist
    setFighters((prev) => {
      const next = { ...prev };

      if (!next[aName]) {
        next[aName] = { id: aName, hp: 100, maxHp: 100, isAttacking: false, isHit: false };
      }
      if (!next[dName]) {
        next[dName] = { id: dName, hp: 100, maxHp: 100, isAttacking: false, isHit: false };
      }

      // Process damage and animation flags
      const damage = typeof data.damage === 'number' ? data.damage : 0;
      if (data.is_hit && damage > 0) {
        next[dName].hp = Math.max(0, next[dName].hp - damage);
        next[dName].isHit = true;
      }
      next[aName].isAttacking = true;

      return next;
    });

    // Reset animation flags after 1s
    setTimeout(() => {
      setFighters((prev) => {
        const next = { ...prev };
        if (next[aName]) next[aName].isAttacking = false;
        if (next[dName]) next[dName].isHit = false;
        return next;
      });
    }, 1000);

    if (data.is_fatality) {
      setImpactOverlay({ text: 'FATALITY', tone: 'fatality' });
    } else if (data.is_hit && typeof data.damage === 'number' && data.damage > 0) {
      setImpactOverlay({ text: `-${data.damage} HP`, tone: 'hit' });
    }
    setTimeout(() => setImpactOverlay(null), 900);
  };

  return (
    <div className={`relative w-full h-96 bg-gray-900 rounded-lg overflow-hidden border-2 transition-all duration-500 ${
      isActive ? 'border-red-500 shadow-[0_0_30px_rgba(239,68,68,0.5)] scale-[1.01]' : 'border-red-900/50 shadow-[0_0_30px_rgba(127,29,29,0.3)]'
    }`}>
      {/* Arena Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-red-950/20 to-black opacity-50"></div>
      
      {/* Fighters */}
      <div className="absolute inset-0 flex items-center justify-between px-20">
        {Object.values(fighters).map((fighter, index) => (
          <div key={fighter.id} className="relative group">
            {/* HP Bar */}
            <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-32 h-4 bg-gray-800 rounded-full border border-gray-700 overflow-hidden">
              <motion.div 
                className={`h-full ${fighter.hp < 30 ? 'bg-red-500' : 'bg-green-500'}`}
                initial={{ width: '100%' }}
                animate={{ width: `${(fighter.hp / fighter.maxHp) * 100}%` }}
                transition={{ type: 'spring' }}
              />
            </div>
            
            {/* Avatar */}
            <motion.div
              animate={{ 
                x: fighter.isAttacking ? (index === 0 ? 50 : -50) : 0,
                rotate: fighter.isHit ? (index === 0 ? -10 : 10) : 0,
                scale: fighter.isHit ? 0.9 : (fighter.isAttacking ? 1.1 : 1)
              }}
              className={`w-32 h-32 rounded-lg border-2 flex items-center justify-center text-4xl shadow-2xl relative transition-colors ${
                fighter.isHit ? 'bg-red-900/50 border-red-500' : 'bg-gray-700 border-gray-500'
              }`}
            >
              {index === 0 ? '🛡️' : '⚔️'}
              <div className="absolute -bottom-8 font-black uppercase tracking-widest text-xs bg-black/50 px-2 py-1 rounded text-white whitespace-nowrap">
                {fighter.id}
              </div>
            </motion.div>
          </div>
        ))}
      </div>

      {/* Battle Log Overlay */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black via-black/80 to-transparent">
        <div className="space-y-1 h-24 overflow-y-auto">
          <AnimatePresence initial={false}>
            {combatLogs.slice().reverse().map((log, i) => (
              <motion.p
                key={`${log.timestamp}-${i}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={`text-xs font-mono ${
                  log.is_fatality ? 'text-red-500 font-black animate-pulse' : 'text-gray-300'
                }`}
              >
                <span className="opacity-50">
                  [{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}]
                </span>{' '}
                {log.log}
              </motion.p>
            ))}
          </AnimatePresence>
        </div>
      </div>

      <AnimatePresence>
        {impactOverlay && (
          <motion.div
            key={`${impactOverlay.text}-${impactOverlay.tone}`}
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 1.05 }}
            className={`absolute top-5 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg border font-black uppercase tracking-[0.18em] text-sm shadow-2xl ${
              impactOverlay.tone === 'fatality'
                ? 'bg-red-600/20 border-red-500 text-red-300'
                : 'bg-amber-500/15 border-amber-400/60 text-amber-200'
            }`}
          >
            {impactOverlay.text}
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* VS Badge */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-6xl font-black text-red-600/10 italic select-none">
        VS
      </div>
    </div>
  );
};
