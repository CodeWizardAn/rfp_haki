import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  ArrowLeft,
  FileText,
  Clock,
  Search,
  CheckCircle2,
  Download,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle } from '@/components/ui';

/* ─── data ─── */

const rfpsByStatus = [
  { month: 'Sep', active: 12, completed: 28, draft: 5 },
  { month: 'Oct', active: 18, completed: 35, draft: 8 },
  { month: 'Nov', active: 15, completed: 41, draft: 4 },
  { month: 'Dec', active: 22, completed: 38, draft: 7 },
  { month: 'Jan', active: 20, completed: 45, draft: 6 },
  { month: 'Feb', active: 14, completed: 52, draft: 3 },
];

const processingDist = [
  { range: '0-1m', count: 18 },
  { range: '1-2m', count: 42 },
  { range: '2-3m', count: 65 },
  { range: '3-5m', count: 38 },
  { range: '5-10m', count: 12 },
  { range: '10m+', count: 4 },
];

const topCategories = [
  { category: 'LT Power Cables', count: 45 },
  { category: 'HT XLPE Cables', count: 38 },
  { category: 'Control Cables', count: 25 },
  { category: 'Instrumentation', count: 18 },
  { category: 'Fire Survival', count: 15 },
  { category: 'Wiring Cables', count: 12 },
  { category: 'Aerial Bunched', count: 8 },
  { category: 'Flexible Cables', count: 6 },
  { category: 'Submarine Cables', count: 3 },
  { category: 'Solar Cables', count: 2 },
];

const rfpSource = [
  { name: 'PDF Upload', value: 58, color: '#00D4FF' },
  { name: 'URL Scan', value: 22, color: '#7C3AED' },
  { name: 'Manual Entry', value: 15, color: '#FFB224' },
  { name: 'Email Import', value: 5, color: '#F472B6' },
];

const extractionAccuracy = [
  { month: 'Sep', accuracy: 82 },
  { month: 'Oct', accuracy: 85 },
  { month: 'Nov', accuracy: 88 },
  { month: 'Dec', accuracy: 91 },
  { month: 'Jan', accuracy: 93 },
  { month: 'Feb', accuracy: 94.2 },
];

const matchRateTrend = [
  { month: 'Sep', rate: 78 },
  { month: 'Oct', rate: 81 },
  { month: 'Nov', rate: 83 },
  { month: 'Dec', rate: 86 },
  { month: 'Jan', rate: 88 },
  { month: 'Feb', rate: 91 },
];

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
  { label: 'Total RFPs', value: '247', change: '+14%', icon: FileText, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10', positive: true },
  { label: 'Avg Processing', value: '3.2 min', change: '-18%', icon: Clock, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10', positive: true },
  { label: 'Extraction Acc.', value: '94.2%', change: '+3.5%', icon: CheckCircle2, color: 'text-amber-glow', bg: 'bg-amber-glow/10', positive: true },
  { label: 'Match Rate', value: '91%', change: '+5%', icon: Search, color: 'text-violet-pulse', bg: 'bg-violet-pulse/10', positive: true },
];

export default function RFPAnalyticsPage() {
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
            <h1 className="text-h1 text-ghost-white">RFP Analytics</h1>
            <p className="text-body text-muted-silver">Deep-dive into RFP processing metrics</p>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
            {['1m', '3m', '6m', '1y'].map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  range === r ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'
                }`}
              >
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
            <motion.div
              key={k.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="glass-card rounded-xl p-3 flex items-center gap-3"
            >
              <div className={`w-9 h-9 rounded-lg ${k.bg} flex items-center justify-center flex-shrink-0`}>
                <Icon size={16} className={k.color} />
              </div>
              <div>
                <p className="text-lg font-bold text-ghost-white leading-none">{k.value}</p>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="text-[10px] text-muted-silver">{k.label}</span>
                  <span className={`text-[10px] font-medium ${k.positive ? 'text-neon-emerald' : 'text-coral-flame'}`}>{k.change}</span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* RFPs by Status over Time */}
        <Card variant="glass" className="md:col-span-2">
          <CardHeader><CardTitle className="text-sm">RFPs by Status Over Time</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={rfpsByStatus}>
                <defs>
                  <linearGradient id="rfpComp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00E68A" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00E68A" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="rfpAct" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="rfpDraft" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8892B0" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8892B0" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Area type="monotone" dataKey="completed" stackId="1" stroke="#00E68A" fill="url(#rfpComp)" strokeWidth={2} />
                <Area type="monotone" dataKey="active" stackId="1" stroke="#00D4FF" fill="url(#rfpAct)" strokeWidth={2} />
                <Area type="monotone" dataKey="draft" stackId="1" stroke="#8892B0" fill="url(#rfpDraft)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-5 pb-3">
            {[{ name: 'Completed', color: '#00E68A' }, { name: 'Active', color: '#00D4FF' }, { name: 'Draft', color: '#8892B0' }].map((l) => (
              <div key={l.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: l.color }} />
                <span className="text-[10px] text-muted-silver">{l.name}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Processing Time Distribution */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Processing Time Distribution</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={processingDist} barSize={22}>
                <XAxis dataKey="range" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="count" fill="#7C3AED" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* RFP Source */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">RFP Source Channel</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={rfpSource} cx="50%" cy="50%" innerRadius={40} outerRadius={60} paddingAngle={3} dataKey="value">
                  {rfpSource.map((d) => <Cell key={d.name} fill={d.color} />)}
                </Pie>
                <Tooltip {...glassTooltip} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-3 pb-3">
            {rfpSource.map((d) => (
              <div key={d.name} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                <span className="text-[10px] text-muted-silver">{d.name} ({d.value}%)</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Top 10 Categories */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Top RFP Categories</CardTitle></CardHeader>
          <div className="px-4 pb-4 space-y-1.5">
            {topCategories.map((c, i) => {
              const max = topCategories[0]?.count ?? 1;
              return (
                <motion.div
                  key={c.category}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="flex items-center gap-2"
                >
                  <span className="text-[10px] text-muted-silver w-28 text-right flex-shrink-0 truncate">{c.category}</span>
                  <div className="flex-1 h-4 bg-steel-slate/15 rounded overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(c.count / max) * 100}%` }}
                      transition={{ duration: 0.5, delay: 0.1 + i * 0.03 }}
                      className="h-full rounded bg-electric-cyan/40"
                    />
                  </div>
                  <span className="text-[10px] font-semibold text-ghost-white w-6 text-right">{c.count}</span>
                </motion.div>
              );
            })}
          </div>
        </Card>

        {/* Extraction Accuracy */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Extraction Accuracy Trend</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={extractionAccuracy}>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} domain={[75, 100]} />
                <Tooltip {...glassTooltip} />
                <Line type="monotone" dataKey="accuracy" stroke="#00E68A" strokeWidth={2} dot={{ fill: '#00E68A', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Terms Match Rate */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Terms Match Rate Trend</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={matchRateTrend}>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} domain={[70, 100]} />
                <Tooltip {...glassTooltip} />
                <Line type="monotone" dataKey="rate" stroke="#00D4FF" strokeWidth={2} dot={{ fill: '#00D4FF', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
