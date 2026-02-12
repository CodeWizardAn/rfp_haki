import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, RefreshCw, CheckCircle2, XCircle, Clock, ChevronRight, ChevronDown } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface AgentError { id: number; agent: string; type: string; message: string; timestamp: string; recoverable: boolean; retries: number; status: 'resolved' | 'pending' | 'failed'; resolution?: string; }

const errors: AgentError[] = [
  { id: 1, agent: 'Sales', type: 'NetworkTimeout', message: 'URL scan timed out after 30s for https://rfp-portal.example.com/tender/2026-44', timestamp: '14:32:15', recoverable: true, retries: 2, status: 'resolved', resolution: 'Auto-retry succeeded on attempt 2' },
  { id: 2, agent: 'Technical', type: 'MatchingError', message: 'Spec comparison failed: unknown cable standard "IEC-62955"', timestamp: '14:33:02', recoverable: false, retries: 0, status: 'pending' },
  { id: 3, agent: 'Pricing', type: 'DataMissing', message: 'No pricing data for product SKU: HAK-XLPE-400', timestamp: '14:33:45', recoverable: true, retries: 1, status: 'resolved', resolution: 'Fallback to average category pricing' },
  { id: 4, agent: 'Master', type: 'OrchestrateStall', message: 'Technical agent unresponsive for 60s during spec matching stage', timestamp: '14:34:10', recoverable: true, retries: 1, status: 'resolved', resolution: 'Agent restarted, resumed from checkpoint' },
  { id: 5, agent: 'Sales', type: 'ParseError', message: 'Failed to parse PDF attachment: corrupt header in rfp_supplement.pdf', timestamp: '14:35:22', recoverable: false, retries: 3, status: 'failed', resolution: 'Manual intervention required' },
];

const statusCfg: Record<string, { icon: typeof CheckCircle2; color: string; badge: 'emerald' | 'amber' | 'coral' }> = {
  resolved: { icon: CheckCircle2, color: 'text-neon-emerald', badge: 'emerald' },
  pending: { icon: Clock, color: 'text-amber-glow', badge: 'amber' },
  failed: { icon: XCircle, color: 'text-coral-flame', badge: 'coral' },
};

export default function AgentErrorHandlingPage() {
  const [expanded, setExpanded] = useState<number[]>([]);
  const toggle = (id: number) => setExpanded((p) => p.includes(id) ? p.filter((i) => i !== id) : [...p, id]);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/agents" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Agent Error Handling</h1><p className="text-body text-muted-silver">Error tracking, recovery, and retry management</p></div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[{ l: 'Resolved', c: 'neon-emerald', v: errors.filter((e) => e.status === 'resolved').length }, { l: 'Pending', c: 'amber-glow', v: errors.filter((e) => e.status === 'pending').length }, { l: 'Failed', c: 'coral-flame', v: errors.filter((e) => e.status === 'failed').length }].map((s) => (
          <Card key={s.l} variant="glass" className="p-4 text-center">
            <span className={`text-2xl font-bold text-${s.c}`}>{s.v}</span>
            <span className="text-xs text-muted-silver block mt-1">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="space-y-2">
        {errors.map((err) => {
          const isOpen = expanded.includes(err.id);
          const cfg = (statusCfg[err.status] ?? statusCfg['pending'])!;
          const Icon = cfg.icon;
          return (
            <Card key={err.id} variant="glass" className="overflow-hidden">
              <button onClick={() => toggle(err.id)} className="w-full flex items-center gap-3 p-4 text-left hover:bg-steel-slate/5 transition-colors">
                <AlertTriangle size={14} className="text-coral-flame flex-shrink-0" />
                <span className="text-[10px] text-muted-silver font-mono w-16">{err.timestamp}</span>
                <span className="text-xs font-semibold text-ghost-white w-16">{err.agent}</span>
                <Badge variant="soft" color="amber" size="sm">{err.type}</Badge>
                <span className="text-xs text-muted-silver flex-1 truncate">{err.message}</span>
                <Icon size={14} className={cfg.color} />
                <Badge variant="soft" color={cfg.badge} size="sm">{err.status}</Badge>
                {isOpen ? <ChevronDown size={12} className="text-muted-silver" /> : <ChevronRight size={12} className="text-muted-silver" />}
              </button>
              {isOpen && (
                <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} className="px-4 pb-4 space-y-2 overflow-hidden">
                  <div className="grid grid-cols-3 gap-3 text-xs">
                    <div><span className="text-muted-silver block">Recoverable</span><span className="text-ghost-white">{err.recoverable ? 'Yes' : 'No'}</span></div>
                    <div><span className="text-muted-silver block">Retries</span><span className="text-ghost-white">{err.retries}</span></div>
                    <div><span className="text-muted-silver block">Status</span><span className={cfg.color}>{err.status}</span></div>
                  </div>
                  {err.resolution && <div className="text-xs bg-deep-navy/40 rounded-lg p-2"><span className="text-muted-silver">Resolution: </span><span className="text-ghost-white">{err.resolution}</span></div>}
                  {err.status === 'pending' && (
                    <button className="flex items-center gap-1 text-xs text-electric-cyan hover:text-electric-cyan/80"><RefreshCw size={12} />Retry Now</button>
                  )}
                </motion.div>
              )}
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
