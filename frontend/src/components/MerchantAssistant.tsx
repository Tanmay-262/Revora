'use client';

import React, { useState } from 'react';
import { Bot, Send, X, User } from 'lucide-react';
import { sendChatMessage } from '@/lib/api';

interface MerchantAssistantProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MerchantAssistant: React.FC<MerchantAssistantProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'bot'; text: string }>>([
    {
      sender: 'bot',
      text: 'Hello! I am Revora, your AI Revenue Recovery Assistant. Ask me about revenue at risk, root causes, recovery uplift, or high-value items requiring review.'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();
    setMessages((prev) => [...prev, { sender: 'user', text: userQuery }]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await sendChatMessage(userQuery);
      setMessages((prev) => [...prev, { sender: 'bot', text: res.reply || 'Summary generated.' }]);
    } catch {
      setMessages((prev) => [...prev, { sender: 'bot', text: 'Sorry, I could not retrieve metrics at this moment.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/75 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 text-slate-100 h-full flex flex-col justify-between p-5 shadow-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3.5 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-sky-500/10 text-sky-400 flex items-center justify-center border border-sky-500/20">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-100">Merchant Assistant</h3>
              <p className="text-[10px] text-slate-400">Grounded in backend facts & policy rules</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Chat Stream */}
        <div className="flex-1 overflow-y-auto my-3 space-y-2.5 pr-1 text-xs">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex gap-2 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.sender === 'bot' && (
                <div className="w-5 h-5 rounded-full bg-sky-500/10 text-sky-400 flex items-center justify-center shrink-0 border border-sky-500/20">
                  <Bot className="w-3 h-3" />
                </div>
              )}

              <div
                className={`p-2.5 rounded-xl max-w-[85%] leading-relaxed ${
                  m.sender === 'user'
                    ? 'bg-sky-600 text-white rounded-br-none shadow-xs'
                    : 'bg-slate-950 text-slate-200 border border-slate-800 rounded-bl-none'
                }`}
              >
                {m.text}
              </div>

              {m.sender === 'user' && (
                <div className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center shrink-0 border border-slate-700">
                  <User className="w-3 h-3" />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 italic">
              <Bot className="w-3 h-3 animate-spin text-sky-400" /> Analyzing metrics...
            </div>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSend} className="pt-3 border-t border-slate-800 flex items-center gap-2">
          <input
            type="text"
            placeholder="Ask about revenue at risk, root causes..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>

      </div>
    </div>
  );
};
