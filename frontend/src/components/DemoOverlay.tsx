'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useColiseumStore } from '@/lib/store';
import type { DemoMarkerEvent } from '@/lib/api';

const severityClasses: Record<string, string> = {
  info: 'border-cyan-400/50 bg-cyan-500/10 text-cyan-100',
  warning: 'border-amber-400/50 bg-amber-500/10 text-amber-100',
  success: 'border-emerald-400/50 bg-emerald-500/10 text-emerald-100',
  error: 'border-red-400/50 bg-red-500/10 text-red-100',
};

export const DemoOverlay: React.FC = () => {
  const latestDemoMarker = useColiseumStore((state) => state.latestDemoMarker);
  const [visibleMarker, setVisibleMarker] = useState<DemoMarkerEvent | null>(null);

  useEffect(() => {
    if (!latestDemoMarker) return;
    setVisibleMarker(latestDemoMarker);
    const timer = window.setTimeout(() => setVisibleMarker(null), 3200);
    return () => window.clearTimeout(timer);
  }, [latestDemoMarker]);

  const classes = useMemo(() => {
    const severity = visibleMarker?.severity || 'info';
    return severityClasses[severity] || severityClasses.info;
  }, [visibleMarker]);

  return (
    <div className="pointer-events-none fixed inset-x-0 top-6 z-50 flex justify-center px-4">
      <AnimatePresence>
        {visibleMarker && (
          <motion.div
            key={`${visibleMarker.marker}-${visibleMarker.timestamp || ''}`}
            initial={{ opacity: 0, y: -20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -12, scale: 0.98 }}
            transition={{ duration: 0.24 }}
            className={`w-full max-w-2xl rounded-xl border px-5 py-4 shadow-2xl backdrop-blur ${classes}`}
          >
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.18em] opacity-90">
                  Director Marker
                </p>
                <h2 className="mt-1 text-xl font-black tracking-tight uppercase italic">
                  {visibleMarker.title}
                </h2>
                {visibleMarker.subtitle && (
                  <p className="mt-1 text-sm opacity-90">{visibleMarker.subtitle}</p>
                )}
              </div>
              <div className="text-right text-[10px] font-mono opacity-80">
                <div>{(visibleMarker.severity || 'info').toUpperCase()}</div>
                {visibleMarker.scenario && <div>{visibleMarker.scenario}</div>}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
