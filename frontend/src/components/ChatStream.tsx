'use client';

import React, { useEffect, useRef } from 'react';
import { useColiseumStore } from '@/lib/store';
import { motion, AnimatePresence } from 'framer-motion';

export const ChatStream: React.FC = () => {
  const messages = useColiseumStore((state) => state.messages);
  const agents = useColiseumStore((state) => state.agents);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getAgentName = (id: string) => {
    return agents.find((a) => a.agent_id === id)?.name || id;
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 rounded-lg overflow-hidden border border-gray-800">
      <div className="p-4 bg-gray-800 border-b border-gray-700">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          Live Debate Stream
        </h3>
      </div>
      
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
      >
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.message_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex flex-col"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold text-primary-400 uppercase tracking-wider">
                  {getAgentName(msg.sender_id)}
                </span>
                <span className="text-[10px] text-gray-500">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="bg-gray-800 text-gray-200 p-3 rounded-lg rounded-tl-none border-l-2 border-primary-500 text-sm leading-relaxed shadow-sm">
                {msg.content}
                
                {/* Agent Thought Stream */}
                {msg.metadata && (msg.metadata.sentiment_context || msg.metadata.topics) && (
                  <div className="mt-3 pt-3 border-t border-gray-700/50 flex flex-wrap gap-2 text-[10px] tracking-wide font-medium">
                    {msg.metadata.sentiment_context && msg.metadata.sentiment_context.sentiment && (
                      <span className={`px-2 py-0.5 rounded-sm border ${
                        msg.metadata.sentiment_context.sentiment === "positive" ? "bg-green-500/10 text-green-400 border-green-500/20" :
                        msg.metadata.sentiment_context.sentiment === "negative" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                        "bg-gray-700/50 text-gray-400 border-gray-600/50"
                      }`}>
                        {msg.metadata.sentiment_context.sentiment.toUpperCase()} ({(msg.metadata.sentiment_context.score * 100).toFixed(0)}%)
                      </span>
                    )}
                    {msg.metadata.topics && Object.entries(msg.metadata.topics)
                        .sort((a: any, b: any) => b[1] - a[1])
                        .slice(0, 2)
                        .map(([topic, score]: any) => (
                      <span key={topic} className="px-2 py-0.5 rounded-sm bg-primary-500/10 text-primary-400 border border-primary-500/20 uppercase">
                        {topic} ({(score * 100).toFixed(0)}%)
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-500 italic text-sm">
            Waiting for the council to convene...
          </div>
        )}
      </div>
    </div>
  );
};
