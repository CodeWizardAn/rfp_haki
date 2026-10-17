import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FileText,
  Banknote,
  Package,
  Building2,
  Activity,
  Upload,
  Plus,
  Play,
  Bot,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { KPICard } from '@/components/analytics/KPICard';
import { MetalMarketPrices } from '@/components/analytics/MetalMarketPrices';
import { TrendChart } from '@/components/charts/TrendChart';
import { DonutChart } from '@/components/charts/DonutChart';
import { BarChart } from '@/components/charts/BarChart';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { useAuthStore } from '@/stores';
import { formatCompactCurrency } from '@/utils/formatters';
import { useEventStream } from '@/hooks/useEventStream';
import { useDashboardStats, useSystemHealth } from '@/hooks/useApi';

// --- Mock data (fallback when backend is offline) ---

const mockRFPTrend = Array.from({ length: 30 }, (_, i) => ({
  date: `Jan ${i + 1}`,
  value: Math.floor(Math.random() * 15) + 5,
}));

const mockBidDonut = [
  { name: 'Draft', value: 8, color: '#8892B0' },
  { name: 'Submitted', value: 15, color: '#00D4FF' },
  { name: 'Approved', value: 12, color: '#00E68A' },
  { name: 'Rejected', value: 3, color: '#FF4757' },
  { name: 'Won', value: 7, color: '#FFB224' },
  { name: 'Lost', value: 4, color: '#1E2642' },
];

const mockRevenueData = [
  { month: 'Sep', submitted: 45, won: 32 },
  { month: 'Oct', submitted: 52, won: 38 },
  { month: 'Nov', submitted: 48, won: 41 },
  { month: 'Dec', submitted: 61, won: 45 },
  { month: 'Jan', submitted: 55, won: 48 },
  { month: 'Feb', submitted: 67, won: 52 },
];

const mockAgentActivity = [
  { id: 1, agent: 'master', action: 'Orchestrated full pipeline for RFP-2026-0142', time: '2m ago', color: '#7C3AED' },
  { id: 2, agent: 'sales', action: 'Generated pricing for 45 matched products', time: '5m ago', color: '#00D4FF' },
  { id: 3, agent: 'technical', action: 'Completed spec comparison for cables category', time: '12m ago', color: '#14B8A6' },
  { id: 4, agent: 'pricing', action: 'Optimized bid margins — saved ₹2.4L', time: '18m ago', color: '#FFB224' },
  { id: 5, agent: 'master', action: 'Started processing RFP-2026-0143', time: '25m ago', color: '#7C3AED' },
];

const mockAlerts = [
  { id: 1, type: 'warning', icon: <AlertTriangle size={14} />, message: 'RFP-0139 deadline in 24 hours', color: 'text-amber-glow' },
  { id: 2, type: 'error', icon: <AlertTriangle size={14} />, message: 'Pipeline stage "compliance" failed for RFP-0141', color: 'text-coral-flame' },
  { id: 3, type: 'success', icon: <CheckCircle2 size={14} />, message: 'Bid B-0087 approved by manager', color: 'text-neon-emerald' },
  { id: 4, type: 'info', icon: <Clock size={14} />, message: 'Vendor "Polycab" updated 12 product prices', color: 'text-electric-cyan' },
];

const systemOverview = [
  { name: 'Core API', status: 'healthy', latency: 120 },
  { name: 'PDF Extractor', status: 'healthy', latency: 210 },
  { name: 'Spec Compare', status: 'warning', latency: 340 },
  { name: 'Vendor Service', status: 'healthy', latency: 160 },
  { name: 'Bid Engine', status: 'healthy', latency: 180 },
];

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // ── Backend data (falls back to mock when API is unreachable) ──
  const { data: backendStats } = useDashboardStats();
  const { data: healthData } = useSystemHealth();

  const [kpis, setKpis] = useState({
    activeRfps: 24,
    totalBidValue: 4_85_00_000,
    productsMatched: 693,
    activeVendors: 156,
    pipelineHealth: 98.2,
  });

  // Sync KPIs from backend when available
  useEffect(() => {
    if (backendStats) {
      setKpis((prev) => ({
        ...prev,
        activeRfps: backendStats.active_rfps ?? prev.activeRfps,
        totalBidValue: backendStats.total_bid_value ?? prev.totalBidValue,
        productsMatched: backendStats.products_count ?? prev.productsMatched,
        activeVendors: backendStats.active_vendors ?? prev.activeVendors,
        pipelineHealth: (healthData as any)?.system_health_score ?? (healthData as any)?.score ?? prev.pipelineHealth,
      }));
    }
  }, [backendStats, healthData]);

  const [alerts, setAlerts] = useState(mockAlerts);
  const [agentActivity, setAgentActivity] = useState(mockAgentActivity);
  const [kpiFlash, setKpiFlash] = useState(false);
  const [showBelowFold, setShowBelowFold] = useState(false);
  const queueRef = useRef<any[]>([]);
  const flushRef = useRef<number | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setShowBelowFold(true), 200);
    return () => window.clearTimeout(timer);
  }, []);

  const processEvent = (data: any) => {
    switch (data?.type) {
      case 'kpi:update':
        setKpis((prev) => ({ ...prev, ...data.payload }));
        setKpiFlash(true);
        window.setTimeout(() => setKpiFlash(false), 400);
        break;
      case 'alert:new':
        setAlerts((prev) => [data.payload, ...prev].slice(0, 8));
        break;
      case 'agent:activity':
        setAgentActivity((prev) => [data.payload, ...prev].slice(0, 10));
        break;
      default:
        break;
    }
  };

  useEventStream({
    url: `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/events/stream`,
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data);
        queueRef.current.push(data);
        if (!flushRef.current) {
          flushRef.current = window.setTimeout(() => {
            const queue = [...queueRef.current];
            queueRef.current = [];
            flushRef.current = null;
            queue.forEach(processEvent);
          }, 500);
        }
      } catch {
        // ignore malformed SSE messages
      }
    },
  });

  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Welcome Banner */}
      <motion.div variants={fadeUp} className="gradient-hero rounded-2xl p-6 border border-steel-slate/20 relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-h1 text-ghost-white">
              Welcome back, <span className="text-gradient-cyan">{user?.full_name || 'Admin'}</span>
            </h1>
            <p className="text-body-lg text-muted-silver mt-1">
              {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              {' · '}
              <span className="text-neon-emerald">All Systems Operational</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="primary" leftIcon={<Upload size={16} />} onClick={() => navigate('/rfps/upload')}>
              Upload RFP
            </Button>
            <Button variant="secondary" leftIcon={<Plus size={16} />} onClick={() => navigate('/bids/create')}>
              Create Bid
            </Button>
            <Button variant="ghost" leftIcon={<Play size={16} />} onClick={() => navigate('/pipeline')}>
              Run Pipeline
            </Button>
          </div>
        </div>
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-violet-pulse/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
      </motion.div>

      {/* KPI Cards Row */}
      <motion.div
        variants={fadeUp}
        className={`flex gap-4 overflow-x-auto pb-2 sm:grid sm:grid-cols-2 lg:grid-cols-5 sm:overflow-visible ${
          kpiFlash ? 'animate-pulse' : ''
        }`}
      >
        <div className="min-w-[220px] sm:min-w-0">
          <KPICard
            title="Active RFPs"
            value={kpis.activeRfps}
            change={12.5}
            changeLabel="vs last week"
            icon={<FileText size={18} />}
            glowColor="cyan"
            onClick={() => navigate('/rfps')}
          />
        </div>
        <div className="min-w-[220px] sm:min-w-0">
          <KPICard
            title="Total Bid Value"
            value={formatCompactCurrency(kpis.totalBidValue)}
            change={8.3}
            changeLabel="this month"
            icon={<Banknote size={18} />}
            glowColor="amber"
            onClick={() => navigate('/bids')}
          />
        </div>
        <div className="min-w-[220px] sm:min-w-0">
          <KPICard
            title="Products Matched"
            value={kpis.productsMatched.toLocaleString('en-IN')}
            change={2.1}
            changeLabel="new matches"
            icon={<Package size={18} />}
            glowColor="emerald"
            onClick={() => navigate('/products')}
          />
        </div>
        <div className="min-w-[220px] sm:min-w-0">
          <KPICard
            title="Active Vendors"
            value={kpis.activeVendors}
            change={-1.4}
            changeLabel="vs last month"
            icon={<Building2 size={18} />}
            glowColor="violet"
            onClick={() => navigate('/vendors')}
          />
        </div>
        <div className="min-w-[220px] sm:min-w-0">
          <KPICard
            title="Pipeline Health"
            value={`${kpis.pipelineHealth.toFixed(1)}%`}
            change={0.5}
            changeLabel="uptime"
            icon={<Activity size={18} />}
            glowColor="emerald"
            onClick={() => navigate('/pipeline')}
          />
        </div>
      </motion.div>

      {/* Charts Row 1: RFP Timeline + Agent Activity */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TrendChart
            title="RFP Processing — Last 30 Days"
            data={mockRFPTrend}
            color="#00D4FF"
            height={280}
          />
        </div>

        {/* Agent Activity Feed */}
        <Card variant="glass">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Agent Activity</CardTitle>
              <Badge variant="pulse" color="violet">Live</Badge>
            </div>
          </CardHeader>
          <div className="space-y-3 max-h-[240px] overflow-y-auto pr-1">
            {agentActivity.map((item) => (
              <div key={item.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-steel-slate/20 transition-colors">
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                  style={{ backgroundColor: `${item.color}20` }}
                >
                  <Bot size={14} style={{ color: item.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-ghost-white leading-snug">{item.action}</p>
                  <p className="text-xs text-muted-silver mt-0.5">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => navigate('/agents')}
            className="w-full mt-3 pt-3 border-t border-steel-slate/20 text-sm text-electric-cyan hover:text-electric-cyan/80 flex items-center justify-center gap-1 transition-colors"
          >
            View All <ArrowRight size={14} />
          </button>
        </Card>
      </motion.div>

      {/* Charts Row 2: Bid Donut + Revenue Bar + Alerts */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <DonutChart
          title="Bid Status Breakdown"
          data={mockBidDonut}
          centerValue="49"
          centerLabel="Total Bids"
        />

        <BarChart
          title="Revenue — Submitted vs Won"
          data={mockRevenueData}
          bars={[
            { dataKey: 'submitted', color: 'rgba(0,212,255,0.4)', name: 'Submitted' },
            { dataKey: 'won', color: '#00E68A', name: 'Won' },
          ]}
          xDataKey="month"
        />

        {/* Alerts Panel */}
        <Card variant="glass">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Alerts</CardTitle>
              <Badge variant="soft" color="coral">{mockAlerts.length}</Badge>
            </div>
          </CardHeader>
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-start gap-3 p-3 rounded-lg bg-steel-slate/15 hover:bg-steel-slate/25 transition-colors cursor-pointer"
              >
                <span className={alert.color}>{alert.icon ?? <AlertTriangle size={14} />}</span>
                <p className="text-sm text-ghost-white leading-snug">{alert.message}</p>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>

      {showBelowFold && (
        <>
          {/* Raw Material & Metal Market Index */}
          <motion.div variants={fadeUp}>
            <MetalMarketPrices />
          </motion.div>

          {/* System Overview Mini Map */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle>System Overview</CardTitle>
              </CardHeader>
              <div className="space-y-3">
                {systemOverview.map((svc) => (
                  <div key={svc.name} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2.5 h-2.5 rounded-full ${
                          svc.status === 'healthy'
                            ? 'bg-neon-emerald'
                            : svc.status === 'warning'
                              ? 'bg-amber-glow'
                              : 'bg-coral-flame'
                        }`}
                      />
                      <span className="text-sm text-ghost-white">{svc.name}</span>
                    </div>
                    <span className="text-xs text-muted-silver">{svc.latency} ms</span>
                  </div>
                ))}
                <div className="mt-3 h-1.5 rounded-full bg-steel-slate/30 overflow-hidden">
                  <div className="h-full gradient-pipeline" style={{ width: '78%' }} />
                </div>
                <p className="text-xs text-muted-silver">Data flow health across services</p>
              </div>
            </Card>
          </motion.div>

          {/* Recent Activity */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <div className="space-y-1 max-h-[280px] overflow-y-auto pr-1">
                {[
                  { text: 'RFP-2026-0143 uploaded by Admin', time: '2 min ago', icon: <Upload size={14} className="text-electric-cyan" /> },
                  { text: 'Bid B-0087 approved — ₹12.4L', time: '18 min ago', icon: <CheckCircle2 size={14} className="text-neon-emerald" /> },
                  { text: 'Vendor "Polycab" rated 4.5★ on delivery', time: '1 hour ago', icon: <Building2 size={14} className="text-teal-depth" /> },
                  { text: '228 products matched for RFP-0142', time: '2 hours ago', icon: <Package size={14} className="text-violet-pulse" /> },
                  { text: 'Pipeline completed for RFP-2026-0140', time: '3 hours ago', icon: <Activity size={14} className="text-neon-emerald" /> },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-steel-slate/15 transition-colors">
                    <span className="w-7 h-7 rounded-full bg-steel-slate/30 flex items-center justify-center flex-shrink-0">
                      {item.icon}
                    </span>
                    <p className="text-sm text-ghost-white flex-1">{item.text}</p>
                    <span className="text-xs text-muted-silver whitespace-nowrap">{item.time}</span>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        </>
      )}
    </motion.div>
  );
}
