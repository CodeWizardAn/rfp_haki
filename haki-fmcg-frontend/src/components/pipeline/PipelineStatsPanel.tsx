import { motion } from 'framer-motion';
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  Clock,
  CheckCircle2,
  XCircle,
  Zap,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui';

/* ─── duration trend ─── */
const durationData = [
  { day: 'Mon', avg: 4.2 },
  { day: 'Tue', avg: 3.8 },
  { day: 'Wed', avg: 5.1 },
  { day: 'Thu', avg: 3.5 },
  { day: 'Fri', avg: 3.9 },
  { day: 'Sat', avg: 2.8 },
  { day: 'Sun', avg: 3.1 },
];

/* ─── success / fail donut ─── */
const outcomeData = [
  { name: 'Success', value: 84, color: '#00E68A' },
  { name: 'Partial', value: 10, color: '#FFB224' },
  { name: 'Failed', value: 6, color: '#FF4757' },
];

/* ─── failure by stage ─── */
const failureStages = [
  { stage: 'Extract', count: 3 },
  { stage: 'Match', count: 8 },
  { stage: 'Price', count: 2 },
  { stage: 'Comply', count: 5 },
  { stage: 'Review', count: 1 },
];

/* ─── throughput trend ─── */
const throughputData = [
  { week: 'W1', runs: 32 },
  { week: 'W2', runs: 45 },
  { week: 'W3', runs: 38 },
  { week: 'W4', runs: 52 },
  { week: 'W5', runs: 61 },
  { week: 'W6', runs: 48 },
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

const statCards = [
  { label: 'Avg Duration', value: '3.6 min', icon: Clock, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10' },
  { label: 'Success Rate', value: '84%', icon: CheckCircle2, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10' },
  { label: 'Failed Today', value: '2', icon: XCircle, color: 'text-coral-flame', bg: 'bg-coral-flame/10' },
  { label: 'Throughput', value: '48/wk', icon: Zap, color: 'text-amber-glow', bg: 'bg-amber-glow/10' },
];

export default function PipelineStatsPanel() {
  return (
    <div className="space-y-4">
      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {statCards.map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="glass-card rounded-xl p-3 flex items-center gap-3"
            >
              <div className={`w-9 h-9 rounded-lg ${s.bg} flex items-center justify-center flex-shrink-0`}>
                <Icon size={16} className={s.color} />
              </div>
              <div>
                <p className="text-lg font-bold text-ghost-white leading-none">{s.value}</p>
                <p className="text-[10px] text-muted-silver">{s.label}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Duration Trend */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Avg Duration Trend</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={durationData}>
                <defs>
                  <linearGradient id="psDur" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} unit=" m" />
                <Tooltip {...glassTooltip} />
                <Area type="monotone" dataKey="avg" stroke="#00D4FF" fill="url(#psDur)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Success Rate Donut */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Outcome Distribution</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={outcomeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={65}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {outcomeData.map((d) => (
                    <Cell key={d.name} fill={d.color} />
                  ))}
                </Pie>
                <Tooltip {...glassTooltip} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center pointer-events-none">
              <span className="text-xl font-bold text-ghost-white">84%</span>
              <span className="text-[9px] text-muted-silver">Success</span>
            </div>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            {outcomeData.map((d) => (
              <div key={d.name} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                <span className="text-[10px] text-muted-silver">{d.name} {d.value}%</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Failure Stages */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Failure by Stage</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={failureStages} barSize={18}>
                <XAxis dataKey="stage" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="count" fill="#FF4757" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Throughput Trend */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Weekly Throughput</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={throughputData}>
                <defs>
                  <linearGradient id="psThru" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00E68A" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00E68A" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="week" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Area type="monotone" dataKey="runs" stroke="#00E68A" fill="url(#psThru)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}
