import { motion } from 'framer-motion';
import {
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp,
  Target,
  Clock,
  XCircle,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui';

/* ─── data ─── */
const winRateData = [
  { name: 'Won', value: 42, color: '#00E68A' },
  { name: 'Lost', value: 18, color: '#FF4757' },
  { name: 'Pending', value: 25, color: '#FFB224' },
];

const bidValueTrend = [
  { month: 'Sep', value: 85 },
  { month: 'Oct', value: 112 },
  { month: 'Nov', value: 98 },
  { month: 'Dec', value: 145 },
  { month: 'Jan', value: 132 },
  { month: 'Feb', value: 165 },
];

const approvalTime = [
  { level: 'PO', avg: 0.6 },
  { level: 'Manager', avg: 1.8 },
  { level: 'Director', avg: 2.4 },
  { level: 'CFO', avg: 1.2 },
];

const rejectionReasons = [
  { reason: 'Price too high', count: 8 },
  { reason: 'Compliance gap', count: 5 },
  { reason: 'Missing docs', count: 4 },
  { reason: 'Delivery terms', count: 3 },
  { reason: 'Vendor rating', count: 2 },
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
  { label: 'Win Rate', value: '68%', icon: Target, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10' },
  { label: 'Avg Bid Value', value: '₹12.4L', icon: TrendingUp, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10' },
  { label: 'Avg Approval', value: '2.1 days', icon: Clock, color: 'text-amber-glow', bg: 'bg-amber-glow/10' },
  { label: 'Rejection Rate', value: '12%', icon: XCircle, color: 'text-coral-flame', bg: 'bg-coral-flame/10' },
];

export default function BidAnalyticsWidget() {
  return (
    <div className="space-y-4">
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
                <p className="text-[10px] text-muted-silver">{k.label}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Win Rate Donut */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Win Rate Breakdown</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={winRateData} cx="50%" cy="50%" innerRadius={45} outerRadius={65} paddingAngle={3} dataKey="value">
                  {winRateData.map((d) => <Cell key={d.name} fill={d.color} />)}
                </Pie>
                <Tooltip {...glassTooltip} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center pointer-events-none">
              <span className="text-xl font-bold text-ghost-white">68%</span>
              <span className="text-[9px] text-muted-silver">Won</span>
            </div>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            {winRateData.map((d) => (
              <div key={d.name} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                <span className="text-[10px] text-muted-silver">{d.name} ({d.value})</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Bid Value Trend */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Avg Bid Value Trend (₹L)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={bidValueTrend}>
                <defs>
                  <linearGradient id="baTrend" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Area type="monotone" dataKey="value" stroke="#00D4FF" fill="url(#baTrend)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Approval Time */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Avg Approval Time (days)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={approvalTime} barSize={24}>
                <XAxis dataKey="level" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="avg" fill="#7C3AED" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Rejection Reasons */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Top Rejection Reasons</CardTitle></CardHeader>
          <div className="px-4 pb-4 space-y-2">
            {rejectionReasons.map((r, i) => {
              const max = rejectionReasons[0]?.count ?? 1;
              return (
                <motion.div
                  key={r.reason}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-3"
                >
                  <span className="text-xs text-muted-silver w-28 text-right flex-shrink-0 truncate">{r.reason}</span>
                  <div className="flex-1 h-5 bg-steel-slate/15 rounded-lg overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(r.count / max) * 100}%` }}
                      transition={{ duration: 0.5, delay: 0.2 + i * 0.05 }}
                      className="h-full rounded-lg bg-coral-flame/50"
                    />
                  </div>
                  <span className="text-xs font-semibold text-ghost-white w-6 text-right">{r.count}</span>
                </motion.div>
              );
            })}
          </div>
        </Card>
      </div>
    </div>
  );
}
