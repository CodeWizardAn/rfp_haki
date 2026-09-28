import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Clock,
  Target,
  BarChart3,
  Trophy,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Activity,
  DollarSign,
  Zap,
} from 'lucide-react';
import { KPICard } from '@/components/analytics/KPICard';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { useAuthStore } from '@/stores';
import { useDashboardStats, useWinLossPrediction } from '@/hooks/useApi';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from 'recharts';

// Static metrics (mirroring the Business Metrics Dashboard screenshot)

const kpiCards = [
  {
    title: 'Processing Time p95',
    value: '5.2 hrs',
    change: -5,
    changeLabel: 'vs last month',
    icon: <Clock size={18} />,
    glowColor: 'cyan' as const,
  },
  {
    title: 'Top-1 Match Accuracy',
    value: '87.2%',
    change: 7,
    changeLabel: 'vs last month',
    icon: <Target size={18} />,
    glowColor: 'emerald' as const,
  },
  {
    title: 'Mean Reciprocal Rank',
    value: '0.93',
    change: 10,
    changeLabel: 'vs last month',
    icon: <BarChart3 size={18} />,
    glowColor: 'amber' as const,
  },
  {
    title: 'Win Rate %',
    value: '77.1%',
    change: 8,
    changeLabel: 'vs last month',
    icon: <Trophy size={18} />,
    glowColor: 'violet' as const,
  },
];

const roiItems = [
  { icon: <CheckCircle2 size={16} className="text-neon-emerald" />, label: 'Manual Cost per RFP', value: '₹41,000', sub: '8 hours × ₹5,000/hr + overhead' },
  { icon: <Zap size={16} className="text-electric-cyan" />, label: 'System Cost per RFP', value: '~₹12,000', sub: 'compute + LLM API used' },
  { icon: <DollarSign size={16} className="text-neon-emerald" />, label: 'Savings per RFP', value: '₹29,000', highlight: true },
];


const alertRows = [
  { resource: 'CPU Usage', warning: '70%', critical: '90%', icon: <Cpu size={14} /> },
  { resource: 'Memory', warning: '75%', critical: '90%', icon: <Activity size={14} /> },
  { resource: 'API Error Rate', warning: 'z-score anomaly', critical: 'Z-score > 3 sigma', icon: <AlertTriangle size={14} /> },
  { resource: 'Response Time', warning: '> 1,000 ms', critical: '> 3,000 ms', icon: <Clock size={14} /> },
];

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.07 } } };
const fadeUp = { hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0, transition: { duration: 0.35 } } };

// Win probability gradient bar segments
const winProbSegments = [
  { label: '0-25', color: '#FF4757' },
  { label: '25-50', color: '#FFB224' },
  { label: '50-75', color: '#00D4FF' },
  { label: '75-100', color: '#00E68A' },
];

export default function UserDashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { data: dashboardStats } = useDashboardStats();
  const { data: winLossPrediction } = useWinLossPrediction();
  const winProb = Math.round(
    (
      winLossPrediction?.target_bid?.predicted_win_probability
      ?? winLossPrediction?.portfolio_forecast?.average_win_probability
      ?? 0.81
    ) * 100,
  );

  // Deterministic automation savings (could be wired to real api later)
  const lastMonthSavings = (dashboardStats as any)?.last_month_savings ?? 30000;
  const thisMonthSavings = (dashboardStats as any)?.this_month_savings ?? 310000;
  const savingsData = [
    { month: 'Last Month', value: lastMonthSavings, fill: '#5B21B6' },
    { month: 'This Month', value: thisMonthSavings, fill: '#7C3AED' },
  ];
  const pctGain = lastMonthSavings > 0
    ? Math.round(((thisMonthSavings - lastMonthSavings) / lastMonthSavings) * 100)
    : 250;

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">

      {/* Page title */}
      <motion.div variants={fadeUp} className="gradient-hero rounded-2xl p-6 border border-steel-slate/20 relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-h1 text-ghost-white flex items-center gap-3">
              <BarChart3 size={28} className="text-violet-pulse" />
              <span>Business Metrics <span className="text-gradient-cyan">Dashboard</span></span>
            </h1>
            <p className="text-body-lg text-muted-silver mt-1">
              Welcome back, <span className="text-electric-cyan font-medium">{user?.full_name || 'User'}</span>
              {' | '}
              {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>
          <Badge variant="soft" color="emerald" size="md">System Operational</Badge>
        </div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-violet-pulse/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
      </motion.div>

      {/* KPI row */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((k) => (
          <KPICard
            key={k.title}
            title={k.title}
            value={k.value}
            change={k.change}
            changeLabel={k.changeLabel}
            icon={k.icon}
            glowColor={k.glowColor}
            onClick={() => navigate('/user/rfps')}
          />
        ))}
      </motion.div>

      {/* Middle row: ROI card + Predictive Analytics + Automation Savings */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Example ROI */}
        <Card variant="glass" className="flex flex-col gap-4">
          <CardHeader>
            <CardTitle>Example ROI</CardTitle>
          </CardHeader>

          {/* Savings headline */}
          <div className="flex items-start gap-3 p-4 rounded-xl bg-neon-emerald/8 border border-neon-emerald/20">
            <TrendingUp size={22} className="text-neon-emerald mt-0.5 shrink-0" />
            <div>
              <p className="text-2xl font-bold text-ghost-white">
                Savings per RFP <span className="text-neon-emerald">₹29,000</span>
              </p>
              <p className="text-sm text-muted-silver mt-0.5">Capacity: <span className="text-electric-cyan font-medium">4× RFPs</span></p>
              <p className="text-sm text-muted-silver">3–5× revenue potential</p>
            </div>
          </div>

          {/* ROI breakdown */}
          <div className="space-y-3">
            {roiItems.map((item) => (
              <div
                key={item.label}
                className={`flex items-center justify-between p-3 rounded-xl ${item.highlight ? 'bg-neon-emerald/10 border border-neon-emerald/25' : 'bg-steel-slate/15'}`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="shrink-0">{item.icon}</span>
                  <div className="min-w-0">
                    <p className={`text-sm font-medium ${item.highlight ? 'text-neon-emerald' : 'text-ghost-white'}`}>{item.label}</p>
                    {item.sub && <p className="text-xs text-muted-silver truncate">{item.sub}</p>}
                  </div>
                </div>
                <span className={`text-base font-bold shrink-0 ml-4 ${item.highlight ? 'text-neon-emerald text-lg' : 'text-ghost-white'}`}>{item.value}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Right column: Predictive Analytics + Automation Savings */}
        <div className="flex flex-col gap-6">

          {/* Predictive Analytics */}
          <Card variant="glass" className="flex-1">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Predictive Analytics</CardTitle>
                <Badge variant="soft" color="violet">Live</Badge>
              </div>
            </CardHeader>

            {/* Win Probability */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-silver">Win Prob</span>
                <span className="text-2xl font-bold text-neon-emerald">{winProb}%</span>
              </div>
              {/* Gradient bar */}
              <div className="relative h-4 rounded-full overflow-hidden flex">
                {winProbSegments.map((seg) => (
                  <div key={seg.label} className="flex-1 h-full" style={{ background: seg.color, opacity: 0.85 }} />
                ))}
                {/* Thumb */}
                <div
                  className="absolute top-0 h-full w-1 bg-white rounded-full shadow-lg"
                  style={{ left: `${winProb}%`, transform: 'translateX(-50%)' }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-muted-silver">
                {winProbSegments.map((seg) => (
                  <span key={seg.label}>{seg.label}</span>
                ))}
              </div>
              {/* Check badge */}
              <div className="flex justify-end">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-neon-emerald/15 text-neon-emerald text-xs font-medium">
                  <CheckCircle2 size={12} /> {winProb}% WIN
                </span>
              </div>
            </div>

            {/* Estimated time */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-steel-slate/20">
              <div className="flex items-center gap-2">
                <Clock size={16} className="text-electric-cyan" />
                <span className="text-sm text-ghost-white">Estimated</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold text-ghost-white">6 hours</span>
                <div className="flex items-end gap-0.5 h-6">
                  {[3, 5, 4, 7, 5, 6, 8].map((h, i) => (
                    <div key={i} className="w-2 rounded-sm bg-amber-glow/70" style={{ height: `${h * 3}px` }} />
                  ))}
                </div>
              </div>
            </div>
            <p className="text-[11px] text-muted-silver mt-2 text-right">Based on requirements count</p>
          </Card>

          {/* Automation Savings */}
          <Card variant="glass">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Automation Savings</CardTitle>
                <Badge variant="soft" color="emerald">+{pctGain}%</Badge>
              </div>
            </CardHeader>
            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={savingsData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false}
                  tickFormatter={(v: number) => v >= 1000 ? `${v / 1000}k` : String(v)} />
                <Tooltip
                  contentStyle={{ background: '#0D1117', border: '1px solid #1E2642', borderRadius: 8, color: '#CDD6F4' }}
                  formatter={(v: any) => [`Rs ${Number(v || 0).toLocaleString('en-IN')}`, 'Savings']}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {savingsData.map((_, index) => (
                    <Cell key={index} fill={index === 1 ? '#7C3AED' : '#4C1D95'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-[11px] text-muted-silver mt-1">Naive Bayes + Linear Regression models</p>
          </Card>

        </div>
      </motion.div>

      {/* Alert Thresholds */}
      <motion.div variants={fadeUp}>
        <Card variant="glass">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle size={18} className="text-amber-glow" />
                Alert Thresholds
              </CardTitle>
              <Badge variant="soft" color="amber">Auto-Monitored</Badge>
            </div>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-steel-slate/30">
                  <th className="text-left py-2.5 pr-4 text-muted-silver font-medium">Resource</th>
                  <th className="text-center py-2.5 px-4 text-amber-glow font-medium">Warning</th>
                  <th className="text-center py-2.5 px-4 text-coral-flame font-medium">Critical</th>
                  <th className="text-center py-2.5 pl-4 text-coral-flame font-medium">!</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-steel-slate/20">
                {alertRows.map((row) => (
                  <tr key={row.resource} className="hover:bg-steel-slate/10 transition-colors">
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2 text-ghost-white">
                        <span className="text-muted-silver">{row.icon}</span>
                        {row.resource}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-block px-2.5 py-0.5 rounded-full bg-amber-glow/10 text-amber-glow text-xs font-medium">
                        {row.warning}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-block px-2.5 py-0.5 rounded-full bg-coral-flame/10 text-coral-flame text-xs font-medium">
                        {row.critical}
                      </span>
                    </td>
                    <td className="py-3 pl-4 text-center">
                      <AlertTriangle size={16} className="text-coral-flame inline-block" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </motion.div>

    </motion.div>
  );
}
