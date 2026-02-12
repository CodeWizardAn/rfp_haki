import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import {
  ArrowLeft,
  Bot,
  Zap,
  CheckCircle2,
  Clock,
  Target,
  Download,
  AlertTriangle,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';

/* ─── data ─── */
const executionTime = [
  { agent: 'Sales', avg: 1.4, p95: 2.8, color: '#3B82F6' },
  { agent: 'Technical', avg: 2.1, p95: 4.2, color: '#F97316' },
  { agent: 'Pricing', avg: 0.9, p95: 1.6, color: '#22C55E' },
  { agent: 'Master', avg: 3.2, p95: 5.1, color: '#A855F7' },
];

const successTrend = [
  { month: 'Sep', sales: 95, technical: 88, pricing: 97, master: 92 },
  { month: 'Oct', sales: 94, technical: 90, pricing: 96, master: 91 },
  { month: 'Nov', sales: 96, technical: 91, pricing: 98, master: 93 },
  { month: 'Dec', sales: 95, technical: 89, pricing: 97, master: 94 },
  { month: 'Jan', sales: 97, technical: 92, pricing: 98, master: 95 },
  { month: 'Feb', sales: 98, technical: 93, pricing: 99, master: 96 },
];

const accuracyRadar = [
  { metric: 'Product Match', sales: 92, technical: 95, pricing: 88, master: 90 },
  { metric: 'Spec Extract', sales: 85, technical: 96, pricing: 80, master: 91 },
  { metric: 'Price Accuracy', sales: 78, technical: 82, pricing: 97, master: 90 },
  { metric: 'Compliance', sales: 88, technical: 90, pricing: 85, master: 94 },
  { metric: 'Response Time', sales: 95, technical: 82, pricing: 98, master: 88 },
  { metric: 'RFP Coverage', sales: 90, technical: 93, pricing: 92, master: 96 },
];

const heatmapData: { day: string; hours: number[] }[] = [
  { day: 'Mon', hours: [12, 18, 25, 30, 22, 15, 10, 5] },
  { day: 'Tue', hours: [8, 22, 28, 35, 30, 18, 12, 6] },
  { day: 'Wed', hours: [10, 20, 32, 40, 35, 25, 14, 8] },
  { day: 'Thu', hours: [14, 24, 30, 38, 28, 20, 11, 4] },
  { day: 'Fri', hours: [6, 16, 22, 28, 20, 14, 8, 3] },
];
const heatSlots = ['9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm', '4pm'];

const recentRuns = [
  { id: 'R-142', agent: 'Sales', rfp: 'RFP-2024-089', status: 'success', duration: '1.2s', ts: '2 min ago' },
  { id: 'R-141', agent: 'Technical', rfp: 'RFP-2024-089', status: 'success', duration: '2.4s', ts: '3 min ago' },
  { id: 'R-140', agent: 'Pricing', rfp: 'RFP-2024-089', status: 'success', duration: '0.8s', ts: '4 min ago' },
  { id: 'R-139', agent: 'Master', rfp: 'RFP-2024-088', status: 'warning', duration: '4.8s', ts: '12 min ago' },
  { id: 'R-138', agent: 'Technical', rfp: 'RFP-2024-088', status: 'error', duration: '5.2s', ts: '14 min ago' },
  { id: 'R-137', agent: 'Sales', rfp: 'RFP-2024-087', status: 'success', duration: '1.1s', ts: '20 min ago' },
];

const agentColors: Record<string, string> = {
  sales: '#3B82F6', technical: '#F97316', pricing: '#22C55E', master: '#A855F7',
};

const glassTooltip = {
  contentStyle: {
    background: 'rgba(18,24,51,0.92)',
    border: '1px solid rgba(0,212,255,0.15)',
    borderRadius: 10,
    color: '#E8ECF4',
    fontSize: 12,
  },
  cursor: { stroke: 'rgba(0,212,255,0.25)' },
};

const kpis = [
  { label: 'Total Executions', value: '3,842', change: '+312', icon: Bot, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10' },
  { label: 'Avg Latency', value: '1.9s', change: '-0.3s', icon: Zap, color: 'text-amber-glow', bg: 'bg-amber-glow/10' },
  { label: 'Success Rate', value: '96.2%', change: '+1.4%', icon: CheckCircle2, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10' },
  { label: 'Accuracy Score', value: '91.5', change: '+2.1', icon: Target, color: 'text-violet-pulse', bg: 'bg-violet-pulse/10' },
];

function heatColor(v: number) {
  if (v >= 35) return 'bg-electric-cyan/70';
  if (v >= 25) return 'bg-electric-cyan/45';
  if (v >= 15) return 'bg-electric-cyan/25';
  if (v >= 8) return 'bg-electric-cyan/12';
  return 'bg-electric-cyan/5';
}

export default function AgentAnalyticsPage() {
  const [range, setRange] = useState('6m');

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/analytics" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Agent Analytics</h1>
            <p className="text-body text-muted-silver">Execution metrics, accuracy & activity</p>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
            {['1m', '3m', '6m', '1y'].map((r) => (
              <button key={r} onClick={() => setRange(r)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${range === r ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'}`}>
                {r}
              </button>
            ))}
          </div>
          <Button variant="secondary" leftIcon={<Download size={14} />}>Export</Button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {kpis.map((k, i) => {
          const Icon = k.icon;
          return (
            <motion.div key={k.label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} className="glass-card rounded-xl p-3 flex items-center gap-3">
              <div className={`w-9 h-9 rounded-lg ${k.bg} flex items-center justify-center flex-shrink-0`}>
                <Icon size={16} className={k.color} />
              </div>
              <div>
                <p className="text-lg font-bold text-ghost-white leading-none">{k.value}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="text-[10px] text-muted-silver">{k.label}</span>
                  <span className="text-[10px] font-medium text-neon-emerald">{k.change}</span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Execution Time Comparison */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Avg Execution Time (seconds)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={executionTime} barSize={18} barGap={3}>
                <XAxis dataKey="agent" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} unit="s" />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="avg" name="Avg" radius={[4, 4, 0, 0]}>
                  {executionTime.map((d) => <Cell key={d.agent} fill={d.color} fillOpacity={0.8} />)}
                </Bar>
                <Bar dataKey="p95" name="P95" radius={[4, 4, 0, 0]}>
                  {executionTime.map((d) => <Cell key={d.agent} fill={d.color} fillOpacity={0.35} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Success Rate Trend */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Success Rate Trend (%)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={successTrend}>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} domain={[80, 100]} />
                <Tooltip {...glassTooltip} />
                <Line type="monotone" dataKey="sales" stroke={agentColors.sales} strokeWidth={2} dot={{ r: 2.5 }} name="Sales" />
                <Line type="monotone" dataKey="technical" stroke={agentColors.technical} strokeWidth={2} dot={{ r: 2.5 }} name="Technical" />
                <Line type="monotone" dataKey="pricing" stroke={agentColors.pricing} strokeWidth={2} dot={{ r: 2.5 }} name="Pricing" />
                <Line type="monotone" dataKey="master" stroke={agentColors.master} strokeWidth={2} dot={{ r: 2.5 }} name="Master" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            {Object.entries(agentColors).map(([k, c]) => (
              <div key={k} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: c }} />
                <span className="text-[10px] text-muted-silver capitalize">{k}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Accuracy Radar */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Accuracy Radar</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-60">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={accuracyRadar}>
                <PolarGrid stroke="rgba(136,146,176,0.15)" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#8892B0', fontSize: 9 }} />
                <PolarRadiusAxis tick={{ fill: '#8892B0', fontSize: 8 }} domain={[60, 100]} />
                <Radar name="Sales" dataKey="sales" stroke={agentColors.sales} fill={agentColors.sales} fillOpacity={0.12} strokeWidth={1.5} />
                <Radar name="Technical" dataKey="technical" stroke={agentColors.technical} fill={agentColors.technical} fillOpacity={0.12} strokeWidth={1.5} />
                <Radar name="Pricing" dataKey="pricing" stroke={agentColors.pricing} fill={agentColors.pricing} fillOpacity={0.12} strokeWidth={1.5} />
                <Radar name="Master" dataKey="master" stroke={agentColors.master} fill={agentColors.master} fillOpacity={0.12} strokeWidth={1.5} />
                <Tooltip {...glassTooltip} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Activity Heatmap */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Activity Heatmap (Executions)</CardTitle></CardHeader>
          <div className="px-4 pb-4">
            <div className="flex items-start gap-2">
              <div className="flex flex-col gap-1 pt-5">
                {heatmapData.map((row) => (
                  <span key={row.day} className="text-[10px] text-muted-silver h-6 flex items-center">{row.day}</span>
                ))}
              </div>
              <div className="flex-1">
                <div className="flex gap-1 mb-1">
                  {heatSlots.map((s) => <span key={s} className="text-[9px] text-muted-silver flex-1 text-center">{s}</span>)}
                </div>
                {heatmapData.map((row) => (
                  <div key={row.day} className="flex gap-1 mb-1">
                    {row.hours.map((v, hi) => (
                      <motion.div
                        key={hi}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.02 * hi }}
                        className={`flex-1 h-6 rounded ${heatColor(v)} flex items-center justify-center`}
                        title={`${row.day} ${heatSlots[hi]}: ${v} runs`}
                      >
                        <span className="text-[8px] text-ghost-white/60">{v}</span>
                      </motion.div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Executions */}
      <Card variant="glass">
        <CardHeader><CardTitle className="text-sm">Recent Agent Executions</CardTitle></CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-steel-slate/15 text-muted-silver">
                <th className="text-left p-2 pl-4">Run</th>
                <th className="text-left p-2">Agent</th>
                <th className="text-left p-2">RFP</th>
                <th className="text-left p-2">Status</th>
                <th className="text-right p-2">Duration</th>
                <th className="text-right p-2 pr-4">Time</th>
              </tr>
            </thead>
            <tbody>
              {recentRuns.map((r) => (
                <tr key={r.id} className="border-b border-steel-slate/10 hover:bg-steel-slate/5 transition-colors">
                  <td className="p-2 pl-4 text-ghost-white font-mono">{r.id}</td>
                  <td className="p-2">
                    <Badge variant="soft" color={r.agent === 'Sales' ? 'blue' : r.agent === 'Technical' ? 'amber' : r.agent === 'Pricing' ? 'green' : 'purple'} size="sm">
                      {r.agent}
                    </Badge>
                  </td>
                  <td className="p-2 text-muted-silver">{r.rfp}</td>
                  <td className="p-2">
                    {r.status === 'success' && <span className="flex items-center gap-1 text-neon-emerald"><CheckCircle2 size={11} /> Success</span>}
                    {r.status === 'warning' && <span className="flex items-center gap-1 text-amber-glow"><AlertTriangle size={11} /> Warning</span>}
                    {r.status === 'error' && <span className="flex items-center gap-1 text-coral-flame"><AlertTriangle size={11} /> Error</span>}
                  </td>
                  <td className="p-2 text-right text-ghost-white font-mono flex items-center justify-end gap-1"><Clock size={10} className="text-muted-silver" />{r.duration}</td>
                  <td className="p-2 pr-4 text-right text-muted-silver">{r.ts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
