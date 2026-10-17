import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,

  Download,

  DollarSign,
  FileText,

  Gavel,
  Bot,
  Clock,

  Target,

} from 'lucide-react';
import { AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Button, Card, CardHeader, CardTitle } from '@/components/ui';
import { formatCompactCurrency } from '@/utils/formatters';
import { useAnalyticsOverview, useRFPAnalytics, usePerformanceMetrics } from '@/hooks/useApi';

const monthlyData = [
  { month: 'Sep', rfps: 12, bids: 8, revenue: 4200000 },
  { month: 'Oct', rfps: 18, bids: 14, revenue: 6800000 },
  { month: 'Nov', rfps: 15, bids: 11, revenue: 5400000 },
  { month: 'Dec', rfps: 22, bids: 18, revenue: 8900000 },
  { month: 'Jan', rfps: 28, bids: 22, revenue: 12400000 },
  { month: 'Feb', rfps: 14, bids: 10, revenue: 5600000 },
];

const categoryData = [
  { name: 'HT Cable', value: 35, color: '#00D4FF' },
  { name: 'LT Cable', value: 28, color: '#00E68A' },
  { name: 'House Wire', value: 18, color: '#FFB224' },
  { name: 'Control Cable', value: 12, color: '#7C3AED' },
  { name: 'Other', value: 7, color: '#FF4757' },
];

const agentPerformance = [
  { agent: 'Sales', time: 4.5, success: 94, color: '#00D4FF' },
  { agent: 'Technical', time: 12.3, success: 97, color: '#14B8A6' },
  { agent: 'Pricing', time: 3.8, success: 98, color: '#FFB224' },
  { agent: 'Master', time: 1.2, success: 99, color: '#7C3AED' },
];

const oemWinRate = [
  { oem: 'Havells', wins: 35, losses: 7 },
  { oem: 'Polycab', wins: 28, losses: 10 },
  { oem: 'KEI', wins: 18, losses: 6 },
  { oem: 'Finolex', wins: 22, losses: 9 },
  { oem: 'RR Kabel', wins: 12, losses: 7 },
];

const tooltipStyle = {
  contentStyle: {
    backgroundColor: '#0F172A',
    border: '1px solid #334155',
    borderRadius: '8px',
    fontSize: '12px',
    color: '#F8FAFC',
    boxShadow: '0 8px 20px rgba(0, 0, 0, 0.35)',
  },
  labelStyle: { color: '#94A3B8', fontWeight: 600, fontSize: '11px' },
  itemStyle: { color: '#FFFFFF', fontWeight: 600, fontSize: '12px' },
};

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d' | '1y'>('30d');

  /* ── Backend hooks ── */
  const { data: apiOverview } = useAnalyticsOverview();
  const { data: _apiRfpAnalytics } = useRFPAnalytics(period);
  const { data: _apiPerformance } = usePerformanceMetrics();

  /* Merge monthly data from backend or fall back to mock */
  const activeMonthlyData = useMemo(() => {
    const overview = apiOverview as Record<string, unknown> | undefined;
    if (overview?.monthly_data && Array.isArray(overview.monthly_data)) {
      return overview.monthly_data as typeof monthlyData;
    }
    return monthlyData;
  }, [apiOverview]);

  const totalRevenue = activeMonthlyData.reduce((s, d) => s + d.revenue, 0);
  const totalRFPs = activeMonthlyData.reduce((s, d) => s + d.rfps, 0);
  const totalBids = activeMonthlyData.reduce((s, d) => s + d.bids, 0);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-electric-cyan/10">
            <BarChart3 size={24} className="text-electric-cyan" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Analytics Dashboard</h1>
            <p className="text-body text-muted-silver">Insights, metrics, and performance analytics</p>
          </div>
        </div>
        <div className="flex gap-2 items-center flex-shrink-0">
          <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
            {(['7d', '30d', '90d', '1y'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                  period === p ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
          <Button variant="secondary" size="sm" leftIcon={<Download size={12} />}>Export</Button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Revenue', value: formatCompactCurrency(totalRevenue), icon: <DollarSign size={16} />, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10', change: '+18.5%' },
          { label: 'RFPs Processed', value: totalRFPs, icon: <FileText size={16} />, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10', change: '+12.3%' },
          { label: 'Bids Generated', value: totalBids, icon: <Gavel size={16} />, color: 'text-amber-glow', bg: 'bg-amber-glow/10', change: '+22.1%' },
          { label: 'Avg Pipeline Time', value: '21.4s', icon: <Clock size={16} />, color: 'text-violet-pulse', bg: 'bg-violet-pulse/10', change: '-8.2%' },
        ].map((kpi) => (
          <Card key={kpi.label} variant="glass">
            <div className="flex items-start justify-between mb-2">
              <div className={`p-2 rounded-lg ${kpi.bg}`}>
                <span className={kpi.color}>{kpi.icon}</span>
              </div>
              <span className={`text-xs font-medium ${kpi.change.startsWith('+') ? 'text-neon-emerald' : 'text-coral-flame'}`}>
                {kpi.change}
              </span>
            </div>
            <p className="text-2xl font-bold text-ghost-white">{kpi.value}</p>
            <p className="text-xs text-muted-silver mt-1">{kpi.label}</p>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend */}
        <Card variant="glass">
          <CardHeader><CardTitle>Revenue Trend</CardTitle></CardHeader>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={activeMonthlyData}>
              <defs>
                <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00E68A" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#00E68A" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" stroke="#8892B0" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#8892B0" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v: number) => `₹${(v / 100000).toFixed(0)}L`} />
              <Tooltip {...tooltipStyle} formatter={(value: unknown) => formatCompactCurrency(Number(value))} />
              <Area type="monotone" dataKey="revenue" stroke="#00E68A" fill="url(#revGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        {/* RFP Category Distribution */}
        <Card variant="glass">
          <CardHeader><CardTitle>RFP by Category</CardTitle></CardHeader>
          <div className="flex items-center">
            <ResponsiveContainer width="50%" height={250}>
              <PieChart>
                <Pie data={categoryData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" paddingAngle={3}>
                  {categoryData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip {...tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-2 flex-1">
              {categoryData.map((cat) => (
                <div key={cat.name} className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                  <span className="text-xs text-ghost-white flex-1">{cat.name}</span>
                  <span className="text-xs text-muted-silver">{cat.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Performance */}
        <Card variant="glass">
          <CardHeader><CardTitle>Agent Performance</CardTitle></CardHeader>
          <div className="space-y-3">
            {agentPerformance.map((agent) => (
              <div key={agent.agent} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: agent.color + '15' }}>
                  <Bot size={14} style={{ color: agent.color }} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-ghost-white">{agent.agent} Agent</span>
                    <div className="flex gap-3 text-xs">
                      <span className="text-muted-silver"><Clock size={10} className="inline mr-1" />{agent.time}s avg</span>
                      <span className="text-neon-emerald"><Target size={10} className="inline mr-1" />{agent.success}%</span>
                    </div>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-steel-slate/30">
                    <div className="h-full rounded-full" style={{ width: `${agent.success}%`, backgroundColor: agent.color }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* OEM Win Rate */}
        <Card variant="glass">
          <CardHeader><CardTitle>OEM Win Rate</CardTitle></CardHeader>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={oemWinRate} layout="vertical">
              <XAxis type="number" stroke="#8892B0" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="oem" stroke="#8892B0" fontSize={11} tickLine={false} axisLine={false} width={60} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="wins" stackId="a" fill="#00E68A" radius={[0, 0, 0, 0]} />
              <Bar dataKey="losses" stackId="a" fill="#FF4757" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-4 mt-2 text-xs text-muted-silver justify-center">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-neon-emerald" /> Won</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-coral-flame" /> Lost</span>
          </div>
        </Card>
      </div>

      {/* RFP + Bid Volume */}
      <Card variant="glass">
        <CardHeader><CardTitle>Monthly Volume: RFPs vs Bids</CardTitle></CardHeader>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={activeMonthlyData}>
            <XAxis dataKey="month" stroke="#8892B0" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="#8892B0" fontSize={11} tickLine={false} axisLine={false} />
            <Tooltip {...tooltipStyle} />
            <Bar dataKey="rfps" fill="#00D4FF" radius={[4, 4, 0, 0]} name="RFPs" />
            <Bar dataKey="bids" fill="#7C3AED" radius={[4, 4, 0, 0]} name="Bids" />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </motion.div>
  );
}
