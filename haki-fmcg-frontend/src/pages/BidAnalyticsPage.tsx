import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  ArrowLeft,
  DollarSign,
  Target,
  Clock,
  Download,
  BarChart3,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle } from '@/components/ui';

/* ─── data ─── */
const conversionFunnel = [
  { name: 'Created', value: 120, fill: '#00D4FF' },
  { name: 'Submitted', value: 85, fill: '#7C3AED' },
  { name: 'Under Review', value: 62, fill: '#FFB224' },
  { name: 'Approved', value: 48, fill: '#00E68A' },
  { name: 'Won', value: 32, fill: '#14B8A6' },
];

const revenueByMonth = [
  { month: 'Sep', revenue: 245, bids: 18 },
  { month: 'Oct', revenue: 312, bids: 22 },
  { month: 'Nov', revenue: 280, bids: 20 },
  { month: 'Dec', revenue: 395, bids: 28 },
  { month: 'Jan', revenue: 420, bids: 32 },
  { month: 'Feb', revenue: 468, bids: 35 },
];

const bidValueByOEM = [
  { oem: 'Finolex', avg: 12.5, max: 28.0 },
  { oem: 'Havells', avg: 15.2, max: 35.0 },
  { oem: 'Polycab', avg: 11.8, max: 22.0 },
  { oem: 'KEI', avg: 9.4, max: 18.5 },
  { oem: 'RR Kabel', avg: 8.2, max: 15.0 },
];

const approvalDistribution = [
  { range: '<1d', count: 15 },
  { range: '1-2d', count: 28 },
  { range: '2-3d', count: 22 },
  { range: '3-5d', count: 12 },
  { range: '5-7d', count: 6 },
  { range: '7d+', count: 3 },
];

const rejectionBreakdown = [
  { reason: 'Pricing not competitive', count: 12 },
  { reason: 'Missing compliance docs', count: 8 },
  { reason: 'Delivery terms rejected', count: 6 },
  { reason: 'Vendor rating below threshold', count: 5 },
  { reason: 'Spec mismatch', count: 4 },
  { reason: 'Budget exceeded', count: 3 },
];

const winLossByVendor = [
  { vendor: 'Havells', won: 8, lost: 3 },
  { vendor: 'Finolex', won: 6, lost: 4 },
  { vendor: 'Polycab', won: 5, lost: 2 },
  { vendor: 'KEI', won: 4, lost: 5 },
  { vendor: 'RR Kabel', won: 3, lost: 4 },
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
  { label: 'Total Bids', value: '120', change: '+22%', icon: BarChart3, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10' },
  { label: 'Win Rate', value: '68%', change: '+5%', icon: Target, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10' },
  { label: 'Total Revenue', value: '₹4.7 Cr', change: '+18%', icon: DollarSign, color: 'text-amber-glow', bg: 'bg-amber-glow/10' },
  { label: 'Avg Approval', value: '2.1d', change: '-12%', icon: Clock, color: 'text-violet-pulse', bg: 'bg-violet-pulse/10' },
];

export default function BidAnalyticsPage() {
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
            <h1 className="text-h1 text-ghost-white">Bid Analytics</h1>
            <p className="text-body text-muted-silver">Conversion funnel, revenue & win/loss insights</p>
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
        {/* Conversion Funnel */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Bid-to-Win Conversion Funnel</CardTitle></CardHeader>
          <div className="px-4 pb-4 space-y-2">
            {conversionFunnel.map((stage, i) => {
              const maxVal = conversionFunnel[0]?.value ?? 1;
              const pct = (stage.value / maxVal) * 100;
              return (
                <motion.div key={stage.name} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }} className="flex items-center gap-3">
                  <span className="text-xs text-muted-silver w-24 text-right flex-shrink-0">{stage.name}</span>
                  <div className="flex-1 h-7 bg-steel-slate/15 rounded-lg overflow-hidden relative">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.6, delay: 0.15 + i * 0.08 }}
                      className="h-full rounded-lg"
                      style={{ background: stage.fill }}
                    />
                    <span className="absolute inset-y-0 left-3 flex items-center text-xs font-semibold text-ghost-white">{stage.value}</span>
                  </div>
                  <span className="text-[10px] text-muted-silver w-10 text-right">{Math.round(pct)}%</span>
                </motion.div>
              );
            })}
          </div>
        </Card>

        {/* Revenue by Month (Bar + Line) */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Monthly Revenue (₹L) & Bids</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenueByMonth} barSize={20}>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Bar yAxisId="left" dataKey="revenue" fill="#00D4FF" radius={[4, 4, 0, 0]} name="Revenue (₹L)" />
                <Line yAxisId="right" type="monotone" dataKey="bids" stroke="#FFB224" strokeWidth={2} dot={{ fill: '#FFB224', r: 3 }} name="Bids" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Avg Bid Value by OEM */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Bid Value by OEM (₹L)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={bidValueByOEM} layout="vertical" barGap={4} barSize={10}>
                <XAxis type="number" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="oem" type="category" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} width={60} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="avg" fill="#7C3AED" radius={[0, 4, 4, 0]} name="Avg" />
                <Bar dataKey="max" fill="#7C3AED" fillOpacity={0.3} radius={[0, 4, 4, 0]} name="Max" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Approval Time Distribution */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Approval Time Distribution</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={approvalDistribution} barSize={22}>
                <XAxis dataKey="range" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="count" fill="#14B8A6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Rejection Breakdown */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Rejection Reasons</CardTitle></CardHeader>
          <div className="px-4 pb-4 space-y-2">
            {rejectionBreakdown.map((r, i) => {
              const max = rejectionBreakdown[0]?.count ?? 1;
              return (
                <motion.div key={r.reason} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }} className="flex items-center gap-2">
                  <span className="text-[10px] text-muted-silver w-40 text-right flex-shrink-0 truncate">{r.reason}</span>
                  <div className="flex-1 h-4 bg-steel-slate/15 rounded overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${(r.count / max) * 100}%` }} transition={{ duration: 0.5, delay: 0.1 + i * 0.04 }} className="h-full rounded bg-coral-flame/50" />
                  </div>
                  <span className="text-xs font-semibold text-ghost-white w-6 text-right">{r.count}</span>
                </motion.div>
              );
            })}
          </div>
        </Card>

        {/* Win/Loss by Vendor */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Win/Loss by Vendor</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={winLossByVendor} barGap={2} barSize={14}>
                <XAxis dataKey="vendor" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="won" fill="#00E68A" radius={[3, 3, 0, 0]} name="Won" />
                <Bar dataKey="lost" fill="#FF4757" radius={[3, 3, 0, 0]} name="Lost" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-neon-emerald" /><span className="text-[10px] text-muted-silver">Won</span></div>
            <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-coral-flame" /><span className="text-[10px] text-muted-silver">Lost</span></div>
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
