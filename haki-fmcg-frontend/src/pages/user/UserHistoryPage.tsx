import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  Search,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  FileText,
  ChevronDown,
  ChevronUp,
  Package,
  ArrowRight,
  Calendar,
  Timer,
  BarChart3,
  Filter,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Badge, Button } from '@/components/ui';
import { usePipelineRuns } from '@/hooks/useApi';

// ── Types ──

type RunStatus = 'completed' | 'failed' | 'running';

interface HistoryRun {
  id: string;
  rfpId: string;
  rfpTitle: string;
  status: RunStatus;
  startedAt: string;
  completedAt: string | null;
  duration: string;
  matchedProducts: number;
  totalItems: number;
  confidence: number;
  stages: { name: string; status: 'done' | 'failed' | 'skipped'; duration: string }[];
  category: string;
}

// ── Fallback Data ──

const fallbackHistory: HistoryRun[] = [
  {
    id: 'RUN-2026-0089', rfpId: 'RFP-2026-0142', rfpTitle: 'Electrical Cables for Nairobi Office',
    status: 'running', startedAt: '2026-02-10 09:15', completedAt: null, duration: '1m 42s',
    matchedProducts: 34, totalItems: 56, confidence: 78, category: 'Cables & Wires',
    stages: [
      { name: 'PDF Extraction', status: 'done', duration: '14s' },
      { name: 'Data Parsing', status: 'done', duration: '8s' },
      { name: 'Product Matching', status: 'done', duration: '52s' },
      { name: 'Spec Comparison', status: 'done', duration: '28s' },
      { name: 'Report Generation', status: 'skipped', duration: '-' },
    ],
  },
  {
    id: 'RUN-2026-0088', rfpId: 'RFP-2026-0141', rfpTitle: 'Data Center Wiring Infrastructure',
    status: 'completed', startedAt: '2026-02-09 14:30', completedAt: '2026-02-09 14:32', duration: '2m 05s',
    matchedProducts: 28, totalItems: 42, confidence: 65, category: 'Electrical',
    stages: [
      { name: 'PDF Extraction', status: 'done', duration: '18s' },
      { name: 'Data Parsing', status: 'done', duration: '12s' },
      { name: 'Product Matching', status: 'done', duration: '58s' },
      { name: 'Spec Comparison', status: 'done', duration: '22s' },
      { name: 'Report Generation', status: 'done', duration: '15s' },
    ],
  },
  {
    id: 'RUN-2026-0087', rfpId: 'RFP-2026-0140', rfpTitle: 'Safety Equipment — Warehouse',
    status: 'completed', startedAt: '2026-02-07 10:00', completedAt: '2026-02-07 10:01', duration: '1m 22s',
    matchedProducts: 128, totalItems: 128, confidence: 94, category: 'Safety Equipment',
    stages: [
      { name: 'PDF Extraction', status: 'done', duration: '10s' },
      { name: 'Data Parsing', status: 'done', duration: '6s' },
      { name: 'Product Matching', status: 'done', duration: '38s' },
      { name: 'Spec Comparison', status: 'done', duration: '18s' },
      { name: 'Report Generation', status: 'done', duration: '10s' },
    ],
  },
  {
    id: 'RUN-2026-0086', rfpId: 'RFP-2026-0139', rfpTitle: 'FMCG Products Q1 Restock',
    status: 'completed', startedAt: '2026-02-05 16:45', completedAt: '2026-02-05 16:48', duration: '2m 50s',
    matchedProducts: 312, totalItems: 320, confidence: 97, category: 'FMCG',
    stages: [
      { name: 'PDF Extraction', status: 'done', duration: '22s' },
      { name: 'Data Parsing', status: 'done', duration: '15s' },
      { name: 'Product Matching', status: 'done', duration: '1m 25s' },
      { name: 'Spec Comparison', status: 'done', duration: '30s' },
      { name: 'Report Generation', status: 'done', duration: '18s' },
    ],
  },
  {
    id: 'RUN-2026-0085', rfpId: 'RFP-2026-0138', rfpTitle: 'Office Supplies Annual Contract',
    status: 'completed', startedAt: '2026-02-03 11:20', completedAt: '2026-02-03 11:22', duration: '2m 10s',
    matchedProducts: 245, totalItems: 260, confidence: 92, category: 'Office Supplies',
    stages: [
      { name: 'PDF Extraction', status: 'done', duration: '16s' },
      { name: 'Data Parsing', status: 'done', duration: '10s' },
      { name: 'Product Matching', status: 'done', duration: '1m 05s' },
      { name: 'Spec Comparison', status: 'done', duration: '24s' },
      { name: 'Report Generation', status: 'done', duration: '15s' },
    ],
  },
  {
    id: 'RUN-2026-0084', rfpId: 'RFP-2026-0137', rfpTitle: 'Industrial Tools — Phase 2',
    status: 'failed', startedAt: '2026-02-01 09:00', completedAt: '2026-02-01 09:00', duration: '8s',
    matchedProducts: 0, totalItems: 18, confidence: 0, category: 'Industrial',
    stages: [
      { name: 'PDF Extraction', status: 'failed', duration: '8s' },
      { name: 'Data Parsing', status: 'skipped', duration: '-' },
      { name: 'Product Matching', status: 'skipped', duration: '-' },
      { name: 'Spec Comparison', status: 'skipped', duration: '-' },
      { name: 'Report Generation', status: 'skipped', duration: '-' },
    ],
  },
  {
    id: 'RUN-2026-0083', rfpId: 'RFP-2026-0136', rfpTitle: 'IT Hardware Procurement',
    status: 'completed', startedAt: '2026-01-28 13:15', completedAt: '2026-01-28 13:17', duration: '1m 55s',
    matchedProducts: 89, totalItems: 95, confidence: 88, category: 'Electrical',
    stages: [
      { name: 'PDF Extraction', status: 'done', duration: '14s' },
      { name: 'Data Parsing', status: 'done', duration: '9s' },
      { name: 'Product Matching', status: 'done', duration: '48s' },
      { name: 'Spec Comparison', status: 'done', duration: '26s' },
      { name: 'Report Generation', status: 'done', duration: '18s' },
    ],
  },
  {
    id: 'RUN-2026-0082', rfpId: 'RFP-2026-0135', rfpTitle: 'Underground Cable Supply',
    status: 'completed', startedAt: '2026-01-25 08:30', completedAt: '2026-01-25 08:32', duration: '2m 15s',
    matchedProducts: 156, totalItems: 162, confidence: 96, category: 'Cables & Wires',
    stages: [
      { name: 'PDF Extraction', status: 'done', duration: '20s' },
      { name: 'Data Parsing', status: 'done', duration: '12s' },
      { name: 'Product Matching', status: 'done', duration: '1m 10s' },
      { name: 'Spec Comparison', status: 'done', duration: '18s' },
      { name: 'Report Generation', status: 'done', duration: '15s' },
    ],
  },
];

const statusConfig: Record<RunStatus, { icon: React.ReactNode; bg: string; text: string; label: string }> = {
  running: { icon: <Loader2 size={14} className="animate-spin" />, bg: 'bg-amber-glow/15', text: 'text-amber-glow', label: 'Running' },
  completed: { icon: <CheckCircle2 size={14} />, bg: 'bg-neon-emerald/15', text: 'text-neon-emerald', label: 'Completed' },
  failed: { icon: <AlertTriangle size={14} />, bg: 'bg-coral-flame/15', text: 'text-coral-flame', label: 'Failed' },
};

const stageStatusConfig: Record<string, { color: string }> = {
  done: { color: 'text-neon-emerald' },
  failed: { color: 'text-coral-flame' },
  skipped: { color: 'text-steel-slate' },
};

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

export default function UserHistoryPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<RunStatus | 'all'>('all');
  const [expandedRun, setExpandedRun] = useState<string | null>(null);

  // ── API ──
  const { data: pipelineResponse } = usePipelineRuns();

  const history: HistoryRun[] = useMemo(() => {
    const apiItems = pipelineResponse?.data ?? pipelineResponse?.items;
    if (Array.isArray(apiItems) && apiItems.length > 0) {
      return apiItems.map((r: any) => ({
        id: r.id ?? r.run_id ?? `RUN-${r.id}`,
        rfpId: r.rfpId ?? r.rfp_id ?? '',
        rfpTitle: r.rfpTitle ?? r.rfp_title ?? r.title ?? 'Untitled',
        status: (r.status === 'running' || r.status === 'in_progress' ? 'running' : r.status ?? 'completed') as RunStatus,
        startedAt: r.startedAt ?? r.started_at ?? r.created_at ?? '',
        completedAt: r.completedAt ?? r.completed_at ?? null,
        duration: r.duration ?? '',
        matchedProducts: r.matchedProducts ?? r.matched_products ?? 0,
        totalItems: r.totalItems ?? r.total_items ?? 0,
        confidence: r.confidence ?? r.match_confidence ?? 0,
        stages: r.stages ?? [],
        category: r.category ?? 'General',
      }));
    }
    return fallbackHistory;
  }, [pipelineResponse]);

  const filtered = useMemo(() => {
    let list = [...history];
    if (statusFilter !== 'all') list = list.filter((r) => r.status === statusFilter);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) => String(r.id).toLowerCase().includes(q) || String(r.rfpId).toLowerCase().includes(q) || r.rfpTitle.toLowerCase().includes(q),
      );
    }
    return list;
  }, [history, search, statusFilter]);

  const totalRuns = history.length;
  const completedRuns = history.filter((r) => r.status === 'completed').length;
  const failedRuns = history.filter((r) => r.status === 'failed').length;
  const avgConfidence = (() => {
    const withConf = history.filter((r) => r.confidence > 0);
    if (withConf.length === 0) return 0;
    return Math.round(withConf.reduce((sum, r) => sum + r.confidence, 0) / withConf.length);
  })();

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <motion.div variants={fadeUp}>
        <h1 className="text-h2 text-ghost-white">History</h1>
        <p className="text-body text-muted-silver mt-1">Track workflow execution history and performance trends</p>
      </motion.div>

      {/* Summary Stats */}
      <motion.div variants={fadeUp} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card variant="glass" className="p-4 text-center">
          <p className="text-2xl font-bold text-ghost-white">{totalRuns}</p>
          <p className="text-xs text-muted-silver">Total Runs</p>
        </Card>
        <Card variant="glass" className="p-4 text-center">
          <p className="text-2xl font-bold text-neon-emerald">{completedRuns}</p>
          <p className="text-xs text-muted-silver">Completed</p>
        </Card>
        <Card variant="glass" className="p-4 text-center">
          <p className="text-2xl font-bold text-coral-flame">{failedRuns}</p>
          <p className="text-xs text-muted-silver">Failed</p>
        </Card>
        <Card variant="glass" className="p-4 text-center">
          <p className="text-2xl font-bold text-electric-cyan">{avgConfidence}%</p>
          <p className="text-xs text-muted-silver">Avg Confidence</p>
        </Card>
      </motion.div>

      {/* Search & Filter */}
      <motion.div variants={fadeUp} className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input
            type="text"
            placeholder="Search by run ID, RFP ID, or title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/60 focus:outline-none focus:border-neon-emerald/40 transition-colors"
          />
        </div>
        <div className="flex items-center gap-1 p-1 rounded-xl bg-steel-slate/20">
          {(['all', 'completed', 'running', 'failed'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                statusFilter === s
                  ? 'bg-neon-emerald/15 text-neon-emerald'
                  : 'text-muted-silver hover:text-ghost-white'
              }`}
            >
              {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </motion.div>

      {/* History List */}
      <motion.div variants={fadeUp} className="space-y-3">
        <AnimatePresence mode="popLayout">
          {filtered.map((run) => {
            const sc = statusConfig[run.status];
            const isExpanded = expandedRun === run.id;

            return (
              <motion.div
                key={run.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
              >
                <Card variant="glass" className="overflow-hidden hover:border-neon-emerald/15 transition-colors">
                  {/* Run Header */}
                  <div
                    onClick={() => setExpandedRun(isExpanded ? null : run.id)}
                    className="p-4 flex items-center gap-4 cursor-pointer hover:bg-steel-slate/10 transition-colors"
                  >
                    {/* Status */}
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${sc.bg} ${sc.text}`}>
                      {sc.icon} {sc.label}
                    </span>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono text-muted-silver">{run.id}</span>
                        <span className="text-xs text-steel-slate">→</span>
                        <span className="text-xs font-mono text-electric-cyan">{run.rfpId}</span>
                      </div>
                      <p className="text-sm font-medium text-ghost-white truncate">{run.rfpTitle}</p>
                    </div>

                    {/* Metrics */}
                    <div className="hidden lg:flex items-center gap-6 flex-shrink-0">
                      <div className="text-center">
                        <p className="text-sm font-semibold text-ghost-white">{run.matchedProducts}/{run.totalItems}</p>
                        <p className="text-[10px] text-muted-silver">Matched</p>
                      </div>
                      {run.confidence > 0 && (
                        <div className="text-center">
                          <p className={`text-sm font-semibold ${run.confidence >= 85 ? 'text-neon-emerald' : run.confidence >= 70 ? 'text-amber-glow' : 'text-coral-flame'}`}>
                            {run.confidence}%
                          </p>
                          <p className="text-[10px] text-muted-silver">Confidence</p>
                        </div>
                      )}
                      <div className="text-center">
                        <p className="text-sm font-semibold text-ghost-white font-mono">{run.duration}</p>
                        <p className="text-[10px] text-muted-silver">Duration</p>
                      </div>
                    </div>

                    {/* Date */}
                    <div className="text-right flex-shrink-0 hidden sm:block">
                      <p className="text-xs text-muted-silver">{run.startedAt}</p>
                    </div>

                    {isExpanded ? <ChevronUp size={18} className="text-muted-silver" /> : <ChevronDown size={18} className="text-muted-silver" />}
                  </div>

                  {/* Stage Details (expanded) */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="border-t border-steel-slate/20 px-4 pb-4 pt-3">
                          <div className="flex items-center gap-6 mb-4 text-xs text-muted-silver">
                            <span className="flex items-center gap-1"><Calendar size={12} /> Started: {run.startedAt}</span>
                            {run.completedAt && <span className="flex items-center gap-1"><CheckCircle2 size={12} /> Completed: {run.completedAt}</span>}
                            <span className="flex items-center gap-1"><Timer size={12} /> Duration: {run.duration}</span>
                            <span className="flex items-center gap-1"><Package size={12} /> Category: {run.category}</span>
                          </div>

                          <h4 className="text-xs font-semibold text-muted-silver uppercase tracking-wider mb-3">Pipeline Stages</h4>
                          <div className="flex items-center gap-2">
                            {run.stages.map((stage, i) => (
                              <div key={i} className="flex items-center gap-2 flex-1">
                                <div className={`flex flex-col items-center gap-1 flex-1 p-3 rounded-lg bg-steel-slate/15 ${stageStatusConfig[stage.status].color}`}>
                                  {stage.status === 'done' ? <CheckCircle2 size={16} /> : stage.status === 'failed' ? <AlertTriangle size={16} /> : <Clock size={16} />}
                                  <span className="text-[10px] font-medium text-center leading-tight">{stage.name}</span>
                                  <span className="text-[10px] text-muted-silver">{stage.duration}</span>
                                </div>
                                {i < run.stages.length - 1 && (
                                  <ArrowRight size={14} className="text-steel-slate/40 flex-shrink-0" />
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {filtered.length === 0 && (
          <div className="text-center py-16">
            <Clock size={48} className="mx-auto text-steel-slate/40 mb-4" />
            <p className="text-muted-silver">No runs match your search criteria.</p>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
