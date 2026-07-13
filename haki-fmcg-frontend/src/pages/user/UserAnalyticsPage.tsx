import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle2,
  FileText,
  Package,
  Zap,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { KPICard } from '@/components/analytics/KPICard';
import { TrendChart } from '@/components/charts/TrendChart';
import { DonutChart } from '@/components/charts/DonutChart';
import { BarChart } from '@/components/charts/BarChart';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { useDashboardStats, useRFPAnalytics, usePerformanceMetrics } from '@/hooks/useApi';

// ── Fallback data ──

const fallbackProcessingTrend = Array.from({ length: 30 }, (_, i) => ({
  date: `Jan ${i + 1}`,
  value: Math.floor(Math.random() * 8) + 2,
}));

const fallbackCompletionDonut = [
  { name: 'Completed', value: 18, color: '#00E68A' },
  { name: 'In Progress', value: 3, color: '#FFB224' },
  { name: 'Pending', value: 5, color: '#00D4FF' },
  { name: 'Failed', value: 1, color: '#FF4757' },
];

const fallbackMonthlyBar = [
  { month: 'Sep', processed: 12, matched: 580 },
  { month: 'Oct', processed: 15, matched: 720 },
  { month: 'Nov', processed: 18, matched: 890 },
  { month: 'Dec', processed: 22, matched: 1050 },
  { month: 'Jan', processed: 20, matched: 980 },
  { month: 'Feb', processed: 27, matched: 1240 },
];

const fallbackProcessingTimes = [
  { stage: 'PDF Extraction', time: '12s', trend: -8, status: 'improving' as const },
  { stage: 'Product Matching', time: '45s', trend: -15, status: 'improving' as const },
  { stage: 'Spec Comparison', time: '28s', trend: 5, status: 'degraded' as const },
  { stage: 'Score Calculation', time: '8s', trend: -2, status: 'improving' as const },
  { stage: 'Report Generation', time: '15s', trend: 0, status: 'stable' as const },
];

const fallbackCategoryBreakdown = [
  { category: 'Cables & Wires', rfps: 8, matches: 456, avgConfidence: 91 },
  { category: 'Electrical', rfps: 6, matches: 312, avgConfidence: 87 },
  { category: 'Safety Equipment', rfps: 4, matches: 189, avgConfidence: 93 },
  { category: 'FMCG', rfps: 3, matches: 520, avgConfidence: 95 },
  { category: 'Industrial', rfps: 3, matches: 145, avgConfidence: 82 },
  { category: 'Office Supplies', rfps: 3, matches: 280, avgConfidence: 89 },
];

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.35 } } };

export default function UserAnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  // ── API ──
  const { data: dashStats } = useDashboardStats();
  const { data: rfpAnalytics } = useRFPAnalytics(timeRange);
  const { data: perfMetrics } = usePerformanceMetrics();

  const stats = useMemo(() => {
    const s = (dashStats as Record<string, any> | undefined)?.data ?? (dashStats as Record<string, any> | undefined);
    return {
      rfpsProcessed: s?.total_rfps ?? s?.rfps_processed ?? 27,
      rfpsProcessedChange: s?.rfp_change ?? 12.5,
      completionRate: s?.completion_rate ?? '94.2%',
      completionRateChange: s?.completion_rate_change ?? 3.1,
      avgProcessingTime: s?.avg_processing_time ?? '1m 48s',
      avgProcessingTimeChange: s?.processing_time_change ?? -18.5,
      productsMatched: s?.total_products_matched ?? s?.products_matched ?? '1,902',
      productsMatchedChange: s?.products_matched_change ?? 8.7,
    };
  }, [dashStats]);

  const rfpAnalyticsRaw = rfpAnalytics as Record<string, any> | undefined;
  const perfMetricsRaw = perfMetrics as Record<string, any> | undefined;

  const rfpProcessingTrend = useMemo(() => {
    const trend = rfpAnalyticsRaw?.data?.trend ?? rfpAnalyticsRaw?.trend;
    if (Array.isArray(trend) && trend.length > 0) return trend;
    return fallbackProcessingTrend;
  }, [rfpAnalytics]);

  const completionRateDonut = useMemo(() => {
    const completion = rfpAnalyticsRaw?.data?.completion ?? rfpAnalyticsRaw?.completion;
    if (Array.isArray(completion) && completion.length > 0) return completion;
    return fallbackCompletionDonut;
  }, [rfpAnalytics]);

  const monthlyBarData = useMemo(() => {
    const monthly = rfpAnalyticsRaw?.data?.monthly ?? rfpAnalyticsRaw?.monthly;
    if (Array.isArray(monthly) && monthly.length > 0) return monthly;
    return fallbackMonthlyBar;
  }, [rfpAnalytics]);

  const avgProcessingTimes = useMemo(() => {
    const times = perfMetricsRaw?.data?.processing_times ?? perfMetricsRaw?.processing_times;
    if (Array.isArray(times) && times.length > 0) return times;
    return fallbackProcessingTimes;
  }, [perfMetrics]);

  const categoryBreakdown = useMemo(() => {
    const cats = rfpAnalyticsRaw?.data?.categories ?? rfpAnalyticsRaw?.categories;
    if (Array.isArray(cats) && cats.length > 0) return cats;
    return fallbackCategoryBreakdown;
  }, [rfpAnalytics]);

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <motion.div variants={fadeUp} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-h2 text-ghost-white">Analytics</h1>
          <p className="text-body text-muted-silver mt-1">System performance and business metrics overview</p>
        </div>
        <div className="flex items-center gap-1 p-1 rounded-xl bg-steel-slate/20">
          {(['7d', '30d', '90d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                timeRange === range
                  ? 'bg-neon-emerald/15 text-neon-emerald'
                  : 'text-muted-silver hover:text-ghost-white'
              }`}
            >
              {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </motion.div>

      {/* KPI Row */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="RFPs Processed" value={stats.rfpsProcessed} change={stats.rfpsProcessedChange} changeLabel="vs last month" icon={<FileText size={18} />} glowColor="cyan" />
        <KPICard title="Completion Rate" value={stats.completionRate} change={stats.completionRateChange} changeLabel="improvement" icon={<CheckCircle2 size={18} />} glowColor="emerald" />
        <KPICard title="Avg. Processing Time" value={stats.avgProcessingTime} change={stats.avgProcessingTimeChange} changeLabel="faster" icon={<Clock size={18} />} glowColor="amber" />
        <KPICard title="Products Matched" value={stats.productsMatched} change={stats.productsMatchedChange} changeLabel="this period" icon={<Package size={18} />} glowColor="violet" />
      </motion.div>

      {/* Charts Row 1 */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TrendChart
            title="RFP Processing Volume — Last 30 Days"
            data={rfpProcessingTrend}
            color="#00E68A"
            height={280}
          />
        </div>
        <DonutChart
          title="Completion Rate"
          data={completionRateDonut}
          centerValue={String(stats.completionRate).replace('%', '') + '%'}
          centerLabel="Success"
        />
      </motion.div>

      {/* Charts Row 2 */}
      <motion.div variants={fadeUp} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChart
          title="Monthly Volume — Processed vs Matched"
          data={monthlyBarData}
          bars={[
            { dataKey: 'processed', color: 'rgba(0,212,255,0.5)', name: 'RFPs Processed' },
            { dataKey: 'matched', color: '#00E68A', name: 'Products Matched' },
          ]}
          xDataKey="month"
        />

        {/* Average Processing Times */}
        <Card variant="glass">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Average Processing Times</CardTitle>
              <Badge variant="soft" color="emerald">Improving</Badge>
            </div>
          </CardHeader>
          <div className="space-y-3 px-4 pb-4">
            {avgProcessingTimes.map((item) => (
              <div key={item.stage} className="flex items-center justify-between p-3 rounded-lg bg-steel-slate/15">
                <div className="flex items-center gap-3">
                  <Zap size={16} className="text-neon-emerald" />
                  <span className="text-sm text-ghost-white">{item.stage}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm font-semibold text-ghost-white font-mono">{item.time}</span>
                  <div className={`flex items-center gap-1 text-xs ${
                    item.status === 'improving' ? 'text-neon-emerald' :
                    item.status === 'degraded' ? 'text-coral-flame' : 'text-muted-silver'
                  }`}>
                    {item.trend < 0 ? <ArrowDownRight size={14} /> : item.trend > 0 ? <ArrowUpRight size={14} /> : <Activity size={14} />}
                    {item.trend !== 0 && <span>{Math.abs(item.trend)}%</span>}
                    {item.trend === 0 && <span>stable</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>

      {/* Category Breakdown Table */}
      <motion.div variants={fadeUp}>
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Category Performance Breakdown</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto px-4 pb-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted-silver border-b border-steel-slate/20">
                  <th className="pb-3 font-medium">Category</th>
                  <th className="pb-3 font-medium">RFPs</th>
                  <th className="pb-3 font-medium">Products Matched</th>
                  <th className="pb-3 font-medium">Avg Confidence</th>
                  <th className="pb-3 font-medium">Performance</th>
                </tr>
              </thead>
              <tbody>
                {categoryBreakdown.map((cat) => (
                  <tr key={cat.category} className="border-b border-steel-slate/10 hover:bg-steel-slate/10 transition-colors">
                    <td className="py-3 text-ghost-white font-medium">{cat.category}</td>
                    <td className="py-3 text-muted-silver">{cat.rfps}</td>
                    <td className="py-3 text-ghost-white font-semibold">{cat.matches.toLocaleString('en-IN')}</td>
                    <td className="py-3">
                      <span className={`font-semibold ${cat.avgConfidence >= 90 ? 'text-neon-emerald' : cat.avgConfidence >= 85 ? 'text-amber-glow' : 'text-coral-flame'}`}>
                        {cat.avgConfidence}%
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="w-24 h-2 rounded-full bg-steel-slate/40">
                        <div
                          className={`h-full rounded-full ${cat.avgConfidence >= 90 ? 'bg-neon-emerald' : cat.avgConfidence >= 85 ? 'bg-amber-glow' : 'bg-coral-flame'}`}
                          style={{ width: `${cat.avgConfidence}%` }}
                        />
                      </div>
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
