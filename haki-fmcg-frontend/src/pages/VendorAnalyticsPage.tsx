import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  ArrowLeft,
  Building2,
  Star,
  CheckCircle2,
  Download,
  Users,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';

/* ─── data ─── */
const performanceTrend = [
  { month: 'Sep', havells: 88, finolex: 85, polycab: 82, kei: 78, rr: 74 },
  { month: 'Oct', havells: 89, finolex: 86, polycab: 84, kei: 80, rr: 76 },
  { month: 'Nov', havells: 91, finolex: 88, polycab: 83, kei: 79, rr: 75 },
  { month: 'Dec', havells: 90, finolex: 87, polycab: 86, kei: 81, rr: 77 },
  { month: 'Jan', havells: 92, finolex: 90, polycab: 88, kei: 83, rr: 78 },
  { month: 'Feb', havells: 93, finolex: 91, polycab: 87, kei: 82, rr: 80 },
];

const ratingDistribution = [
  { range: '4.5–5.0', count: 8, color: '#00E68A' },
  { range: '4.0–4.4', count: 12, color: '#14B8A6' },
  { range: '3.5–3.9', count: 10, color: '#FFB224' },
  { range: '3.0–3.4', count: 6, color: '#FF8C00' },
  { range: '<3.0', count: 4, color: '#FF4757' },
];

const topByCategory = [
  { category: 'LT Power', vendor: 'Havells', score: 95 },
  { category: 'HT XLPE', vendor: 'Finolex', score: 92 },
  { category: 'Control', vendor: 'Polycab', score: 90 },
  { category: 'Fire Survival', vendor: 'KEI', score: 88 },
  { category: 'Wiring', vendor: 'RR Kabel', score: 85 },
];

const vendorGrowth = [
  { month: 'Sep', total: 32, newVendors: 3 },
  { month: 'Oct', total: 34, newVendors: 2 },
  { month: 'Nov', total: 36, newVendors: 2 },
  { month: 'Dec', total: 38, newVendors: 2 },
  { month: 'Jan', total: 40, newVendors: 2 },
  { month: 'Feb', total: 42, newVendors: 2 },
];

const complianceDist = [
  { name: 'Compliant', value: 30, color: '#00E68A' },
  { name: 'Expiring Soon', value: 6, color: '#FFB224' },
  { name: 'Non-Compliant', value: 4, color: '#FF4757' },
  { name: 'Pending Review', value: 2, color: '#8892B0' },
];

const vendorColors: Record<string, string> = {
  havells: '#EF4444', finolex: '#3B82F6', polycab: '#F97316', kei: '#22C55E', rr: '#A855F7',
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
  { label: 'Total Vendors', value: '42', change: '+5', icon: Building2, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10' },
  { label: 'Avg Rating', value: '4.1', change: '+0.3', icon: Star, color: 'text-amber-glow', bg: 'bg-amber-glow/10' },
  { label: 'Compliance Rate', value: '88%', change: '+4%', icon: CheckCircle2, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10' },
  { label: 'New This Month', value: '2', change: '—', icon: Users, color: 'text-violet-pulse', bg: 'bg-violet-pulse/10' },
];

export default function VendorAnalyticsPage() {
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
            <h1 className="text-h1 text-ghost-white">Vendor Analytics</h1>
            <p className="text-body text-muted-silver">Performance trends, ratings & compliance</p>
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
        {/* Performance Trend (Multi-Line) */}
        <Card variant="glass" className="md:col-span-2">
          <CardHeader><CardTitle className="text-sm">Vendor Performance Trend</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceTrend}>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} domain={[65, 100]} />
                <Tooltip {...glassTooltip} />
                <Line type="monotone" dataKey="havells" stroke={vendorColors.havells} strokeWidth={2} dot={{ r: 3 }} name="Havells" />
                <Line type="monotone" dataKey="finolex" stroke={vendorColors.finolex} strokeWidth={2} dot={{ r: 3 }} name="Finolex" />
                <Line type="monotone" dataKey="polycab" stroke={vendorColors.polycab} strokeWidth={2} dot={{ r: 3 }} name="Polycab" />
                <Line type="monotone" dataKey="kei" stroke={vendorColors.kei} strokeWidth={2} dot={{ r: 3 }} name="KEI" />
                <Line type="monotone" dataKey="rr" stroke={vendorColors.rr} strokeWidth={2} dot={{ r: 3 }} name="RR Kabel" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            {Object.entries(vendorColors).map(([k, c]) => (
              <div key={k} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: c }} />
                <span className="text-[10px] text-muted-silver capitalize">{k === 'rr' ? 'RR Kabel' : k.charAt(0).toUpperCase() + k.slice(1)}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Rating Distribution */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Rating Distribution</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ratingDistribution} barSize={24}>
                <XAxis dataKey="range" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {ratingDistribution.map((d) => <Cell key={d.range} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Top Vendors by Category */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Top Vendor per Category</CardTitle></CardHeader>
          <div className="px-4 pb-4 space-y-2">
            {topByCategory.map((c, i) => (
              <motion.div key={c.category} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-3 py-1.5">
                <span className="text-xs text-muted-silver w-24 text-right flex-shrink-0">{c.category}</span>
                <div className="flex-1 flex items-center gap-2">
                  <div className="flex-1 h-5 bg-steel-slate/15 rounded overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${c.score}%` }}
                      transition={{ duration: 0.5, delay: 0.1 + i * 0.05 }}
                      className="h-full rounded bg-electric-cyan/40"
                    />
                  </div>
                  <Badge variant="soft" color="cyan" size="sm">{c.vendor}</Badge>
                  <span className="text-xs font-semibold text-ghost-white w-8 text-right">{c.score}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </Card>

        {/* Vendor Growth */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Vendor Growth Over Time</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={vendorGrowth}>
                <defs>
                  <linearGradient id="vaGrow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Area type="monotone" dataKey="total" stroke="#00D4FF" fill="url(#vaGrow)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Compliance Status */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Compliance Status</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={complianceDist} cx="50%" cy="50%" innerRadius={40} outerRadius={62} paddingAngle={3} dataKey="value">
                  {complianceDist.map((d) => <Cell key={d.name} fill={d.color} />)}
                </Pie>
                <Tooltip {...glassTooltip} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center pointer-events-none">
              <span className="text-xl font-bold text-ghost-white">42</span>
              <span className="text-[9px] text-muted-silver">Vendors</span>
            </div>
          </div>
          <div className="flex flex-wrap justify-center gap-3 pb-3">
            {complianceDist.map((d) => (
              <div key={d.name} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                <span className="text-[10px] text-muted-silver">{d.name} ({d.value})</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
