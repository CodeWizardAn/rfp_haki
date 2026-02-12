import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Cpu,
  HardDrive,
  MemoryStick,
  Database,
  Zap,
  Shield,
  Layers,
  BarChart3,
  Activity,
  ToggleLeft,
  ToggleRight,
  Play,
  Loader2,
  AlertTriangle,
  RefreshCw,
  Server,
  Timer,
  Gauge,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface PerfModule {
  id: string;
  name: string;
  icon: React.ReactNode;
  enabled: boolean;
  status: 'healthy' | 'warning' | 'error';
  description: string;
  stats: { label: string; value: string }[];
}

/* ─── mock data ─── */
const initialModules: PerfModule[] = [
  { id: 'caching', name: 'Redis Cache', icon: <Database size={14} />, enabled: true, status: 'healthy', description: 'In-memory caching for API responses and query results', stats: [{ label: 'Hit Rate', value: '94.2%' }, { label: 'Size', value: '1.2 GB' }, { label: 'Keys', value: '45,218' }] },
  { id: 'rate_limit', name: 'Rate Limiter', icon: <Shield size={14} />, enabled: true, status: 'healthy', description: 'API rate limiting per user/IP with sliding window', stats: [{ label: 'Limit', value: '1000/min' }, { label: 'Current', value: '342/min' }, { label: 'Blocked', value: '12 today' }] },
  { id: 'batch', name: 'Batch Processor', icon: <Layers size={14} />, enabled: true, status: 'warning', description: 'Bulk operations for imports, exports, and analytics', stats: [{ label: 'Queue', value: '23 jobs' }, { label: 'Throughput', value: '150/s' }, { label: 'Failed', value: '2 jobs' }] },
  { id: 'autoscale', name: 'Auto Scaler', icon: <BarChart3 size={14} />, enabled: false, status: 'healthy', description: 'Automatic horizontal scaling based on CPU/memory thresholds', stats: [{ label: 'Instances', value: '2/8' }, { label: 'Threshold', value: '75% CPU' }, { label: 'Cooldown', value: '300s' }] },
  { id: 'conn_pool', name: 'Connection Pool', icon: <Server size={14} />, enabled: true, status: 'healthy', description: 'Database connection pooling with PgBouncer', stats: [{ label: 'Active', value: '18/50' }, { label: 'Idle', value: '32' }, { label: 'Wait', value: '0' }] },
  { id: 'query_opt', name: 'Query Optimizer', icon: <Zap size={14} />, enabled: true, status: 'healthy', description: 'Automatic query plan analysis and index suggestions', stats: [{ label: 'Optimized', value: '1,234' }, { label: 'Slow Queries', value: '3' }, { label: 'Avg', value: '12ms' }] },
  { id: 'compression', name: 'Response Compression', icon: <HardDrive size={14} />, enabled: true, status: 'healthy', description: 'Gzip/Brotli compression for API responses', stats: [{ label: 'Ratio', value: '4.2x' }, { label: 'Saved', value: '892 MB/day' }, { label: 'Method', value: 'Brotli' }] },
  { id: 'cdn', name: 'CDN Cache', icon: <Activity size={14} />, enabled: true, status: 'healthy', description: 'Edge caching for static assets and public endpoints', stats: [{ label: 'Hit Rate', value: '98.1%' }, { label: 'Bandwidth', value: '2.4 TB' }, { label: 'Regions', value: '5' }] },
  { id: 'bottleneck', name: 'Bottleneck Detector', icon: <AlertTriangle size={14} />, enabled: true, status: 'warning', description: 'Real-time identification of performance bottlenecks', stats: [{ label: 'Alerts', value: '3 active' }, { label: 'Scanned', value: '156 endpoints' }, { label: 'Last', value: '2m ago' }] },
  { id: 'profiler', name: 'APM Profiler', icon: <Timer size={14} />, enabled: false, status: 'healthy', description: 'Application performance monitoring with distributed tracing', stats: [{ label: 'Traces', value: '0' }, { label: 'Spans', value: '0' }, { label: 'Overhead', value: '~2%' }] },
];

const GaugeBar = ({ label, value, max, unit, color }: { label: string; value: number; max: number; unit: string; color: string }) => {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div>
      <div className="flex justify-between text-[10px] mb-1">
        <span className="text-muted-silver">{label}</span>
        <span className={color}>{value}{unit} / {max}{unit}</span>
      </div>
      <div className="h-2 rounded-full bg-steel-slate/20 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full rounded-full ${pct > 85 ? 'bg-coral-flame' : pct > 65 ? 'bg-amber-glow' : 'bg-neon-emerald'}`}
        />
      </div>
    </div>
  );
};

export default function PerformanceTuningPage() {
  const [modules, setModules] = useState(initialModules);
  const [loadTesting, setLoadTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ rps: number; avgLatency: number; p99: number; errors: number } | null>(null);

  const toggleModule = (id: string) => {
    setModules((prev) => prev.map((m) => m.id === id ? { ...m, enabled: !m.enabled } : m));
  };

  const runLoadTest = () => {
    setLoadTesting(true);
    setTestResult(null);
    setTimeout(() => {
      setTestResult({ rps: 2847, avgLatency: 42, p99: 189, errors: 3 });
      setLoadTesting(false);
    }, 3000);
  };

  const enabledCount = modules.filter((m) => m.enabled).length;
  const warningCount = modules.filter((m) => m.status === 'warning').length;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/settings" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
          <ArrowLeft size={18} className="text-muted-silver" />
        </Link>
        <div className="flex-1">
          <h1 className="text-h1 text-ghost-white">Performance Tuning</h1>
          <p className="text-body text-muted-silver">{enabledCount}/{modules.length} modules active · {warningCount} warnings</p>
        </div>
        <Button variant="secondary" size="sm" leftIcon={<RefreshCw size={14} />}>Refresh Metrics</Button>
      </div>

      {/* Resource Gauges */}
      <div className="grid md:grid-cols-4 gap-3">
        {[
          { label: 'CPU', value: 42, max: 100, unit: '%', icon: <Cpu size={14} className="text-electric-cyan" />, color: 'text-electric-cyan' },
          { label: 'Memory', value: 6.2, max: 16, unit: ' GB', icon: <MemoryStick size={14} className="text-violet-pulse" />, color: 'text-violet-pulse' },
          { label: 'Disk I/O', value: 120, max: 500, unit: ' MB/s', icon: <HardDrive size={14} className="text-neon-emerald" />, color: 'text-neon-emerald' },
          { label: 'Network', value: 340, max: 1000, unit: ' Mbps', icon: <Gauge size={14} className="text-amber-glow" />, color: 'text-amber-glow' },
        ].map((g) => (
          <Card key={g.label} variant="glass" className="p-3">
            <div className="flex items-center gap-1.5 mb-2">{g.icon}<span className="text-xs font-semibold text-ghost-white">{g.label}</span></div>
            <GaugeBar {...g} />
          </Card>
        ))}
      </div>

      {/* Module Grid */}
      <div className="grid md:grid-cols-2 gap-3">
        {modules.map((mod) => (
          <Card key={mod.id} variant="glass" className={`p-4 transition-all ${!mod.enabled ? 'opacity-50' : ''}`}>
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg ${mod.status === 'healthy' ? 'bg-neon-emerald/10 text-neon-emerald' : mod.status === 'warning' ? 'bg-amber-glow/10 text-amber-glow' : 'bg-coral-flame/10 text-coral-flame'}`}>
                {mod.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-xs font-semibold text-ghost-white">{mod.name}</h4>
                  <Badge variant="soft" color={mod.status === 'healthy' ? 'green' : mod.status === 'warning' ? 'amber' : 'red'} size="sm">{mod.status}</Badge>
                </div>
                <p className="text-[10px] text-muted-silver mt-0.5">{mod.description}</p>
                {mod.enabled && (
                  <div className="flex gap-3 mt-2">
                    {mod.stats.map((s) => (
                      <div key={s.label}>
                        <span className="text-[9px] text-muted-silver/70 block">{s.label}</span>
                        <span className="text-xs text-ghost-white font-mono">{s.value}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button onClick={() => toggleModule(mod.id)} className="flex-shrink-0 mt-0.5">
                {mod.enabled
                  ? <ToggleRight size={22} className="text-neon-emerald" />
                  : <ToggleLeft size={22} className="text-muted-silver/40" />
                }
              </button>
            </div>
          </Card>
        ))}
      </div>

      {/* Load Test */}
      <Card variant="glass" className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-ghost-white">Load Test</h3>
            <p className="text-[10px] text-muted-silver">Run a simulated stress test against the platform</p>
          </div>
          <Button onClick={runLoadTest} disabled={loadTesting} leftIcon={loadTesting ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}>
            {loadTesting ? 'Running...' : 'Run Load Test'}
          </Button>
        </div>
        {testResult && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-4 gap-3">
            {[
              { label: 'Requests/sec', value: testResult.rps.toLocaleString(), color: 'text-electric-cyan' },
              { label: 'Avg Latency', value: `${testResult.avgLatency}ms`, color: 'text-neon-emerald' },
              { label: 'P99 Latency', value: `${testResult.p99}ms`, color: 'text-amber-glow' },
              { label: 'Errors', value: testResult.errors.toString(), color: testResult.errors > 10 ? 'text-coral-flame' : 'text-neon-emerald' },
            ].map((r) => (
              <div key={r.label} className="p-2.5 rounded-lg bg-steel-slate/8 text-center">
                <span className={`text-lg font-bold font-mono ${r.color}`}>{r.value}</span>
                <span className="text-[9px] text-muted-silver block">{r.label}</span>
              </div>
            ))}
          </motion.div>
        )}
      </Card>
    </motion.div>
  );
}
