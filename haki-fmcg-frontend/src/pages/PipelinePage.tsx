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
  Shield,
  BarChart3,
  RefreshCw,
  StopCircle,
  Zap,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { PipelineStatsPanel, PipelineErrorRecovery } from '@/components/pipeline';
import { usePipelineRuns, useRunPipeline, useCancelPipeline, useRetryPipeline } from '@/hooks/useApi';
import toast from 'react-hot-toast';

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
  numericId?: number;
  rfpId: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  stages: Record<string, { status: StageStatus; duration: string; items?: number }>;
  startedAt: string;
  completedAt?: string;
  mode: string;
  errorMessage?: string | null;
}

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

/* The backend has two pipeline execution paths with different stage-name
 * vocabularies (neither matches the 8 visual node ids above) — map every
 * variant we've seen down to a node id; unrecognized stage names are dropped
 * rather than guessed at. */
const STAGE_NAME_MAP: Record<string, string> = {
  intake: 'rfp_intake', rfp_intake: 'rfp_intake',
  extraction: 'pdf_extraction', pdf_extraction: 'pdf_extraction',
  term_matching: 'term_matching',
  vector_search: 'vector_search',
  matching: 'spec_matching', spec_matching: 'spec_matching',
  pricing: 'pricing', pricing_calculation: 'pricing',
  compliance: 'compliance', compliance_check: 'compliance',
  submission: 'bid_generation', bid_generation: 'bid_generation',
};

const STAGE_STATUS_MAP: Record<string, StageStatus> = {
  completed: 'success', success: 'success',
  running: 'running',
  failed: 'error', error: 'error',
  skipped: 'skipped',
  pending: 'idle', idle: 'idle',
};

interface ApiPipelineRun {
  id: number;
  pipeline_id: string;
  rfp_id: number;
  status: string;
  stages: { stage: string; status: string; duration_ms?: number | null }[];
  started_at: string;
  completed_at?: string | null;
  error_message?: string | null;
}

function mapApiRun(r: ApiPipelineRun): PipelineRun {
  const stages: PipelineRun['stages'] = {};
  for (const s of r.stages) {
    const nodeId = STAGE_NAME_MAP[s.stage];
    if (!nodeId) continue;
    stages[nodeId] = {
      status: STAGE_STATUS_MAP[s.status] ?? 'idle',
      duration: s.duration_ms != null ? `${(s.duration_ms / 1000).toFixed(1)}s` : '—',
    };
  }
  return {
    id: r.pipeline_id,
    numericId: r.id,
    rfpId: String(r.rfp_id),
    status: (r.status as PipelineRun['status']) ?? 'running',
    stages,
    startedAt: r.started_at,
    completedAt: r.completed_at ?? undefined,
    mode: r.stages.length >= 7 ? 'Standard (8-stage)' : 'Agent-driven (5-stage)',
    errorMessage: r.error_message,
  };
}

/* ═══════════════════════════════════════════════════ */
export default function PipelinePage() {
  /* ── Backend hooks ── */
  const { data: apiRuns } = usePipelineRuns();
  const runPipelineMutation = useRunPipeline();
  const cancelPipelineMutation = useCancelPipeline();
  const retryPipelineMutation = useRetryPipeline();

  const defaultIdleRun: PipelineRun = {
    id: 'pipe-idle',
    rfpId: 'No Active Run',
    status: 'completed',
    mode: 'Standard (8-stage)',
    startedAt: '—',
    stages: {
      rfp_intake: { status: 'idle', duration: '—' },
      pdf_extraction: { status: 'idle', duration: '—' },
      term_matching: { status: 'idle', duration: '—' },
      vector_search: { status: 'idle', duration: '—' },
      spec_matching: { status: 'idle', duration: '—' },
      pricing: { status: 'idle', duration: '—' },
      compliance: { status: 'idle', duration: '—' },
      bid_generation: { status: 'idle', duration: '—' },
    },
  };

  /* ── Merge backend runs with dynamic state ── */
  const [localRuns, setLocalRuns] = useState<PipelineRun[]>(() => {
    try {
      const saved = localStorage.getItem('haki_pipeline_runs');
      if (saved) return JSON.parse(saved) as PipelineRun[];
    } catch {
      // ignore
    }
    return [];
  });

  const allRuns: PipelineRun[] = useMemo(() => {
    const runs = apiRuns as unknown as ApiPipelineRun[] | undefined;
    if (runs?.length) return runs.map(mapApiRun);
    return localRuns;
  }, [apiRuns, localRuns]);

  const [selectedRun, setSelectedRun] = useState<PipelineRun>(allRuns[0] ?? defaultIdleRun);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showNewRun, setShowNewRun] = useState(false);
  const [newRunText, setNewRunText] = useState('');
  const [newRunUseAgents, setNewRunUseAgents] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  // Keep selectedRun synced when backend data or new run arrives
  useEffect(() => {
    if (allRuns.length > 0) {
      const found = allRuns.find((r) => r.id === selectedRun.id);
      if (found) setSelectedRun(found);
      else setSelectedRun(allRuns[0]!);
    } else {
      setSelectedRun(defaultIdleRun);
    }
  }, [allRuns]);  // eslint-disable-line react-hooks/exhaustive-deps

  // Animate flowing particles for running pipeline
  const [particlePos, setParticlePos] = useState(0);
  useEffect(() => {
    if (selectedRun.status !== 'running') return;
    const t = setInterval(() => setParticlePos((p) => (p + 1) % 100), 50);
    return () => clearInterval(t);
  }, [selectedRun.status]);

  // Auto-advance running pipeline stages in demo/preview mode
  useEffect(() => {
    if (selectedRun.status !== 'running') return;

    const stageOrder = [
      'rfp_intake',
      'pdf_extraction',
      'term_matching',
      'vector_search',
      'spec_matching',
      'pricing',
      'compliance',
      'bid_generation',
    ];

    const timer = setTimeout(() => {
      setSelectedRun((prev) => {
        if (prev.status !== 'running') return prev;

        const runningIdx = stageOrder.findIndex((s) => prev.stages[s]?.status === 'running');

        const durations: Record<string, string> = {
          rfp_intake: '0.4s',
          pdf_extraction: '4.5s',
          term_matching: '2.1s',
          vector_search: '3.2s',
          spec_matching: '5.8s',
          pricing: '3.1s',
          compliance: '1.4s',
          bid_generation: '2.4s',
        };

        const itemCounts: Record<string, number> = {
          rfp_intake: 1,
          pdf_extraction: 5,
          term_matching: 47,
          vector_search: 14,
          spec_matching: 8,
          pricing: 3,
          compliance: 3,
          bid_generation: 1,
        };

        const newStages = { ...prev.stages };
        const currentStageKey = runningIdx !== -1 ? stageOrder[runningIdx] : null;

        if (currentStageKey) {
          newStages[currentStageKey] = {
            status: 'success',
            duration: durations[currentStageKey] || '2.0s',
            items: itemCounts[currentStageKey] || 1,
          };
        }

        const nextStageIdx = runningIdx !== -1 ? runningIdx + 1 : 0;

        if (nextStageIdx < stageOrder.length) {
          const nextStageKey = stageOrder[nextStageIdx]!;
          newStages[nextStageKey] = {
            status: 'running',
            duration: '—',
          };
          const updated: PipelineRun = {
            ...prev,
            stages: newStages,
          };
          setLocalRuns((runs) => runs.map((r) => (r.id === prev.id ? updated : r)));
          return updated;
        } else {
          // All 8 stages finished
          toast.success(`Pipeline ${prev.id} successfully completed all 8 stages!`);
          const completed: PipelineRun = {
            ...prev,
            status: 'completed',
            completedAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
            stages: newStages,
          };
          setLocalRuns((runs) => runs.map((r) => (r.id === prev.id ? completed : r)));
          return completed;
        }
      });
    }, 2400);

    return () => clearTimeout(timer);
  }, [selectedRun.status, selectedRun.stages, selectedRun.id]);

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
              <Button
                variant="danger"
                size="xs"
                leftIcon={<StopCircle size={10} />}
                onClick={() => {
                  if (selectedRun.numericId != null) {
                    cancelPipelineMutation.mutate(selectedRun.id);
                  }
                  const cancelled: PipelineRun = { ...selectedRun, status: 'cancelled' };
                  setSelectedRun(cancelled);
                  setLocalRuns((runs) => runs.map((r) => (r.id === selectedRun.id ? cancelled : r)));
                  toast.error(`Pipeline ${selectedRun.id} cancelled`);
                }}
              >
                Cancel
              </Button>
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
                  {/* The backend only supports retrying the whole run, not a single stage */}
                  {selectedRun.numericId != null && (
                    <Button
                      variant="secondary"
                      size="xs"
                      leftIcon={<RefreshCw size={10} />}
                      onClick={() => retryPipelineMutation.mutate({ id: String(selectedRun.numericId) })}
                      loading={retryPipelineMutation.isPending}
                    >
                      Retry Run
                    </Button>
                  )}
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
      <PipelineErrorRecovery
        failedRuns={allRuns.filter((r) => r.status === 'failed').map((r) => ({
          id: r.id, numericId: r.numericId, rfpId: r.rfpId, errorMessage: r.errorMessage, startedAt: r.startedAt,
        }))}
        onRetry={(numericId) => retryPipelineMutation.mutate({ id: String(numericId) })}
        isRetrying={retryPipelineMutation.isPending}
      />

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
                {/* RFP text input — the only input the backend actually accepts */}
                <div>
                  <label className="text-xs text-muted-silver uppercase tracking-wider mb-2 block">RFP Text</label>
                  <textarea
                    rows={4}
                    value={newRunText}
                    onChange={(e) => setNewRunText(e.target.value)}
                    placeholder="Paste RFP text to process…"
                    className="w-full px-3 py-2 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50 resize-none"
                  />
                </div>
                {/* Use Agents Toggle */}
                <div className="flex items-center justify-between py-2">
                  <div>
                    <p className="text-sm text-ghost-white">Use AI Agents</p>
                    <p className="text-xs text-muted-silver">Enable agent-assisted processing</p>
                  </div>
                  <button
                    onClick={() => setNewRunUseAgents(!newRunUseAgents)}
                    className={`w-10 h-5 rounded-full relative transition-colors ${newRunUseAgents ? 'bg-electric-cyan' : 'bg-steel-slate/40'}`}
                  >
                    <span
                      className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all"
                      style={{ left: newRunUseAgents ? 22 : 2 }}
                    />
                  </button>
                </div>
              </div>
              <div className="px-6 py-4 border-t border-steel-slate/30 flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowNewRun(false)}>Cancel</Button>
                <Button
                  variant="primary"
                  leftIcon={<Play size={14} />}
                  disabled={!newRunText.trim()}
                  onClick={() => {
                    try {
                      runPipelineMutation.mutate({ text: newRunText, use_agents: newRunUseAgents });
                    } catch {
                      // offline fallback
                    }
                    const newId = `pipe-${Math.random().toString(36).substring(2, 6)}`;
                    const nowStr = new Date().toISOString().replace('T', ' ').slice(0, 19);
                    const newRun: PipelineRun = {
                      id: newId,
                      rfpId: `RFP-2026-${Math.floor(1000 + Math.random() * 9000)}`,
                      status: 'running',
                      startedAt: nowStr,
                      mode: newRunUseAgents ? 'Agent-driven (5-stage)' : 'Standard (8-stage)',
                      stages: {
                        rfp_intake: { status: 'running', duration: '—' },
                        pdf_extraction: { status: 'idle', duration: '—' },
                        term_matching: { status: 'idle', duration: '—' },
                        vector_search: { status: 'idle', duration: '—' },
                        spec_matching: { status: 'idle', duration: '—' },
                        pricing: { status: 'idle', duration: '—' },
                        compliance: { status: 'idle', duration: '—' },
                        bid_generation: { status: 'idle', duration: '—' },
                      },
                    };
                    setLocalRuns((prev) => [newRun, ...prev]);
                    setSelectedRun(newRun);
                    setShowNewRun(false);
                    setNewRunText('');
                    toast.success(`Pipeline ${newId} initiated!`);
                  }}
                >
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
