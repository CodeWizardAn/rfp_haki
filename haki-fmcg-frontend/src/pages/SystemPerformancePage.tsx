import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  ArrowLeft,
  Cpu,
  HardDrive,
  Activity,
  Zap,
  Database,
  Download,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle } from '@/components/ui';

/* ─── data ─── */
const cpuMemory = [
  { time: '00:00', cpu: 24, mem: 52 },
  { time: '04:00', cpu: 18, mem: 48 },
  { time: '08:00', cpu: 45, mem: 61 },
  { time: '10:00', cpu: 72, mem: 75 },
  { time: '12:00', cpu: 65, mem: 70 },
  { time: '14:00', cpu: 58, mem: 68 },
  { time: '16:00', cpu: 80, mem: 78 },
  { time: '18:00', cpu: 42, mem: 62 },
  { time: '20:00', cpu: 30, mem: 55 },
  { time: '22:00', cpu: 22, mem: 50 },
];

const responseTime = [
  { time: '00:00', p50: 45, p90: 120, p99: 380 },
  { time: '04:00', p50: 38, p90: 95, p99: 280 },
  { time: '08:00', p50: 62, p90: 180, p99: 520 },
  { time: '10:00', p50: 85, p90: 240, p99: 680 },
  { time: '12:00', p50: 78, p90: 210, p99: 600 },
  { time: '14:00', p50: 68, p90: 190, p99: 540 },
  { time: '16:00', p50: 92, p90: 260, p99: 740 },
  { time: '18:00', p50: 55, p90: 150, p99: 420 },
  { time: '20:00', p50: 42, p90: 110, p99: 320 },
  { time: '22:00', p50: 35, p90: 88, p99: 260 },
];

const throughput = [
  { time: '00:00', rps: 12 },
  { time: '04:00', rps: 8 },
  { time: '08:00', rps: 45 },
  { time: '10:00', rps: 82 },
  { time: '12:00', rps: 75 },
  { time: '14:00', rps: 68 },
  { time: '16:00', rps: 95 },
  { time: '18:00', rps: 38 },
  { time: '20:00', rps: 22 },
  { time: '22:00', rps: 15 },
];

const errorEndpoints = [
  { endpoint: '/api/rfp/process', rate: 2.4 },
  { endpoint: '/api/pipeline/run', rate: 1.8 },
  { endpoint: '/api/vendors/search', rate: 0.9 },
  { endpoint: '/api/bids/export', rate: 0.5 },
  { endpoint: '/api/analytics/kpi', rate: 0.2 },
];

const dbMetrics = [
  { query: 'rfp_search', avg: 45, p99: 220 },
  { query: 'product_match', avg: 82, p99: 380 },
  { query: 'vendor_list', avg: 28, p99: 120 },
  { query: 'bid_summary', avg: 35, p99: 180 },
  { query: 'audit_log', avg: 18, p99: 85 },
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

/* ─── Gauge Component ─── */
function ResourceGauge({ label, value, unit, icon: Icon, color }: {
  label: string; value: number; unit: string;
  icon: React.ElementType; color: string;
}) {
  const pct = Math.min(value, 100);
  const ringColor = pct > 80 ? '#FF4757' : pct > 60 ? '#FFB224' : '#00E68A';
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="glass-card rounded-xl p-4 flex flex-col items-center">
      <div className="relative w-20 h-20">
        <svg viewBox="0 0 80 80" className="w-20 h-20 -rotate-90">
          <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(30,38,66,0.5)" strokeWidth="6" />
          <motion.circle
            cx="40" cy="40" r="36" fill="none" stroke={ringColor} strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-bold text-ghost-white">{value}</span>
          <span className="text-[9px] text-muted-silver">{unit}</span>
        </div>
      </div>
      <div className="flex items-center gap-1 mt-2">
        <Icon size={12} className={color} />
        <span className="text-xs text-muted-silver">{label}</span>
      </div>
    </div>
  );
}

export default function SystemPerformancePage() {
  const [range, setRange] = useState('24h');

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/analytics" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">System Performance</h1>
            <p className="text-body text-muted-silver">Infrastructure & API metrics</p>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
            {['1h', '6h', '24h', '7d'].map((r) => (
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

      {/* Resource Gauges */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <ResourceGauge label="CPU Usage" value={42} unit="%" icon={Cpu} color="text-electric-cyan" />
        <ResourceGauge label="Memory" value={62} unit="%" icon={HardDrive} color="text-amber-glow" />
        <ResourceGauge label="Disk I/O" value={28} unit="%" icon={Database} color="text-neon-emerald" />
        <ResourceGauge label="Network" value={35} unit="Mbps" icon={Activity} color="text-violet-pulse" />
        <ResourceGauge label="Cache Hit" value={94} unit="%" icon={Zap} color="text-neon-emerald" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* CPU & Memory Timeline */}
        <Card variant="glass" className="md:col-span-2">
          <CardHeader><CardTitle className="text-sm">CPU & Memory Usage Timeline</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cpuMemory}>
                <defs>
                  <linearGradient id="spCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="spMem" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FFB224" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#FFB224" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} unit="%" domain={[0, 100]} />
                <Tooltip {...glassTooltip} />
                <Area type="monotone" dataKey="cpu" stroke="#00D4FF" fill="url(#spCpu)" strokeWidth={2} name="CPU %" />
                <Area type="monotone" dataKey="mem" stroke="#FFB224" fill="url(#spMem)" strokeWidth={2} name="Memory %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-5 pb-3">
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-electric-cyan" /><span className="text-[10px] text-muted-silver">CPU</span></div>
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-glow" /><span className="text-[10px] text-muted-silver">Memory</span></div>
          </div>
        </Card>

        {/* API Response Time Percentiles */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">API Response Time (ms)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={responseTime}>
                <XAxis dataKey="time" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Line type="monotone" dataKey="p50" stroke="#00E68A" strokeWidth={2} dot={false} name="P50" />
                <Line type="monotone" dataKey="p90" stroke="#FFB224" strokeWidth={2} dot={false} name="P90" />
                <Line type="monotone" dataKey="p99" stroke="#FF4757" strokeWidth={2} dot={false} name="P99" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-neon-emerald" /><span className="text-[10px] text-muted-silver">P50</span></div>
            <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-glow" /><span className="text-[10px] text-muted-silver">P90</span></div>
            <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-coral-flame" /><span className="text-[10px] text-muted-silver">P99</span></div>
          </div>
        </Card>

        {/* Throughput */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Request Throughput (req/s)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={throughput}>
                <defs>
                  <linearGradient id="spThru" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#7C3AED" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Area type="monotone" dataKey="rps" stroke="#7C3AED" fill="url(#spThru)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Error Rate by Endpoint */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Error Rate by Endpoint (%)</CardTitle></CardHeader>
          <div className="px-4 pb-4 space-y-2">
            {errorEndpoints.map((e, i) => (
              <motion.div
                key={e.endpoint}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-2"
              >
                <span className="text-[10px] text-muted-silver font-mono w-36 text-right truncate flex-shrink-0">{e.endpoint}</span>
                <div className="flex-1 h-4 bg-steel-slate/15 rounded overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(e.rate / 3) * 100}%` }}
                    transition={{ duration: 0.5, delay: 0.1 + i * 0.04 }}
                    className={`h-full rounded ${e.rate > 2 ? 'bg-coral-flame/60' : e.rate > 1 ? 'bg-amber-glow/60' : 'bg-neon-emerald/40'}`}
                  />
                </div>
                <span className={`text-xs font-semibold w-10 text-right ${e.rate > 2 ? 'text-coral-flame' : e.rate > 1 ? 'text-amber-glow' : 'text-neon-emerald'}`}>
                  {e.rate}%
                </span>
              </motion.div>
            ))}
          </div>
        </Card>

        {/* Database Query Performance */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Database Query Performance (ms)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dbMetrics} barGap={4} barSize={14}>
                <XAxis dataKey="query" tick={{ fill: '#8892B0', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="avg" fill="#00D4FF" radius={[3, 3, 0, 0]} name="Avg" />
                <Bar dataKey="p99" fill="#FF4757" radius={[3, 3, 0, 0]} name="P99" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-electric-cyan" /><span className="text-[10px] text-muted-silver">Avg</span></div>
            <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-coral-flame" /><span className="text-[10px] text-muted-silver">P99</span></div>
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
