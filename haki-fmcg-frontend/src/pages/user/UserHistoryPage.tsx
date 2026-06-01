import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Calendar,
  Trash2,
  Zap,
  Building2,
  RefreshCw,
  Cpu,
  Award,
  Eye,
} from 'lucide-react';
import { Card, Button } from '@/components/ui';

// ── API ──

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const hdrs = () => {
  const t = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` };
};

// ── Types ──

type AnalysisStatus = 'completed' | 'partial' | 'failed';

interface SavedAnalysis {
  id: string;
  file_name: string;
  rfp_title: string;
  organization: string;
  detected_application: string;
  total_requirements: number;
  matched: number;
  confidence: number;
  oem_names: string[];
  agent_mode: string;
  status: AnalysisStatus;
  saved_at: string;
  saved_by: string;
  source: string;
}

// ── Status Configs ──

const statusConfig: Record<AnalysisStatus, { icon: React.ReactNode; bg: string; text: string; label: string }> = {
  completed: { icon: <CheckCircle2 size={14} />, bg: 'bg-neon-emerald/15', text: 'text-neon-emerald', label: 'Completed' },
  partial: { icon: <AlertTriangle size={14} />, bg: 'bg-amber-glow/15', text: 'text-amber-glow', label: 'Partial' },
  failed: { icon: <AlertTriangle size={14} />, bg: 'bg-coral-flame/15', text: 'text-coral-flame', label: 'Failed' },
};

// ── Animations ──

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

// ── Helpers ──

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function confColor(c: number): string {
  if (c >= 85) return 'text-neon-emerald';
  if (c >= 70) return 'text-amber-glow';
  return 'text-coral-flame';
}

// ══════════════════════════════════════════════════════════════════
//  Main Component
// ══════════════════════════════════════════════════════════════════

export default function UserHistoryPage() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<SavedAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<AnalysisStatus | 'all'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // ── Fetch analyses ──

  const fetchAnalyses = useCallback(async (showSpinner = true) => {
    if (showSpinner) setLoading(true);
    setError('');
    try {
      const r = await fetch(`${API}/api/v1/saved-analyses`, { headers: hdrs() });
      if (!r.ok) throw new Error(`Failed to load history (${r.status})`);
      const j = await r.json();
      const items: SavedAnalysis[] = (j.data ?? j ?? []).map((it: any) => ({
        id: it.id ?? '',
        file_name: it.file_name ?? 'Unknown',
        rfp_title: it.rfp_title ?? it.file_name ?? 'Untitled',
        organization: it.organization ?? '',
        detected_application: it.detected_application ?? '',
        total_requirements: it.total_requirements ?? 0,
        matched: it.matched ?? 0,
        confidence: it.confidence ?? 0,
        oem_names: it.oem_names ?? [],
        agent_mode: it.agent_mode ?? 'unknown',
        status: (it.status ?? 'completed') as AnalysisStatus,
        saved_at: it.saved_at ?? '',
        saved_by: it.saved_by ?? '',
        source: it.source ?? 'manual',
      }));
      setAnalyses(items);
    } catch (e: any) {
      setError(e.message || 'Failed to load history');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchAnalyses(); }, [fetchAnalyses]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const iv = setInterval(() => fetchAnalyses(false), 30000);
    return () => clearInterval(iv);
  }, [fetchAnalyses]);

  // ── Delete ──

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      const r = await fetch(`${API}/api/v1/saved-analyses/${id}`, { method: 'DELETE', headers: hdrs() });
      if (r.ok) {
        setAnalyses((prev) => prev.filter((a) => a.id !== id));
        if (expandedId === id) setExpandedId(null);
      }
    } catch { /* empty */ }
    setDeletingId(null);
  };

  // ── Generate Bid ──

  const handleGenerateBid = (item: SavedAnalysis) => {
    navigate('/user/bid-generator', {
      state: { analysisId: item.id, fileName: item.file_name },
    });
  };

  // ── View in Analyzer ──

  const handleViewDetails = (item: SavedAnalysis) => {
    navigate('/user/rfp-analyzer', {
      state: { analysisId: item.id },
    });
  };

  // ── Filtering ──

  const filtered = useMemo(() => {
    let list = [...analyses];
    if (statusFilter !== 'all') list = list.filter((a) => a.status === statusFilter);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (a) =>
          a.id.toLowerCase().includes(q) ||
          a.file_name.toLowerCase().includes(q) ||
          a.rfp_title.toLowerCase().includes(q) ||
          a.organization.toLowerCase().includes(q) ||
          a.detected_application.toLowerCase().includes(q),
      );
    }
    return list;
  }, [analyses, search, statusFilter]);

  // ── Stats ──

  const totalAnalyses = analyses.length;
  const completedCount = analyses.filter((a) => a.status === 'completed').length;
  const partialCount = analyses.filter((a) => a.status === 'partial').length;
  const avgConfidence = (() => {
    const withConf = analyses.filter((a) => a.confidence > 0);
    if (withConf.length === 0) return 0;
    return Math.round(withConf.reduce((s, a) => s + a.confidence, 0) / withConf.length);
  })();

  // ══════════════════════════════════════════════════════════════════
  // Render
  // ══════════════════════════════════════════════════════════════════

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <motion.div variants={fadeUp} className="flex items-center justify-between">
        <div>
          <h1 className="text-h2 text-ghost-white">Analysis History</h1>
          <p className="text-body text-muted-silver mt-1">
            Real-time record of every RFP analysis — generate bids anytime
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />}
            onClick={() => { setRefreshing(true); fetchAnalyses(false); }}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<FileText size={14} />}
            onClick={() => navigate('/user/rfp-analyzer')}
          >
            New Analysis
          </Button>
        </div>
      </motion.div>

      {/* Summary Stats */}
      <motion.div variants={fadeUp} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card variant="glass" className="p-4 text-center">
          <p className="text-2xl font-bold text-ghost-white">{totalAnalyses}</p>
          <p className="text-xs text-muted-silver">Total Analyses</p>
        </Card>
        <Card variant="glass" className="p-4 text-center">
          <p className="text-2xl font-bold text-neon-emerald">{completedCount}</p>
          <p className="text-xs text-muted-silver">Fully Matched</p>
        </Card>
        <Card variant="glass" className="p-4 text-center">
          <p className="text-2xl font-bold text-amber-glow">{partialCount}</p>
          <p className="text-xs text-muted-silver">Partial</p>
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
            placeholder="Search by ID, filename, title, organization, or application..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/60 focus:outline-none focus:border-neon-emerald/40 transition-colors"
          />
        </div>
        <div className="flex items-center gap-1 p-1 rounded-xl bg-steel-slate/20">
          {(['all', 'completed', 'partial', 'failed'] as const).map((s) => (
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

      {/* Loading */}
      {loading && (
        <motion.div variants={fadeUp} className="text-center py-16">
          <Loader2 size={32} className="mx-auto text-electric-cyan animate-spin mb-4" />
          <p className="text-sm text-muted-silver">Loading analysis history...</p>
        </motion.div>
      )}

      {/* Error */}
      {!loading && error && (
        <motion.div variants={fadeUp}>
          <Card variant="glass" className="p-8 text-center border-coral-flame/20">
            <AlertTriangle size={40} className="mx-auto text-coral-flame mb-3" />
            <p className="text-sm text-coral-flame mb-4">{error}</p>
            <Button variant="secondary" size="sm" onClick={() => fetchAnalyses()}>
              Retry
            </Button>
          </Card>
        </motion.div>
      )}

      {/* Empty State */}
      {!loading && !error && analyses.length === 0 && (
        <motion.div variants={fadeUp}>
          <Card variant="glass" className="p-12 text-center">
            <Clock size={48} className="mx-auto text-steel-slate/40 mb-4" />
            <h2 className="text-lg font-semibold text-ghost-white mb-2">No Analysis History Yet</h2>
            <p className="text-sm text-muted-silver mb-6">
              Analyze an RFP to see it here. Every analysis is automatically saved so you can
              generate bids from it at any time.
            </p>
            <div className="flex gap-3 justify-center">
              <Button variant="primary" onClick={() => navigate('/user/rfp-analyzer')}>
                Analyze an RFP
              </Button>
              <Button variant="secondary" onClick={() => navigate('/user/rfp-processing')}>
                RFP Processing
              </Button>
            </div>
          </Card>
        </motion.div>
      )}

      {/* No results for filter */}
      {!loading && !error && filtered.length === 0 && analyses.length > 0 && (
        <motion.div variants={fadeUp} className="text-center py-12">
          <Search size={40} className="mx-auto text-steel-slate/40 mb-3" />
          <p className="text-muted-silver text-sm">No analyses match your search criteria.</p>
        </motion.div>
      )}

      {/* History List */}
      <motion.div variants={fadeUp} className="space-y-3">
        <AnimatePresence mode="popLayout">
          {filtered.map((item) => {
            const sc = statusConfig[item.status] || statusConfig.completed;
            const isExpanded = expandedId === item.id;
            const ratio = item.total_requirements > 0
              ? Math.round((item.matched / item.total_requirements) * 100)
              : 0;

            return (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
              >
                <Card variant="glass" className="overflow-hidden hover:border-neon-emerald/15 transition-colors">
                  {/* Row Header */}
                  <div
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    className="p-4 flex items-center gap-4 cursor-pointer hover:bg-steel-slate/10 transition-colors"
                  >
                    {/* Status Badge */}
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${sc.bg} ${sc.text} flex-shrink-0`}
                    >
                      {sc.icon} {sc.label}
                    </span>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-mono text-muted-silver">{item.id}</span>
                        {item.source === 'auto' && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-electric-cyan/10 text-electric-cyan font-medium">
                            AUTO
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-ghost-white truncate">{item.rfp_title}</p>
                      {item.organization && (
                        <p className="text-xs text-muted-silver flex items-center gap-1 mt-0.5">
                          <Building2 size={11} /> {item.organization}
                        </p>
                      )}
                    </div>

                    {/* Metrics (desktop) */}
                    <div className="hidden lg:flex items-center gap-6 flex-shrink-0">
                      <div className="text-center">
                        <p className="text-sm font-semibold text-ghost-white">
                          {item.matched}/{item.total_requirements}
                        </p>
                        <p className="text-[10px] text-muted-silver">Matched</p>
                      </div>
                      <div className="text-center">
                        <p className={`text-sm font-semibold ${confColor(item.confidence)}`}>
                          {item.confidence}%
                        </p>
                        <p className="text-[10px] text-muted-silver">Confidence</p>
                      </div>
                      <div className="text-center">
                        <div className="w-14 h-1.5 bg-steel-slate/30 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              ratio >= 85
                                ? 'bg-neon-emerald'
                                : ratio >= 60
                                  ? 'bg-amber-glow'
                                  : 'bg-coral-flame'
                            }`}
                            style={{ width: `${ratio}%` }}
                          />
                        </div>
                        <p className="text-[10px] text-muted-silver mt-1">{ratio}% coverage</p>
                      </div>
                    </div>

                    {/* Date */}
                    <div className="text-right flex-shrink-0 hidden sm:block">
                      <p className="text-xs text-muted-silver">{timeAgo(item.saved_at)}</p>
                      <p className="text-[10px] text-steel-slate mt-0.5">
                        {new Date(item.saved_at).toLocaleDateString()}
                      </p>
                    </div>

                    {isExpanded ? (
                      <ChevronUp size={18} className="text-muted-silver flex-shrink-0" />
                    ) : (
                      <ChevronDown size={18} className="text-muted-silver flex-shrink-0" />
                    )}
                  </div>

                  {/* Expanded Detail Panel */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="border-t border-steel-slate/20 px-4 pb-4 pt-3 space-y-4">
                          {/* Detail Chips */}
                          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-silver">
                            <span className="flex items-center gap-1">
                              <Calendar size={12} /> {new Date(item.saved_at).toLocaleString()}
                            </span>
                            <span className="flex items-center gap-1">
                              <FileText size={12} /> {item.file_name}
                            </span>
                            {item.detected_application && (
                              <span className="flex items-center gap-1">
                                <Zap size={12} /> {item.detected_application}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Cpu size={12} />{' '}
                              {item.agent_mode === 'multi-agent-parallel'
                                ? 'AI Multi-Agent'
                                : 'Deterministic'}
                            </span>
                            <span className="flex items-center gap-1">
                              <Package size={12} /> {item.matched}/{item.total_requirements} matched
                            </span>
                          </div>

                          {/* OEM Badges */}
                          {item.oem_names.length > 0 && (
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-xs text-muted-silver font-medium">OEMs:</span>
                              {item.oem_names.slice(0, 6).map((name) => (
                                <span
                                  key={name}
                                  className="px-2 py-0.5 rounded-full bg-electric-cyan/10 text-electric-cyan text-[11px] font-medium"
                                >
                                  {name}
                                </span>
                              ))}
                              {item.oem_names.length > 6 && (
                                <span className="text-[11px] text-muted-silver">
                                  +{item.oem_names.length - 6} more
                                </span>
                              )}
                            </div>
                          )}

                          {/* Match Progress Bar */}
                          <div>
                            <div className="flex items-center justify-between text-xs mb-1.5">
                              <span className="text-muted-silver">Match Coverage</span>
                              <span className="text-ghost-white font-semibold">{ratio}%</span>
                            </div>
                            <div className="w-full h-2 bg-steel-slate/20 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${
                                  ratio >= 85
                                    ? 'bg-neon-emerald'
                                    : ratio >= 60
                                      ? 'bg-amber-glow'
                                      : 'bg-coral-flame'
                                }`}
                                style={{ width: `${ratio}%` }}
                              />
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-3 pt-1">
                            <Button
                              variant="primary"
                              size="sm"
                              leftIcon={<Award size={14} />}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleGenerateBid(item);
                              }}
                            >
                              Generate Bid
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              leftIcon={<Eye size={14} />}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleViewDetails(item);
                              }}
                            >
                              View Details
                            </Button>
                            <div className="flex-1" />
                            <Button
                              variant="secondary"
                              size="sm"
                              className="text-coral-flame/80 hover:text-coral-flame hover:border-coral-flame/30"
                              leftIcon={
                                deletingId === item.id ? (
                                  <Loader2 size={14} className="animate-spin" />
                                ) : (
                                  <Trash2 size={14} />
                                )
                              }
                              onClick={(e) => {
                                e.stopPropagation();
                                if (confirm('Delete this analysis from history?')) {
                                  handleDelete(item.id);
                                }
                              }}
                              disabled={deletingId === item.id}
                            >
                              Delete
                            </Button>
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
      </motion.div>
    </motion.div>
  );
}
