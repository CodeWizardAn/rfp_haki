import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, FlaskConical, TrendingUp, BarChart3, CheckCircle2, XCircle, Play, Pause } from 'lucide-react';
import { Card, Badge } from '@/components/ui';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';

/* ─── mock experiments ─── */
interface Experiment { id: string; name: string; metric: string; status: 'running' | 'completed' | 'paused'; variantA: { name: string; value: number; sample: number }; variantB: { name: string; value: number; sample: number }; confidence: number; winner?: 'A' | 'B'; startedAt: string; }
const initialExperiments: Experiment[] = [
  { id: 'exp-001', name: 'Bid Scoring Algorithm v2', metric: 'Win Rate', status: 'completed', variantA: { name: 'Current (v1)', value: 42, sample: 312 }, variantB: { name: 'New (v2)', value: 51, sample: 308 }, confidence: 96.4, winner: 'B', startedAt: '2026-01-05' },
  { id: 'exp-002', name: 'Simplified RFP Upload Flow', metric: 'Completion Rate', status: 'running', variantA: { name: 'Multi-Step', value: 68, sample: 185 }, variantB: { name: 'Single-Page', value: 74, sample: 192 }, confidence: 82.1, startedAt: '2026-01-22' },
  { id: 'exp-003', name: 'Agent Response Timeout (5s vs 10s)', metric: 'Success Rate', status: 'running', variantA: { name: '5s Timeout', value: 88, sample: 540 }, variantB: { name: '10s Timeout', value: 93, sample: 527 }, confidence: 91.3, startedAt: '2026-01-28' },
  { id: 'exp-004', name: 'Vendor Ranking Weight Adjustment', metric: 'Match Accuracy', status: 'paused', variantA: { name: 'Equal Weights', value: 71, sample: 102 }, variantB: { name: 'Weighted by History', value: 73, sample: 98 }, confidence: 44.2, startedAt: '2026-02-01' },
];

const statusCfg: Record<string, { color: string; badge: 'emerald' | 'cyan' | 'amber' }> = {
  running: { color: 'text-neon-emerald', badge: 'emerald' },
  completed: { color: 'text-electric-cyan', badge: 'cyan' },
  paused: { color: 'text-amber-glow', badge: 'amber' },
};

export default function ABTestingDashboardPage() {
  const [items, setItems] = useState<Experiment[]>(initialExperiments);
  const [filter, setFilter] = useState<'all' | 'running' | 'completed' | 'paused'>('all');
  const filtered = filter === 'all' ? items : items.filter((e) => e.status === filter);

  const toggleStatus = (id: string) => {
    setItems((prev) =>
      prev.map((e) => {
        if (e.id === id) {
          const nextStatus = e.status === 'running' ? 'paused' : 'running';
          toast.success(`Experiment "${e.name}" is now ${nextStatus}`);
          return { ...e, status: nextStatus };
        }
        return e;
      })
    );
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/analytics" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div className="p-2.5 rounded-xl bg-violet-pulse/10"><FlaskConical size={20} className="text-violet-pulse" /></div>
        <div><h1 className="text-h1 text-ghost-white">A/B Testing Dashboard</h1><p className="text-body text-muted-silver">Monitor experiments and measure impact</p></div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Active Experiments', value: items.filter((e) => e.status === 'running').length, icon: <Play size={14} className="text-neon-emerald" /> },
          { label: 'Completed', value: items.filter((e) => e.status === 'completed').length, icon: <CheckCircle2 size={14} className="text-electric-cyan" /> },
          { label: 'Avg Confidence', value: `${(items.reduce((s, e) => s + e.confidence, 0) / items.length).toFixed(1)}%`, icon: <TrendingUp size={14} className="text-amber-glow" /> },
          { label: 'Total Samples', value: items.reduce((s, e) => s + e.variantA.sample + e.variantB.sample, 0).toLocaleString(), icon: <BarChart3 size={14} className="text-violet-pulse" /> },
        ].map((k) => (
          <Card key={k.label} variant="glass" className="p-4 text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">{k.icon}<span className="text-[10px] text-muted-silver uppercase tracking-wider">{k.label}</span></div>
            <span className="text-xl font-bold text-ghost-white font-mono">{k.value}</span>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(['all', 'running', 'completed', 'paused'] as const).map((f) => (
          <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${filter === f ? 'bg-electric-cyan/10 text-electric-cyan' : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/10'}`}>
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Experiment cards */}
      <div className="space-y-4">
        {filtered.map((exp) => {
          const sc = (statusCfg[exp.status] ?? statusCfg['running'])!;
          const chartData = [
            { name: exp.variantA.name, value: exp.variantA.value, fill: '#8892B0' },
            { name: exp.variantB.name, value: exp.variantB.value, fill: '#00D4FF' },
          ];
          return (
            <Card key={exp.id} variant="glass" className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <h3 className="text-sm font-semibold text-ghost-white">{exp.name}</h3>
                    <Badge variant="soft" color={sc.badge} size="sm">{exp.status}</Badge>
                    {exp.winner && <Badge variant="solid" color="emerald" size="sm">Winner: Variant {exp.winner}</Badge>}
                  </div>
                  <p className="text-xs text-muted-silver">Metric: <span className="text-electric-cyan">{exp.metric}</span> · Started {exp.startedAt}</p>
                </div>
                <div className="flex gap-1">
                  {exp.status === 'running' && (
                    <button
                      onClick={() => toggleStatus(exp.id)}
                      title="Pause experiment"
                      className="p-1.5 rounded-lg hover:bg-amber-glow/10 text-amber-glow cursor-pointer transition-colors"
                    >
                      <Pause size={14} />
                    </button>
                  )}
                  {exp.status === 'paused' && (
                    <button
                      onClick={() => toggleStatus(exp.id)}
                      title="Resume experiment"
                      className="p-1.5 rounded-lg hover:bg-neon-emerald/10 text-neon-emerald cursor-pointer transition-colors"
                    >
                      <Play size={14} />
                    </button>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Chart */}
                <div className="md:col-span-1">
                  <ResponsiveContainer width="100%" height={120}>
                    <BarChart data={chartData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E2642" horizontal={false} />
                      <XAxis type="number" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} domain={[0, 100]} />
                      <YAxis type="category" dataKey="name" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} width={90} />
                      <Tooltip contentStyle={{ background: '#121833', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '8px', color: '#E8ECF4', fontSize: 12 }} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {chartData.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Variant details */}
                <div className="md:col-span-2 grid grid-cols-2 gap-3">
                  {[exp.variantA, exp.variantB].map((v, i) => (
                    <div key={v.name} className={`p-3 rounded-lg border ${exp.winner === (i === 0 ? 'A' : 'B') ? 'border-neon-emerald/30 bg-neon-emerald/5' : 'border-steel-slate/15 bg-steel-slate/5'}`}>
                      <div className="flex items-center gap-1.5 mb-2">
                        {exp.winner === (i === 0 ? 'A' : 'B') ? <CheckCircle2 size={12} className="text-neon-emerald" /> : <XCircle size={12} className="text-muted-silver" />}
                        <span className="text-xs font-semibold text-ghost-white">{v.name}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div><span className="text-muted-silver block">Value</span><span className="text-ghost-white font-mono font-bold">{v.value}%</span></div>
                        <div><span className="text-muted-silver block">Samples</span><span className="text-ghost-white font-mono">{v.sample}</span></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Confidence bar */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-muted-silver">Statistical Confidence</span>
                  <span className={`font-mono font-bold ${exp.confidence >= 95 ? 'text-neon-emerald' : exp.confidence >= 80 ? 'text-amber-glow' : 'text-coral-flame'}`}>{exp.confidence}%</span>
                </div>
                <div className="w-full h-2 bg-steel-slate/20 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${exp.confidence >= 95 ? 'bg-neon-emerald' : exp.confidence >= 80 ? 'bg-amber-glow' : 'bg-coral-flame'}`} style={{ width: `${exp.confidence}%` }} />
                </div>
                {exp.confidence >= 95 && <p className="text-[10px] text-neon-emerald mt-1">✓ Statistically significant — safe to roll out</p>}
                {exp.confidence < 80 && <p className="text-[10px] text-coral-flame mt-1">⚠ Not yet significant — continue collecting data</p>}
              </div>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
