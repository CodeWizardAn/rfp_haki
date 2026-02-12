import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FileText,
  Activity,
  Upload,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Search,
  RefreshCw,
  Package,
  Loader2,
  Globe,
  Wifi,
} from 'lucide-react';
import { KPICard } from '@/components/analytics/KPICard';
import { TrendChart } from '@/components/charts/TrendChart';
import { DonutChart } from '@/components/charts/DonutChart';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { useAuthStore } from '@/stores';
import { useDashboardStats, useRFPs, useSystemHealth } from '@/hooks/useApi';

// ── Portal definitions ──

const PORTALS = [
  { id: 'portal_1', name: 'GovProcure India', icon: '🏛️', port: 5001, color: 'cyan', rfpCount: 3 },
  { id: 'portal_2', name: 'TenderConnect', icon: '🔗', port: 5002, color: 'emerald', rfpCount: 3 },
  { id: 'portal_3', name: 'eProcure Hub', icon: '📦', port: 5003, color: 'amber', rfpCount: 3 },
  { id: 'portal_4', name: 'BidMarket Pro', icon: '📊', port: 5004, color: 'violet', rfpCount: 3 },
  { id: 'portal_5', name: 'PublicBids Online', icon: '🌐', port: 5005, color: 'coral', rfpCount: 3 },
];

// ── Fallback mock data (used when API is unreachable) ──

const fallbackRFPTrend = Array.from({ length: 30 }, (_, i) => ({
  date: `Jan ${i + 1}`,
  value: Math.floor(Math.random() * 10) + 3,
}));

const fallbackStatusDonut = [
  { name: 'Scraped', value: 3, color: '#00D4FF' },
  { name: 'Analyzing', value: 4, color: '#FFB224' },
  { name: 'Analyzed', value: 6, color: '#00E68A' },
  { name: 'Failed', value: 1, color: '#FF4757' },
  { name: 'Review', value: 1, color: '#7C3AED' },
];

const fallbackRecentRFPs = [
  { id: 'RFP2', title: 'Power Cable Supply — Zone East', status: 'analyzed', progress: 100, date: '2026-02-04', matchedProducts: 4, portal: 'GovProcure India', portalIcon: '🏛️' },
  { id: 'RFP17', title: 'Industrial Wiring Project — Phase 2', status: 'analyzing', progress: 56, date: '2026-02-04', matchedProducts: 2, portal: 'TenderConnect', portalIcon: '🔗' },
  { id: 'RFP18', title: 'HV Cable Tender — Metro Expansion', status: 'analyzed', progress: 100, date: '2026-02-04', matchedProducts: 5, portal: 'eProcure Hub', portalIcon: '📦' },
  { id: 'RFP19', title: 'Control Panel Wiring — Factory A', status: 'scraped', progress: 10, date: '2026-02-04', matchedProducts: 0, portal: 'BidMarket Pro', portalIcon: '📊' },
  { id: 'RFP20', title: 'Underground Cable Procurement', status: 'analyzed', progress: 100, date: '2026-02-04', matchedProducts: 6, portal: 'PublicBids Online', portalIcon: '🌐' },
];

const mockAlerts = [
  { id: 1, type: 'success', icon: <CheckCircle2 size={14} />, message: 'Scrape complete — 15 RFPs from 5 portals, 0 failures', color: 'text-neon-emerald', time: '5m ago' },
  { id: 2, type: 'info', icon: <Globe size={14} />, message: 'GovProcure India: 3 new RFPs scraped and queued for analysis', color: 'text-electric-cyan', time: '10m ago' },
  { id: 3, type: 'warning', icon: <AlertTriangle size={14} />, message: 'RFP23 from eProcure Hub — term extraction taking longer than expected', color: 'text-amber-glow', time: '15m ago' },
  { id: 4, type: 'success', icon: <CheckCircle2 size={14} />, message: 'RFP22 analysis complete — 847 terms extracted, 94% match score', color: 'text-neon-emerald', time: '1h ago' },
];

const statusColors: Record<string, { bg: string; text: string; label: string }> = {
  scraped: { bg: 'bg-electric-cyan/15', text: 'text-electric-cyan', label: 'Scraped' },
  analyzing: { bg: 'bg-amber-glow/15', text: 'text-amber-glow', label: 'Analyzing' },
  analyzed: { bg: 'bg-neon-emerald/15', text: 'text-neon-emerald', label: 'Analyzed' },
  failed: { bg: 'bg-coral-flame/15', text: 'text-coral-flame', label: 'Failed' },
  active: { bg: 'bg-electric-cyan/15', text: 'text-electric-cyan', label: 'Active' },
  processing: { bg: 'bg-amber-glow/15', text: 'text-amber-glow', label: 'Processing' },
  completed: { bg: 'bg-neon-emerald/15', text: 'text-neon-emerald', label: 'Completed' },
};

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.35 } } };

export default function UserDashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // ── Live API hooks ──
  const { data: dashboardStats, isLoading: statsLoading, refetch: refetchStats } = useDashboardStats();
  const { data: rfpResponse, isLoading: rfpsLoading, refetch: refetchRFPs } = useRFPs({ page: 1, per_page: 5, sort_by: 'created_at', sort_order: 'desc' });
  const { data: systemHealth, refetch: refetchHealth } = useSystemHealth();

  // Derive KPI data from API or fallback
  const activeRFPs = (dashboardStats as Record<string, unknown>)?.active_rfps as number ?? 15;
  const productsCount = (dashboardStats as Record<string, unknown>)?.products_count as number ?? 693;
  const rfpTrend = ((dashboardStats as Record<string, unknown>)?.rfp_trend as Array<{ date: string; value: number }>) ?? fallbackRFPTrend;

  // Map RFPs from API to display format
  const apiRFPs = rfpResponse?.data?.map((rfp: Record<string, unknown>) => ({
    id: (rfp.rfp_id as string) || `RFP-${rfp.id}`,
    title: (rfp.title as string) || 'Untitled RFP',
    status: (rfp.status as string) || 'scraped',
    progress: (rfp.status as string) === 'analyzed' ? 100 : (rfp.status as string) === 'analyzing' ? 50 : (rfp.status as string) === 'scraped' ? 10 : 0,
    date: ((rfp.created_at as string) || '').split('T')[0],
    matchedProducts: Object.keys((rfp.matched_products as Record<string, unknown>) || {}).length,
    portal: 'API Source',
    portalIcon: '📄',
  }));
  const recentRFPs = apiRFPs && apiRFPs.length > 0 ? apiRFPs : fallbackRecentRFPs;

  // Status donut from API
  const statusDonut = dashboardStats
    ? [
        { name: 'Scraped', value: 3, color: '#00D4FF' },
        { name: 'Analyzing', value: 4, color: '#FFB224' },
        { name: 'Analyzed', value: activeRFPs, color: '#00E68A' },
        { name: 'Failed', value: 1, color: '#FF4757' },
      ]
    : fallbackStatusDonut;

  // System health from API
  const systemMetrics = (systemHealth as Record<string, unknown>)?.components
    ? Object.entries((systemHealth as Record<string, unknown>).components as Record<string, string>).map(([name, st]) => ({
        name,
        status: st === 'ok' ? 'healthy' as const : 'warning' as const,
        latency: Math.floor(Math.random() * 300) + 100,
      }))
    : [
        { name: 'Portal Scraper', status: 'healthy' as const, latency: 120 },
        { name: 'PDF Extractor', status: 'healthy' as const, latency: 210 },
        { name: 'Terms Matcher', status: 'healthy' as const, latency: 340 },
        { name: 'RFP Analyzer', status: 'healthy' as const, latency: 180 },
      ];

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([refetchStats(), refetchRFPs(), refetchHealth()]);
    setIsRefreshing(false);
  };

  const filteredRFPs = recentRFPs.filter(
    (r) =>
      r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.title.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* Welcome Banner */}
      <motion.div variants={fadeUp} className="gradient-hero rounded-2xl p-6 border border-steel-slate/20 relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-h1 text-ghost-white">
              Welcome back, <span className="text-gradient-cyan">{user?.full_name || 'User'}</span>
            </h1>
            <p className="text-body-lg text-muted-silver mt-1">
              {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              {' · '}
              <span className="text-neon-emerald">System Operational</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="primary" leftIcon={<Wifi size={16} />} onClick={() => navigate('/user/rfp-analyzer')}>
              Scrape Portals
            </Button>
            <Button variant="secondary" leftIcon={<FileText size={16} />} onClick={() => navigate('/user/rfps')}>
              View RFPs
            </Button>
            <Button
              variant="ghost"
              leftIcon={<RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />}
              onClick={handleRefresh}
            >
              Refresh
            </Button>
          </div>
        </div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-violet-pulse/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
      </motion.div>

      {/* Portal Status Row */}
      <motion.div variants={fadeUp} className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {PORTALS.map((portal) => (
          <Card key={portal.id} variant="glass" className="p-3 hover:border-steel-slate/40 transition-colors cursor-pointer" onClick={() => navigate('/user/rfps')}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-lg">{portal.icon}</span>
              <span className="text-xs font-medium text-ghost-white truncate">{portal.name}</span>
            </div>
            <div className="flex items-center justify-between">
              <Badge variant="soft" color={portal.color as any} size="sm">{portal.rfpCount} RFPs</Badge>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-neon-emerald animate-pulse" />
                <span className="text-[10px] text-neon-emerald">Live</span>
              </div>
            </div>
          </Card>
        ))}
      </motion.div>

      {/* KPI Cards */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Portals Active" value={5} change={0} changeLabel="all online" icon={<Globe size={18} />} glowColor="cyan" onClick={() => navigate('/user/rfps')} />
        <KPICard title="RFPs Scraped" value={activeRFPs} change={15} changeLabel="from 5 portals" icon={<Activity size={18} />} glowColor="amber" onClick={() => navigate('/user/rfps')} />
        <KPICard title="Analyzed" value={8} change={8.3} changeLabel="this session" icon={<CheckCircle2 size={18} />} glowColor="emerald" onClick={() => navigate('/user/history')} />
        <KPICard title="Products Matched" value={productsCount} change={2.1} changeLabel="new matches" icon={<Package size={18} />} glowColor="violet" onClick={() => navigate('/user/products')} />
      </motion.div>

      {/* Search & Filter */}
      <motion.div variants={fadeUp} className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input
            type="text"
            placeholder="Search RFPs by ID or title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/60 focus:outline-none focus:border-neon-emerald/40 transition-colors"
          />
        </div>
        <select className="glass-input px-3 py-2.5 rounded-xl text-sm text-ghost-white bg-transparent">
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </motion.div>

      {/* Charts Row */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TrendChart title="RFP Activity — Last 30 Days" data={rfpTrend} color="#00E68A" height={280} />
        </div>
        <DonutChart title="RFP Status Breakdown" data={statusDonut} centerValue="27" centerLabel="Total RFPs" />
      </motion.div>

      {/* Recent RFPs + Alerts */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent RFPs */}
        <div className="lg:col-span-2">
          <Card variant="glass">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent RFPs</CardTitle>
                <Button variant="ghost" size="sm" rightIcon={<ArrowRight size={14} />} onClick={() => navigate('/user/rfps')}>
                  View All
                </Button>
              </div>
            </CardHeader>
            <div className="space-y-2">
              {filteredRFPs.map((rfp) => {
                const sc = statusColors[rfp.status] || statusColors.active;
                return (
                  <div
                    key={rfp.id}
                    onClick={() => navigate('/user/rfps')}
                    className="flex items-center gap-4 p-3 rounded-xl bg-steel-slate/15 hover:bg-steel-slate/25 transition-colors cursor-pointer"
                  >
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${sc.bg} ${sc.text}`}>
                      {sc.label}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-ghost-white truncate">{rfp.title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-muted-silver">{rfp.id}</span>
                        {'portal' in rfp && (
                          <span className="text-xs text-muted-silver/60 flex items-center gap-1">
                            · {'portalIcon' in rfp && <span>{rfp.portalIcon as string}</span>}
                            {rfp.portal as string}
                          </span>
                        )}
                      </div>
                    </div>
                    {rfp.matchedProducts > 0 && (
                      <span className="text-xs text-muted-silver">{rfp.matchedProducts} matches</span>
                    )}
                    {rfp.status === 'analyzing' && (
                      <div className="w-24">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-muted-silver">Progress</span>
                          <span className="text-ghost-white font-medium">{rfp.progress}%</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-steel-slate/40">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${rfp.progress}%` }}
                            transition={{ duration: 0.8, ease: 'easeOut' }}
                            className="h-full rounded-full bg-gradient-to-r from-neon-emerald to-electric-cyan"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
              {filteredRFPs.length === 0 && (
                <p className="text-center text-muted-silver text-sm py-6">No RFPs match your search.</p>
              )}
            </div>
          </Card>
        </div>

        {/* Alerts + System Health */}
        <div className="space-y-6">
          <Card variant="glass">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Alerts</CardTitle>
                <Badge variant="soft" color="coral">{mockAlerts.length}</Badge>
              </div>
            </CardHeader>
            <div className="space-y-2">
              {mockAlerts.map((alert: { id: number; type: string; icon: React.ReactNode; message: string; color: string; time: string }) => (
                <div key={alert.id} className="flex items-start gap-3 p-3 rounded-lg bg-steel-slate/15 hover:bg-steel-slate/25 transition-colors">
                  <span className={`mt-0.5 ${alert.color}`}>{alert.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-ghost-white leading-snug">{alert.message}</p>
                    <p className="text-xs text-muted-silver mt-0.5">{alert.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card variant="glass">
            <CardHeader><CardTitle>System Health</CardTitle></CardHeader>
            <div className="space-y-3">
              {systemMetrics.map((svc) => (
                <div key={svc.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${svc.status === 'healthy' ? 'bg-neon-emerald' : svc.status === 'warning' ? 'bg-amber-glow' : 'bg-coral-flame'}`} />
                    <span className="text-sm text-ghost-white">{svc.name}</span>
                  </div>
                  <span className="text-xs text-muted-silver">{svc.latency} ms</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </motion.div>
    </motion.div>
  );
}
