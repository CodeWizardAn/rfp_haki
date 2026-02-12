import { motion } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Globe, Clock, CheckCircle2, TrendingUp, Cpu, DollarSign, Users, Layers } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

/* ─── agent data ─── */
const agents: Record<string, { name: string; color: string; icon: React.ReactNode; description: string; stats: { label: string; value: string }[]; capabilities: string[]; recentActions: { action: string; time: string; status: 'success' | 'warning' }[] }> = {
  sales: {
    name: 'Sales Agent', color: 'text-electric-cyan', icon: <Globe size={20} className="text-electric-cyan" />, description: 'Scans URLs, discovers RFPs, selects relevant opportunities, and prepares RFP summaries for the pipeline.',
    stats: [{ label: 'URLs Monitored', value: '24' }, { label: 'RFPs Discovered', value: '187' }, { label: 'Success Rate', value: '94.2%' }, { label: 'Avg Scan Time', value: '8.3s' }],
    capabilities: ['URL scanning & web scraping', 'RFP document discovery', 'RFP relevance filtering', 'Summary generation', 'Auto-categorization'],
    recentActions: [{ action: 'Scanned gem.gov.in — found 3 new RFPs', time: '2m ago', status: 'success' }, { action: 'Analyzed RFP-2026-0045 relevance → 92% match', time: '8m ago', status: 'success' }, { action: 'URL timeout on cppp.nic.in — retrying', time: '15m ago', status: 'warning' }, { action: 'Processed RFP batch #12 — 5 RFPs categorized', time: '32m ago', status: 'success' }],
  },
  technical: {
    name: 'Technical Agent', color: 'text-teal-depth', icon: <Cpu size={20} className="text-teal-depth" />, description: 'Analyzes product specifications, matches OEM databases (15 products, 8 datasheets), and performs compliance verification.',
    stats: [{ label: 'Products Analyzed', value: '2,456' }, { label: 'Avg Match Score', value: '87.3%' }, { label: 'Datasheets Loaded', value: '8' }, { label: 'OEM Databases', value: '5' }],
    capabilities: ['Spec-to-spec matching', 'BIS/IEC compliance check', 'Engineering calculations', 'Cable sizing & voltage drop', 'Datasheet extraction'],
    recentActions: [{ action: 'Matched 12 products for RFP-2026-0044', time: '5m ago', status: 'success' }, { action: 'Compliance check — IS 7098 passed', time: '12m ago', status: 'success' }, { action: 'Low confidence match for 3C×400 — manual review', time: '20m ago', status: 'warning' }, { action: 'Updated Finolex product database', time: '1h ago', status: 'success' }],
  },
  pricing: {
    name: 'Pricing Agent', color: 'text-amber-glow', icon: <DollarSign size={20} className="text-amber-glow" />, description: 'Calculates pricing with Indian market rates, GST, testing costs, volume discounts, and generates competitive bid amounts.',
    stats: [{ label: 'Quotes Generated', value: '834' }, { label: 'Avg Turnaround', value: '4.2s' }, { label: 'Pricing Accuracy', value: '96.1%' }, { label: 'Products Priced', value: '15' }],
    capabilities: ['Unit price calculation', 'GST computation (18%)', 'Testing cost estimation', 'Volume discount tiers', 'Historical price comparison'],
    recentActions: [{ action: 'Priced 8-item bid for RFP-2026-0044 — ₹23.4L', time: '5m ago', status: 'success' }, { action: 'Volume discount applied — 5% tier', time: '12m ago', status: 'success' }, { action: 'Price variance alert — Polycab +8% vs last quarter', time: '25m ago', status: 'warning' }, { action: 'Updated service pricing tables', time: '2h ago', status: 'success' }],
  },
  master: {
    name: 'Master Agent', color: 'text-violet-pulse', icon: <Users size={20} className="text-violet-pulse" />, description: 'Orchestrates all agents, consolidates results from Sales/Technical/Pricing, generates scope-of-supply tables, and manages conversations.',
    stats: [{ label: 'Workflows Run', value: '412' }, { label: 'Avg Consolidation', value: '6.8s' }, { label: 'Conversations', value: '1,247' }, { label: 'Success Rate', value: '98.4%' }],
    capabilities: ['Multi-agent orchestration', 'Result consolidation', 'Scope of supply generation', 'Conversation management', 'Fallback handling'],
    recentActions: [{ action: 'Consolidated 3-agent workflow for RFP-2026-0044', time: '4m ago', status: 'success' }, { action: 'Generated scope of supply — 12 line items', time: '4m ago', status: 'success' }, { action: 'Fallback: used cached pricing (agent timeout)', time: '18m ago', status: 'warning' }, { action: 'Managed conversation CONV_20260206_1234', time: '30m ago', status: 'success' }],
  },
};

export default function AgentDetailPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const agent = (agents[agentId ?? 'sales'] ?? agents['sales'])!;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/agents" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div className="p-2.5 rounded-xl bg-steel-slate/15">{agent.icon}</div>
        <div><h1 className="text-h1 text-ghost-white">{agent.name}</h1><p className="text-body text-muted-silver">{agent.description}</p></div>
        <Badge variant="pulse" color="emerald" size="sm" className="ml-auto">Online</Badge>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {agent.stats.map((s) => (
          <Card key={s.label} variant="glass" className="p-3 text-center">
            <span className="text-lg font-bold text-ghost-white font-mono">{s.value}</span>
            <span className="text-[10px] text-muted-silver block">{s.label}</span>
          </Card>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Capabilities */}
        <Card variant="glass" className="p-4">
          <h3 className="text-sm font-semibold text-ghost-white mb-3 flex items-center gap-2"><Layers size={14} className="text-electric-cyan" />Capabilities</h3>
          <div className="space-y-1.5">
            {agent.capabilities.map((c) => (
              <div key={c} className="flex items-center gap-2 text-xs text-muted-silver"><CheckCircle2 size={11} className="text-neon-emerald flex-shrink-0" />{c}</div>
            ))}
          </div>
        </Card>

        {/* Recent Actions */}
        <Card variant="glass" className="p-4">
          <h3 className="text-sm font-semibold text-ghost-white mb-3 flex items-center gap-2"><Clock size={14} className="text-amber-glow" />Recent Activity</h3>
          <div className="space-y-2">
            {agent.recentActions.map((a, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: 6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-start gap-2 p-2 rounded-lg bg-steel-slate/5">
                {a.status === 'success' ? <CheckCircle2 size={12} className="text-neon-emerald mt-0.5 flex-shrink-0" /> : <TrendingUp size={12} className="text-amber-glow mt-0.5 flex-shrink-0" />}
                <div className="flex-1 min-w-0"><p className="text-xs text-ghost-white">{a.action}</p><span className="text-[10px] text-muted-silver">{a.time}</span></div>
              </motion.div>
            ))}
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
