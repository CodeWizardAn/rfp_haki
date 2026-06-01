import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Send, Bot, User, Loader2 } from 'lucide-react';
import { Card } from '@/components/ui';

interface ChatMsg { id: number; role: 'user' | 'agent'; agent?: string; text: string; ts: string; }

const initialMessages: ChatMsg[] = [
  { id: 1, role: 'agent', agent: 'Master', text: 'Hello! I\'m the Master Agent. I can help you run RFP analysis, check bid status, or query product specifications. What would you like to do?', ts: '14:30:00' },
];

const agentResponses: Record<string, { agent: string; text: string }> = {
  'rfp': { agent: 'Sales', text: 'I found 3 active RFPs matching your criteria. RFP-2026-0044 (Power Cables) has the highest priority with a deadline in 5 days. Shall I start the analysis pipeline?' },
  'price': { agent: 'Pricing', text: 'Current pricing for XLPE cables: ₹2,450/100m for 240mm², ₹3,120/100m for 400mm². I can generate a competitive quote with 8% margin. Want me to proceed?' },
  'spec': { agent: 'Technical', text: 'Specification match results: 8 out of 12 requirements fully met (87% score). Gaps found in voltage rating (33kV required vs 22kV available) and temperature range. Shall I suggest alternatives?' },
  'status': { agent: 'Master', text: 'Pipeline status: 2 workflows active. WF-2026-044 is at Stage 5/8 (Pricing). WF-2026-043 completed successfully 2 hours ago with 92% match score.' },
};

export default function AgentChatPage() {
  const [messages, setMessages] = useState<ChatMsg[]>(initialMessages);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: ChatMsg = { id: Date.now(), role: 'user', text: input, ts: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) };
    setMessages((p) => [...p, userMsg]);
    setInput('');
    setTyping(true);

    const key = Object.keys(agentResponses).find((k) => input.toLowerCase().includes(k));
    const resp = (key ? agentResponses[key] : undefined) ?? { agent: 'Master', text: 'I understand your request. Let me coordinate with the relevant agents to get you the best answer. This may take a moment...' };

    setTimeout(() => {
      setTyping(false);
      setMessages((p) => [...p, { id: Date.now() + 1, role: 'agent', agent: resp.agent, text: resp.text, ts: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }]);
    }, 1200);
  };

  const agentColor: Record<string, string> = { Master: 'bg-violet-pulse/20 text-violet-pulse', Sales: 'bg-electric-cyan/20 text-electric-cyan', Technical: 'bg-teal-depth/20 text-teal-depth', Pricing: 'bg-amber-glow/20 text-amber-glow' };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center gap-3 mb-4">
        <Link to="/agents" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Agent Chat Interface</h1><p className="text-body text-muted-silver">Interact with agents via natural language</p></div>
      </div>

      <Card variant="glass" className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((msg) => (
            <motion.div key={msg.id} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] ${msg.role === 'user' ? 'bg-electric-cyan/10 border border-electric-cyan/20' : 'bg-steel-slate/20 border border-steel-slate/20'} rounded-xl p-3`}>
                <div className="flex items-center gap-2 mb-1">
                  {msg.role === 'agent' ? (
                    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded ${agentColor[msg.agent ?? 'Master']}`}><Bot size={10} />{msg.agent}</span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-electric-cyan"><User size={10} />You</span>
                  )}
                  <span className="text-[9px] text-muted-silver">{msg.ts}</span>
                </div>
                <p className="text-sm text-ghost-white leading-relaxed">{msg.text}</p>
              </div>
            </motion.div>
          ))}
          {typing && (
            <div className="flex justify-start">
              <div className="bg-steel-slate/20 border border-steel-slate/20 rounded-xl p-3 flex items-center gap-2">
                <Loader2 size={14} className="text-violet-pulse animate-spin" /><span className="text-xs text-muted-silver">Agent is typing...</span>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="border-t border-steel-slate/20 p-3 flex gap-2">
          <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSend()} placeholder="Ask agents about RFPs, pricing, specs, or status..." className="flex-1 bg-deep-navy/50 border border-steel-slate/20 rounded-lg px-3 py-2 text-sm text-ghost-white placeholder:text-muted-silver/50 focus:outline-none focus:ring-1 focus:ring-electric-cyan/40" />
          <button onClick={handleSend} className="bg-electric-cyan/20 text-electric-cyan p-2 rounded-lg hover:bg-electric-cyan/30 transition-colors"><Send size={16} /></button>
        </div>
      </Card>
    </motion.div>
  );
}
