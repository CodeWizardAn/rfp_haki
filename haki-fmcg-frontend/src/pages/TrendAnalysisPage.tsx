import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from 'recharts';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Activity,
  Download,
  Eye,
  EyeOff,
  AlertTriangle,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle } from '@/components/ui';

/* ─── data ─── */
const months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'];

// Historical + forecast (last 2 are forecast)
const trendData = months.map((m, i) => ({
  month: m,
  rfps: [42, 48, 55, 52, 60, 58, 65, 70][i],
  winRate: [62, 64, 66, 63, 68, 70, 72, 74][i],
  revenue: [2.1, 2.4, 2.8, 2.6, 3.1, 3.0, 3.4, 3.8][i],
  matchScore: [82, 84, 85, 83, 87, 88, 90, 92][i],
  // Moving averages (7-day equivalent for monthly = 3-month)
  rfpsMa: [null, null, 48.3, 51.7, 55.7, 56.7, 61.0, 64.3][i] as number | null,
  winRateMa: [null, null, 64.0, 64.3, 65.7, 67.0, 70.0, 72.0][i] as number | null,
  revenueMa: [null, null, 2.43, 2.6, 2.83, 2.9, 3.17, 3.4][i] as number | null,
  isForecast: i >= 6,
  isAnomaly: i === 3, // Oct dip
}));

interface MetricDef {
  key: string;
  label: string;
  color: string;
  maKey: string;
  unit: string;
  current: string;
  change: string;
  changeDir: 'up' | 'down';
}

const metricDefs: MetricDef[] = [
  { key: 'rfps', label: 'RFP Volume', color: '#00D4FF', maKey: 'rfpsMa', unit: '', current: '65', change: '+12%', changeDir: 'up' },
  { key: 'winRate', label: 'Win Rate', color: '#00E68A', maKey: 'winRateMa', unit: '%', current: '72%', change: '+4%', changeDir: 'up' },
  { key: 'revenue', label: 'Revenue (₹ Cr)', color: '#FFB224', maKey: 'revenueMa', unit: ' Cr', current: '₹3.4 Cr', change: '+13%', changeDir: 'up' },
  { key: 'matchScore', label: 'Match Score', color: '#7C3AED', maKey: '', unit: '', current: '90', change: '+2.3', changeDir: 'up' },
];

const correlations = [
  { pair: 'RFP Volume ↔ Revenue', r: 0.94, strength: 'Strong +' },
  { pair: 'Win Rate ↔ Match Score', r: 0.87, strength: 'Strong +' },
  { pair: 'RFP Volume ↔ Win Rate', r: 0.72, strength: 'Moderate +' },
  { pair: 'Revenue ↔ Match Score', r: 0.65, strength: 'Moderate +' },
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

export default function TrendAnalysisPage() {
  const [range, setRange] = useState('6m');
  const [visibleMetrics, setVisibleMetrics] = useState<Set<string>>(new Set(['rfps', 'winRate', 'revenue', 'matchScore']));
  const [showMa, setShowMa] = useState(true);
  const [showForecast, setShowForecast] = useState(true);
  const [showAnomalies, setShowAnomalies] = useState(true);

  const toggleMetric = (key: string) => {
    setVisibleMetrics((prev) => {
      const next = new Set(prev);
      if (next.has(key)) { if (next.size > 1) next.delete(key); }
      else next.add(key);
      return next;
    });
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/analytics" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Trend Analysis</h1>
            <p className="text-body text-muted-silver">Multi-metric trends, forecasts & correlations</p>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
            {['3m', '6m', '1y', '2y'].map((r) => (
              <button key={r} onClick={() => setRange(r)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${range === r ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'}`}>
                {r}
              </button>
            ))}
          </div>
          <Button variant="secondary" leftIcon={<Download size={14} />}>Export</Button>
        </div>
      </div>

      {/* Metric KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {metricDefs.map((m, i) => (
          <motion.button
            key={m.key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            onClick={() => toggleMetric(m.key)}
            className={`glass-card rounded-xl p-3 text-left transition-all ${visibleMetrics.has(m.key) ? 'border-l-2' : 'opacity-50 border-l-2 border-transparent'}`}
            style={{ borderLeftColor: visibleMetrics.has(m.key) ? m.color : 'transparent' }}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-muted-silver">{m.label}</span>
              {visibleMetrics.has(m.key) ? <Eye size={10} className="text-muted-silver" /> : <EyeOff size={10} className="text-muted-silver/40" />}
            </div>
            <p className="text-lg font-bold text-ghost-white">{m.current}</p>
            <span className={`text-[10px] font-medium flex items-center gap-0.5 ${m.changeDir === 'up' ? 'text-neon-emerald' : 'text-coral-flame'}`}>
              {m.changeDir === 'up' ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
              {m.change}
            </span>
          </motion.button>
        ))}
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center">
        <span className="text-xs text-muted-silver">Display:</span>
        <button onClick={() => setShowMa(!showMa)} className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg transition-colors ${showMa ? 'bg-electric-cyan/10 text-electric-cyan' : 'text-muted-silver bg-steel-slate/10'}`}>
          <Activity size={10} /> Moving Average
        </button>
        <button onClick={() => setShowForecast(!showForecast)} className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg transition-colors ${showForecast ? 'bg-violet-pulse/10 text-violet-pulse' : 'text-muted-silver bg-steel-slate/10'}`}>
          <TrendingUp size={10} /> Forecast
        </button>
        <button onClick={() => setShowAnomalies(!showAnomalies)} className={`flex items-center gap-1 text-[10px] px-2 py-1 rounded-lg transition-colors ${showAnomalies ? 'bg-amber-glow/10 text-amber-glow' : 'text-muted-silver bg-steel-slate/10'}`}>
          <AlertTriangle size={10} /> Anomalies
        </button>
      </div>

      {/* Individual Trend Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {metricDefs.filter((m) => visibleMetrics.has(m.key)).map((metric) => (
          <Card key={metric.key} variant="glass">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ background: metric.color }} />
                {metric.label}
              </CardTitle>
            </CardHeader>
            <div className="px-4 pb-4 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id={`grad-${metric.key}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={metric.color} stopOpacity={0.2} />
                      <stop offset="95%" stopColor={metric.color} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip {...glassTooltip} />

                  {/* Forecast zone */}
                  {showForecast && <ReferenceArea x1="Jan" x2="Feb" fill={metric.color} fillOpacity={0.04} />}

                  {/* Anomaly marker */}
                  {showAnomalies && <ReferenceLine x="Oct" stroke="#FFB224" strokeDasharray="3 3" strokeWidth={1} />}

                  {/* Main line */}
                  <Area
                    type="monotone"
                    dataKey={metric.key}
                    stroke={metric.color}
                    fill={`url(#grad-${metric.key})`}
                    strokeWidth={2}
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      if (showAnomalies && payload.isAnomaly) {
                        return <circle key={`anom-${cx}`} cx={cx} cy={cy} r={5} fill="#FFB224" stroke="#FFB224" strokeWidth={2} fillOpacity={0.4} />;
                      }
                      if (showForecast && payload.isForecast) {
                        return <circle key={`fc-${cx}`} cx={cx} cy={cy} r={3} fill={metric.color} stroke={metric.color} strokeWidth={1} strokeDasharray="2 2" fillOpacity={0.5} />;
                      }
                      return <circle key={`dot-${cx}`} cx={cx} cy={cy} r={2.5} fill={metric.color} />;
                    }}
                  />

                  {/* Moving average line */}
                  {showMa && metric.maKey && (
                    <Line
                      type="monotone"
                      dataKey={metric.maKey}
                      stroke={metric.color}
                      strokeWidth={1.5}
                      strokeDasharray="5 3"
                      dot={false}
                      connectNulls
                    />
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        ))}
      </div>

      {/* Correlation Matrix */}
      <Card variant="glass">
        <CardHeader><CardTitle className="text-sm">Metric Correlations</CardTitle></CardHeader>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {correlations.map((c) => (
            <div key={c.pair} className="flex items-center gap-3 p-2.5 rounded-lg bg-steel-slate/8">
              <div className="flex-1">
                <span className="text-xs text-ghost-white block">{c.pair}</span>
                <span className="text-[10px] text-muted-silver">{c.strength}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 h-2 bg-steel-slate/15 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${c.r * 100}%` }}
                    transition={{ duration: 0.5 }}
                    className={`h-full rounded-full ${c.r >= 0.8 ? 'bg-neon-emerald' : c.r >= 0.6 ? 'bg-electric-cyan' : 'bg-amber-glow'}`}
                  />
                </div>
                <span className="text-xs font-mono font-semibold text-ghost-white w-8 text-right">{c.r.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Tender Pricing Intelligence CTA */}
      <Card variant="glass">
        <div className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-violet-pulse/10">
              <AlertTriangle size={18} className="text-violet-pulse" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-ghost-white">Tender Pricing Intelligence</h3>
              <p className="text-xs text-muted-silver max-w-lg">
                Auto-fill RFPs from your OEM catalog, compare historical tender pricing, and get AI-powered win probability estimates. <span className="text-amber-glow font-medium">Example: if historically a tender cost ₹25L and now is ₹21L, the system flags the risk automatically.</span>
              </p>
            </div>
          </div>
          <Link to="/analytics/tender-pricing">
            <Button variant="primary" leftIcon={<TrendingUp size={14} />}>
              Open Pricing Intel
            </Button>
          </Link>
        </div>
      </Card>
    </motion.div>
  );
}
