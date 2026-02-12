import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Bot, Clock, ChevronDown, ChevronRight, ArrowRight } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

const messages = [
  { id: 1, from: 'Master', to: 'Sales', type: 'request', payload: 'Scan RFP-2026-0044 URLs', ts: '14:32:01', latency: '—', status: 'delivered' as const },
  { id: 2, from: 'Sales', to: 'Master', type: 'response', payload: 'Found 3 matching RFPs, selected RFP #2', ts: '14:32:09', latency: '8.2s', status: 'delivered' as const },
  { id: 3, from: 'Master', to: 'Technical', type: 'request', payload: 'Analyze specs for 12 requirements', ts: '14:32:10', latency: '—', status: 'delivered' as const },
  { id: 4, from: 'Master', to: 'Pricing', type: 'request', payload: 'Prepare pricing for matched products', ts: '14:32:10', latency: '—', status: 'delivered' as const },
  { id: 5, from: 'Technical', to: 'Master', type: 'response', payload: 'Matched 8/12 requirements, avg score 87%', ts: '14:32:52', latency: '42.1s', status: 'delivered' as const },
  { id: 6, from: 'Technical', to: 'Pricing', type: 'data', payload: 'Product list with specs for pricing', ts: '14:32:53', latency: '—', status: 'delivered' as const },
  { id: 7, from: 'Pricing', to: 'Master', type: 'response', payload: 'Pricing complete: ₹23,45,000 total', ts: '14:33:01', latency: '51.0s', status: 'delivered' as const },
  { id: 8, from: 'Master', to: 'Master', type: 'consolidate', payload: 'Consolidating all agent results', ts: '14:33:02', latency: '—', status: 'delivered' as const },
];

const agentColor: Record<string, string> = { Master: 'text-violet-pulse', Sales: 'text-electric-cyan', Technical: 'text-teal-depth', Pricing: 'text-amber-glow' };
const typeColor: Record<string, string> = { request: 'cyan', response: 'emerald', data: 'amber', consolidate: 'violet' };

export default function AgentIntercomPage() {
  const [expanded, setExpanded] = useState<number[]>([]);
  const toggle = (id: number) => setExpanded((p) => p.includes(id) ? p.filter((i) => i !== id) : [...p, id]);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/agents" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Agent Inter-Communication Log</h1><p className="text-body text-muted-silver">Message queue between agents — Workflow WF-2026-044</p></div>
      </div>

      <div className="grid grid-cols-4 gap-2">
        {['Master', 'Sales', 'Technical', 'Pricing'].map((a) => {
          const count = messages.filter((m) => m.from === a).length;
          return (
            <Card key={a} variant="glass" className="p-3 text-center">
              <Bot size={16} className={`${agentColor[a]} mx-auto mb-1`} />
              <span className="text-xs font-semibold text-ghost-white">{a}</span>
              <span className="text-[10px] text-muted-silver block">{count} messages</span>
            </Card>
          );
        })}
      </div>

      <div className="space-y-1.5">
        {messages.map((msg) => {
          const isExpanded = expanded.includes(msg.id);
          return (
            <Card key={msg.id} variant="glass" className="overflow-hidden">
              <button onClick={() => toggle(msg.id)} className="w-full flex items-center gap-3 p-3 hover:bg-steel-slate/5 transition-colors text-left">
                <span className="text-[10px] text-muted-silver font-mono w-16 flex-shrink-0">{msg.ts}</span>
                <span className={`text-xs font-semibold w-20 ${agentColor[msg.from]}`}>{msg.from}</span>
                <ArrowRight size={12} className="text-muted-silver/40" />
                <span className={`text-xs font-semibold w-20 ${agentColor[msg.to]}`}>{msg.to}</span>
                <Badge variant="soft" color={typeColor[msg.type] as 'cyan' | 'emerald' | 'amber' | 'violet'} size="sm">{msg.type}</Badge>
                <span className="text-xs text-ghost-white flex-1 truncate">{msg.payload}</span>
                {msg.latency !== '—' && <span className="text-[10px] text-muted-silver font-mono"><Clock size={9} className="inline mr-0.5" />{msg.latency}</span>}
                {isExpanded ? <ChevronDown size={12} className="text-muted-silver" /> : <ChevronRight size={12} className="text-muted-silver" />}
              </button>
              {isExpanded && (
                <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} className="px-3 pb-3 overflow-hidden">
                  <pre className="text-[10px] text-muted-silver bg-deep-navy/50 rounded-lg p-2 font-mono overflow-x-auto">{JSON.stringify({ from: msg.from, to: msg.to, type: msg.type, payload: msg.payload, timestamp: `2026-02-06T${msg.ts}.000Z`, latency: msg.latency, status: msg.status }, null, 2)}</pre>
                </motion.div>
              )}
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
