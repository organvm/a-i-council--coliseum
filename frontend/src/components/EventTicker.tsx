'use client';

import React, { useEffect } from 'react';
import { eventsApi } from '@/lib/api';
import { useColiseumStore } from '@/lib/store';

export const EventTicker: React.FC = () => {
  const events = useColiseumStore((state) => state.events);
  const setStoreEvents = useColiseumStore((state) => state.setEvents);

  useEffect(() => {
    const fetchEvents = () => {
      eventsApi.list(10).then((res) => setStoreEvents(res.data));
    };
    fetchEvents();
    const interval = setInterval(fetchEvents, 30000);
    return () => clearInterval(interval);
  }, [setStoreEvents]);

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
