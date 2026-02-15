'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';

interface Event {
  event_id: string;
  title: string;
  category: string;
  timestamp: string;
}

export const EventTicker: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    const fetchEvents = () => {
      api.get('/api/events?limit=10').then((res) => setEvents(res.data));
    };
    fetchEvents();
    const interval = setInterval(fetchEvents, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-primary-900/20 border-y border-primary-900/30 py-2 overflow-hidden whitespace-nowrap">
      <div className="flex animate-marquee items-center">
        {events.map((event) => (
          <div key={event.event_id} className="flex items-center mx-8">
            <span className="text-[10px] font-black uppercase text-primary-500 mr-2">
              [{event.category || 'EVENT'}]
            </span>
            <span className="text-xs font-bold text-gray-300">
              {event.title}
            </span>
            <span className="mx-4 text-gray-700">•</span>
          </div>
        ))}
        {/* Repeat for seamless loop */}
        {events.map((event) => (
          <div key={`${event.event_id}-loop`} className="flex items-center mx-8">
            <span className="text-[10px] font-black uppercase text-primary-500 mr-2">
              [{event.category || 'EVENT'}]
            </span>
            <span className="text-xs font-bold text-gray-300">
              {event.title}
            </span>
            <span className="mx-4 text-gray-700">•</span>
          </div>
        ))}
      </div>
    </div>
  );
};
