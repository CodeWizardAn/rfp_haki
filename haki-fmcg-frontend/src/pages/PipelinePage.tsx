import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch,
  Play,
  History,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  FileText,
  Braces,
  Search,
  Globe,
  Shield,
  BarChart3,
  RefreshCw,
  StopCircle,
  Zap,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { PipelineStatsPanel, PipelineErrorRecovery } from '@/components/pipeline';
import { usePipelineRuns, useRunPipeline, useCancelPipeline } from '@/hooks/useApi';

/* ───── pipeline stages definition ───── */
const STAGES = [
  { id: 'rfp_intake', label: 'RFP\nIntake', icon: <FileText size={16} />, col: 0, row: 0 },
  { id: 'pdf_extraction', label: 'PDF\nExtraction', icon: <FileText size={16} />, col: 1, row: 0 },
  { id: 'term_matching', label: 'Term\nMatching', icon: <Search size={16} />, col: 2, row: 0 },
  { id: 'vector_search', label: 'Vector\nSearch', icon: <Braces size={16} />, col: 3, row: 0 },
  { id: 'spec_matching', label: 'Spec\nMatching', icon: <Search size={16} />, col: 1, row: 1 },
  { id: 'pricing', label: 'Price\nCalc', icon: <BarChart3 size={16} />, col: 2, row: 1 },
  { id: 'compliance', label: 'Compliance\nCheck', icon: <Shield size={16} />, col: 3, row: 1 },
  { id: 'bid_generation', label: 'Bid\nGeneration', icon: <Zap size={16} />, col: 4, row: 0 },
];

const CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 7], // top row
  [1, 4], [4, 5], [5, 6], [6, 7], // bottom row
];

type StageStatus = 'idle' | 'running' | 'success' | 'error' | 'skipped';

interface PipelineRun {
  id: string;
  rfpId: string;
  status: 'running' | 'completed' | 'failed';
  stages: Record<string, { status: StageStatus; duration: string; items?: number }>;
  startedAt: string;
  completedAt?: string;
  mode: string;
}

/* mock history */
const mockRuns: PipelineRun[] = [
  {
    id: 'pipe-8a3f',
    rfpId: 'RFP-2026-0001',
    status: 'running',
    startedAt: '2026-02-04 09:12:34',
    mode: 'Standard (8-stage)',
    stages: {
      rfp_intake: { status: 'success', duration: '0.4s', items: 1 },
      pdf_extraction: { status: 'success', duration: '4.5s', items: 5 },
      term_matching: { status: 'success', duration: '2.1s', items: 47 },
      vector_search: { status: 'success', duration: '3.2s', items: 14 },
      spec_matching: { status: 'running', duration: '—', items: undefined },
      pricing: { status: 'idle', duration: '—' },
      compliance: { status: 'idle', duration: '—' },
      bid_generation: { status: 'idle', duration: '—' },
    },
  },
  {
    id: 'pipe-7c22',
    rfpId: 'RFP-2026-0002',
    status: 'completed',
    startedAt: '2026-02-03 14:05:12',
    completedAt: '2026-02-03 14:08:45',
    mode: 'Agent-driven (5-stage)',
    stages: {
      rfp_intake: { status: 'success', duration: '0.3s', items: 1 },
      pdf_extraction: { status: 'success', duration: '3.8s', items: 3 },
      term_matching: { status: 'success', duration: '1.8s', items: 32 },
      vector_search: { status: 'success', duration: '2.5s', items: 8 },
      spec_matching: { status: 'success', duration: '6.4s', items: 8 },
      pricing: { status: 'success', duration: '3.1s', items: 3 },
      compliance: { status: 'success', duration: '1.2s', items: 3 },
      bid_generation: { status: 'success', duration: '2.4s', items: 1 },
    },
  },
  {
    id: 'pipe-5b11',
    rfpId: 'RFP-2026-0003',
    status: 'failed',
    startedAt: '2026-02-02 10:30:00',
    completedAt: '2026-02-02 10:32:15',
    mode: 'Standard (8-stage)',
    stages: {
      rfp_intake: { status: 'success', duration: '0.5s', items: 1 },
      pdf_extraction: { status: 'error', duration: '2.1s' },
      term_matching: { status: 'skipped', duration: '—' },
      vector_search: { status: 'skipped', duration: '—' },
      spec_matching: { status: 'skipped', duration: '—' },
      pricing: { status: 'skipped', duration: '—' },
      compliance: { status: 'skipped', duration: '—' },
      bid_generation: { status: 'skipped', duration: '—' },
    },
  },
];

/* ───── node color helpers ───── */
const nodeColors: Record<StageStatus, { bg: string; border: string; text: string; glow: string }> = {
  idle: { bg: 'bg-steel-slate/20', border: 'border-steel-slate/30', text: 'text-muted-silver/60', glow: '' },
  running: { bg: 'bg-electric-cyan/10', border: 'border-electric-cyan/50', text: 'text-electric-cyan', glow: 'shadow-[0_0_20px_rgba(0,212,255,0.25)]' },
  success: { bg: 'bg-neon-emerald/10', border: 'border-neon-emerald/50', text: 'text-neon-emerald', glow: '' },
  error: { bg: 'bg-coral-flame/10', border: 'border-coral-flame/50', text: 'text-coral-flame', glow: '' },
  skipped: { bg: 'bg-amber-glow/5', border: 'border-amber-glow/20', text: 'text-amber-glow/50', glow: '' },
};

const statusBadgeColor = (s: string) =>
  s === 'running' ? 'cyan' : s === 'completed' ? 'emerald' : 'coral';

/* ═══════════════════════════════════════════════════ */
export default function PipelinePage() {
  /* ── Backend hooks ── */
  const { data: apiRuns } = usePipelineRuns();
  const runPipelineMutation = useRunPipeline();
  const cancelPipelineMutation = useCancelPipeline();

  /* ── Merge backend runs with mock fallback ── */
  const allRuns: PipelineRun[] = useMemo(() => {
    if (apiRuns && Array.isArray(apiRuns) && apiRuns.length > 0) {
      return (apiRuns as unknown as PipelineRun[]);
    }
    const runs = (apiRuns as unknown as { data?: PipelineRun[] })?.data;
    if (runs?.length) return runs;
    return mockRuns;
  }, [apiRuns]);

  const [selectedRun, setSelectedRun] = useState<PipelineRun>(allRuns[0] ?? mockRuns[0]!);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showNewRun, setShowNewRun] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Keep selectedRun synced when backend data arrives
  useEffect(() => {
    if (allRuns.length && allRuns[0] && allRuns[0].id !== selectedRun.id) {
      const found = allRuns.find((r) => r.id === selectedRun.id);
      if (found) setSelectedRun(found);
      else setSelectedRun(allRuns[0]);
    }
  }, [allRuns]);  // eslint-disable-line react-hooks/exhaustive-deps

  // Animate flowing particles for running pipeline
  const [particlePos, setParticlePos] = useState(0);
  useEffect(() => {
    if (selectedRun.status !== 'running') return;
    const t = setInterval(() => setParticlePos((p) => (p + 1) % 100), 50);
    return () => clearInterval(t);
  }, [selectedRun.status]);

  const completedStages = Object.values(selectedRun.stages).filter((s) => s.status === 'success').length;
  const totalStages = STAGES.length;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-electric-cyan/10">
            <GitBranch size={24} className="text-electric-cyan" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Pipeline Control Center</h1>
            <p className="text-body text-muted-silver">Visualize, monitor, and control processing pipelines</p>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button variant="secondary" leftIcon={<History size={14} />} onClick={() => setShowHistory(!showHistory)}>
            History
          </Button>
          <Button variant="primary" leftIcon={<Play size={14} />} onClick={() => setShowNewRun(true)}>
            Run New Pipeline
          </Button>
        </div>
      </div>

      {/* ── Active Run Info ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Pipeline', value: selectedRun.id, color: 'text-electric-cyan' },
          { label: 'RFP', value: selectedRun.rfpId, color: 'text-ghost-white' },
          { label: 'Stages', value: `${completedStages}/${totalStages}`, color: 'text-neon-emerald' },
          { label: 'Mode', value: selectedRun.mode, color: 'text-violet-pulse' },
        ].map((item) => (
          <Card key={item.label} variant="glass" className="!p-3">
            <p className="text-xs text-muted-silver uppercase tracking-wider">{item.label}</p>
            <p className={`text-sm font-bold mt-0.5 ${item.color}`}>{item.value}</p>
          </Card>
        ))}
      </div>

      {/* ── Flow Diagram ── */}
      <Card variant="glass" className="relative overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Pipeline Flow
            {selectedRun.status === 'running' && (
              <span className="inline-flex items-center gap-1 text-xs text-electric-cyan">
                <Loader2 size={12} className="animate-spin" /> Live
              </span>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 text-xs text-muted-silver">
              <Clock size={12} /> Started: {selectedRun.startedAt}
            </div>
            {selectedRun.status === 'running' && (
              <Button variant="danger" size="xs" leftIcon={<StopCircle size={10} />} onClick={() => cancelPipelineMutation.mutate(selectedRun.id)}>Cancel</Button>
            )}
          </div>
        </CardHeader>

        {/* SVG Flow */}
        <div ref={canvasRef} className="relative py-6 px-4 overflow-x-auto">
          <div className="min-w-[800px] relative" style={{ height: 260 }}>
            {/* SVG Connections */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
              {CONNECTIONS.map(([fromIdx, toIdx], ci) => {
                const from = STAGES[fromIdx!]!;
                const to = STAGES[toIdx!]!;
                const x1 = from.col * 160 + 70;
                const y1 = from.row * 120 + 50;
                const x2 = to.col * 160 + 70;
                const y2 = to.row * 120 + 50;

                const fromStatus = selectedRun.stages[from.id]?.status || 'idle';
                const toStatus = selectedRun.stages[to.id]?.status || 'idle';
                const isActive = fromStatus === 'success' && (toStatus === 'running' || toStatus === 'success');

                return (
                  <g key={ci}>
                    <line
                      x1={x1} y1={y1} x2={x2} y2={y2}
                      stroke={isActive ? '#00D4FF' : '#1E2642'}
                      strokeWidth={2}
                      strokeDasharray={isActive ? undefined : '4 4'}
                      opacity={isActive ? 0.6 : 0.3}
                    />
                    {/* Flowing particle */}
                    {isActive && selectedRun.status === 'running' && toStatus === 'running' && (
                      <circle
                        cx={x1 + (x2 - x1) * (particlePos / 100)}
                        cy={y1 + (y2 - y1) * (particlePos / 100)}
                        r={3}
                        fill="#00D4FF"
                        opacity={0.8}
                      />
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Stage Nodes */}
            {STAGES.map((stage) => {
              const stageData = selectedRun.stages[stage.id];
              const status: StageStatus = stageData?.status || 'idle';
              const colors = nodeColors[status];
              const x = stage.col * 160 + 10;
              const y = stage.row * 120 + 10;

              return (
                <motion.button
                  key={stage.id}
                  className={`absolute flex flex-col items-center justify-center w-[120px] h-[80px] rounded-xl border-2 transition-all cursor-pointer ${colors.bg} ${colors.border} ${colors.glow} ${
                    selectedStage === stage.id ? 'ring-2 ring-electric-cyan/40' : ''
                  }`}
                  style={{ left: x, top: y, zIndex: 1 }}
                  onClick={() => setSelectedStage(selectedStage === stage.id ? null : stage.id)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className={colors.text}>{stage.icon}</span>
                  <span className={`text-xs mt-1 text-center leading-tight whitespace-pre-line ${colors.text}`}>
                    {stage.label}
                  </span>
                  {/* Status indicator */}
                  <span className="absolute -top-1 -right-1">
                    {status === 'success' && <CheckCircle2 size={14} className="text-neon-emerald" />}
                    {status === 'running' && <Loader2 size={14} className="text-electric-cyan animate-spin" />}
                    {status === 'error' && <XCircle size={14} className="text-coral-flame" />}
                    {status === 'skipped' && <span className="text-amber-glow text-[10px] font-bold">—</span>}
                  </span>
                  {/* Duration */}
                  {stageData && stageData.duration !== '—' && (
                    <span className="absolute -bottom-5 text-[10px] text-muted-silver">{stageData.duration}</span>
                  )}
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-2 mx-4 mb-4">
          <div className="flex items-center justify-between text-xs text-muted-silver mb-1">
            <span>Pipeline Progress</span>
            <span>{completedStages}/{totalStages} stages</span>
          </div>
          <div className="w-full h-2 rounded-full bg-steel-slate/30">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-electric-cyan via-neon-emerald to-electric-cyan"
              initial={{ width: 0 }}
              animate={{ width: `${(completedStages / totalStages) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </Card>

      {/* ── Stage Detail (Expanded) ── */}
      <AnimatePresence>
        {selectedStage && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="capitalize">{selectedStage.replace('_', ' ')} — Stage Detail</CardTitle>
                <div className="flex gap-2">
                  <Badge variant="soft" color={statusBadgeColor(selectedRun.stages[selectedStage]?.status || 'idle')}>
                    {selectedRun.stages[selectedStage]?.status || 'idle'}
                  </Badge>
                  <Button variant="secondary" size="xs" leftIcon={<RefreshCw size={10} />}>Re-run Stage</Button>
                </div>
              </CardHeader>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-xs text-muted-silver">Duration</p>
                  <p className="text-ghost-white font-medium">{selectedRun.stages[selectedStage]?.duration || '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-silver">Items Processed</p>
                  <p className="text-ghost-white font-medium">{selectedRun.stages[selectedStage]?.items ?? '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-silver">Input</p>
                  <p className="text-muted-silver font-mono text-xs">Previous stage output</p>
                </div>
                <div>
                  <p className="text-xs text-muted-silver">Output</p>
                  <p className="text-muted-silver font-mono text-xs">JSON (click to expand)</p>
                </div>
              </div>
              {/* Mock JSON preview */}
              <pre className="mt-4 p-4 rounded-lg bg-deep-navy/60 text-xs text-electric-cyan/70 font-mono overflow-x-auto max-h-40">
{JSON.stringify({
  stage: selectedStage,
  status: selectedRun.stages[selectedStage]?.status,
  duration: selectedRun.stages[selectedStage]?.duration,
  items_processed: selectedRun.stages[selectedStage]?.items ?? 0,
  pipeline_id: selectedRun.id,
  rfp_id: selectedRun.rfpId,
}, null, 2)}
              </pre>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Pipeline History ── */}
      <AnimatePresence>
        {showHistory && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Pipeline History</CardTitle>
              </CardHeader>
              <div className="space-y-3">
                {allRuns.map((run) => (
                  <button
                    key={run.id}
                    onClick={() => { setSelectedRun(run); setSelectedStage(null); }}
                    className={`w-full flex items-center justify-between p-4 rounded-xl transition-colors text-left ${
                      selectedRun.id === run.id ? 'bg-electric-cyan/10 border border-electric-cyan/30' : 'bg-steel-slate/10 hover:bg-steel-slate/15'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <Badge variant="soft" color={statusBadgeColor(run.status)}>{run.status}</Badge>
                      <div>
                        <p className="text-sm font-medium text-ghost-white">{run.id}</p>
                        <p className="text-xs text-muted-silver">{run.rfpId} · {run.mode}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted-silver">{run.startedAt}</p>
                      <p className="text-xs text-muted-silver">
                        {Object.values(run.stages).filter((s) => s.status === 'success').length}/{STAGES.length} stages
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Pipeline Statistics ── */}
      <PipelineStatsPanel />

      {/* ── Error Recovery ── */}
      <PipelineErrorRecovery />

      {/* ── New Pipeline Run Modal ── */}
      <AnimatePresence>
        {showNewRun && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-deep-navy/70 backdrop-blur-sm z-40"
              onClick={() => setShowNewRun(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg bg-midnight-blue border border-steel-slate/30 rounded-2xl shadow-2xl"
            >
              <div className="px-6 py-5 border-b border-steel-slate/30">
                <h3 className="text-lg font-semibold text-ghost-white">New Pipeline Run</h3>
                <p className="text-xs text-muted-silver mt-1">Configure and start a new processing pipeline</p>
              </div>
              <div className="px-6 py-5 space-y-4">
                {/* Input Type */}
                <div>
                  <label className="text-xs text-muted-silver uppercase tracking-wider mb-2 block">Input Type</label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { value: 'pdf', label: 'PDF Upload', icon: <FileText size={14} /> },
                      { value: 'text', label: 'Text Paste', icon: <Braces size={14} /> },
                      { value: 'json', label: 'Requirements JSON', icon: <Braces size={14} /> },
                      { value: 'url', label: 'URL Scan', icon: <Globe size={14} /> },
                    ].map((opt) => (
                      <button
                        key={opt.value}
                        className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-steel-slate/30 text-muted-silver hover:border-electric-cyan/40 hover:text-electric-cyan transition-colors text-sm"
                      >
                        {opt.icon} {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                {/* Pipeline Mode */}
                <div>
                  <label className="text-xs text-muted-silver uppercase tracking-wider mb-2 block">Pipeline Mode</label>
                  <div className="flex gap-2">
                    <button className="flex-1 px-3 py-2.5 rounded-lg bg-electric-cyan/10 border border-electric-cyan/30 text-electric-cyan text-sm font-medium">
                      Standard (8-stage)
                    </button>
                    <button className="flex-1 px-3 py-2.5 rounded-lg border border-steel-slate/30 text-muted-silver text-sm hover:border-steel-slate/50 transition-colors">
                      Agent-driven (5-stage)
                    </button>
                  </div>
                </div>
                {/* Use Agents Toggle */}
                <div className="flex items-center justify-between py-2">
                  <div>
                    <p className="text-sm text-ghost-white">Use AI Agents</p>
                    <p className="text-xs text-muted-silver">Enable agent-assisted processing</p>
                  </div>
                  <div className="w-10 h-5 rounded-full bg-electric-cyan/30 relative cursor-pointer">
                    <div className="absolute right-0.5 top-0.5 w-4 h-4 rounded-full bg-electric-cyan transition-transform" />
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 border-t border-steel-slate/30 flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowNewRun(false)}>Cancel</Button>
                <Button variant="primary" leftIcon={<Play size={14} />} onClick={() => { runPipelineMutation.mutate({}); setShowNewRun(false); }}>
                  Start Pipeline
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
