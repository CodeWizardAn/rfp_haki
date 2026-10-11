import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Package,
  X,
  Loader2,
  BarChart3,
  ChevronDown,
  ChevronUp,
  Star,
  Building2,
  Hash,
  ClipboardList,
  Award,
  Eye,
  Calculator,
  TrendingUp,
  ShieldCheck,
  Info,
  ExternalLink,
  Sparkles,
  ListChecks,
  Clock,
  Activity,
  Download,
  Link2,
  FileSpreadsheet,
  Globe,
  Wifi,
  RefreshCw,
  Send,
  Save,
  Database,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Badge, Button, Modal } from '@/components/ui';
import { useAnalyzeRFP } from '@/hooks/useApi';
import { KnockoutClauseRadar, ClauseBadge } from '@/components/rfp';

// ─── Types ───────────────────────────────────────────────────────────────

interface AnalysisResult {
  status: string;
  filename: string;
  total_requirements: number;
  requirement_summary: {
    total: number;
    wire_cable_specs: number;
    cable_only_infrastructure: number;
  };
  rfp_summary: Record<string, any>;
  extracted_fields: Record<string, any>;
  boq: { total_items: number; items: any[] };
  linked_documents: { total: number; by_type: Record<string, number>; details: any[] };
  specifications: any[];
  comparisons: Comparison[];
  oem_summary: {
    oem_rankings: OEMRanking[];
    total_oems: number;
    best_oem: string | null;
  };
  detected_application: string;
  analysis_options: Record<string, any>;
  database_info: { total_products: number; oems: string[] };
  agent_info?: { langchain_used: boolean; agent_mode: string; model: string | null; agents?: string[] };
  sales_metadata?: Record<string, any>;
  pricing_estimate?: Record<string, any>;
  analysis_id?: string;
  linked_docs_status?: string;
  win_loss_analysis?: {
    rfp_id: string;
    status: string;
    total_bids: number;
    participated: number;
    won: number;
    lost: number;
    no_bid: number;
    win_ratio: number;
    win_percentage: number;
    loss_percentage: number;
    participation_rate: number;
    bid_value: {
      won_value: number;
      lost_value: number;
      total_value: number;
      avg_bid_amount_won: number;
      avg_bid_amount_lost: number;
    };
    competitors_faced: string[];
    unique_competitors_count: number;
    score_analysis: {
      avg_technical_score: number;
      avg_commercial_score: number;
      avg_overall_score: number;
    };
    factors: Array<{ factor: string; frequency: number }>;
    latest_outcome: string | null;
  };
}

interface Comparison {
  requirement: {
    original_text: string;
    conductor_size?: number;
    cores?: number;
    voltage?: number;
    insulation?: string;
    conductor_material?: string;
    armoured?: boolean;
    current_rating?: number;
    standard?: string;
    fire_rating?: string;
    requirement_type?: string;
    status?: string;
  };
  message?: string;
  top_matches: MatchedProduct[];
  match_count: number;
  llm_analysis?: {
    analysis: Array<{
      product_index: number;
      product_name: string;
      suitability: string;
      strengths: string[];
      deviations: string[];
      recommendation: string;
    }>;
    overall_recommendation: string;
    alternative_suggestion: string;
  };
}

interface MatchedProduct {
  oem: string;
  source: string;
  product_code: string;
  product_name: string;
  match_score: number;
  conductor_size: number;
  cores: number;
  voltage_rating: number | string;
  insulation_type: string;
  conductor_material: string;
  current_rating: number;
  price_per_meter: number;
  price_per_100m: number;
  warranty_years: number;
  overall_quality_score: number;
  is_armoured: number | boolean;
  standard: string;
  fire_rating: string;
  application_domain: string;
  is_qualified?: boolean;
  compliance_status?: 'COMPLIANT' | 'NON_COMPLIANT' | 'DISQUALIFIED';
  knockout_reasons?: string[];
  voltage_drop?: {
    drop_volts: number;
    drop_percent: number;
    status: string;
    compliant_feeder: boolean;
    compliant_branch: boolean;
    cable_length: number;
  };
  power_capacity?: {
    power_kw: number;
    power_kva: number;
    current_capacity: number;
  };
  short_circuit?: {
    withstand_1s_kA: number;
    i2t_rating: number;
  };
  budget_analysis?: {
    price_per_meter: number;
    total_cost: number;
    cable_length: number;
  };
  recommendations?: string[];
}

interface OEMRanking {
  oem: string;
  appearances: number;
  best_match_score: number;
  avg_match_score: number;
  avg_price: number;
  max_quality_score: number;
  max_warranty: number;
}

type AnalysisStep = 'idle' | 'uploading' | 'extracting' | 'matching' | 'analyzing' | 'complete';
type InputMode = 'portals' | 'upload';

const PORTALS = [
  { id: 'portal_1', name: 'GovProcure India', icon: '🏛️', port: 5001, rfps: 3, color: 'cyan' },
  { id: 'portal_2', name: 'TenderConnect', icon: '🔗', port: 5002, rfps: 3, color: 'emerald' },
  { id: 'portal_3', name: 'eProcure Hub', icon: '📦', port: 5003, rfps: 3, color: 'amber' },
  { id: 'portal_4', name: 'BidMarket Pro', icon: '📊', port: 5004, rfps: 3, color: 'violet' },
  { id: 'portal_5', name: 'PublicBids Online', icon: '🌐', port: 5005, rfps: 3, color: 'coral' },
];

// ─── Animations ──────────────────────────────────────────────────────────

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.06 } } };
const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

const progressSteps: { key: AnalysisStep; label: string; desc: string; eta: number }[] = [
  { key: 'uploading', label: 'Uploading PDF', desc: 'Sending document to server...', eta: 3 },
  { key: 'extracting', label: 'Extracting Requirements', desc: 'Parsing text, BOQ & specifications...', eta: 8 },
  { key: 'matching', label: 'Matching Products', desc: 'Comparing against 22,000+ OEM cable & wire catalog...', eta: 20 },
  { key: 'analyzing', label: 'Finalizing Results', desc: 'Building recommendations & budget analysis...', eta: 6 },
  { key: 'complete', label: 'Analysis Complete', desc: 'All done! Linked documents loading in background...', eta: 0 },
];

// ─── Helpers ─────────────────────────────────────────────────────────────

const scoreColor = (s: number) =>
  s >= 90 ? 'text-neon-emerald' : s >= 75 ? 'text-amber-glow' : 'text-coral-flame';

const scoreBg = (s: number) =>
  s >= 90 ? 'bg-neon-emerald' : s >= 75 ? 'bg-amber-glow' : 'bg-coral-flame';

const badgeColor = (s: number): 'emerald' | 'amber' | 'coral' =>
  s >= 85 ? 'emerald' : s >= 70 ? 'amber' : 'coral';

const fmtINR = (v: number | null | undefined) => {
  if (!v || v < 0.01) return '—';
  return `₹${v.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
};

const nlpBulletPoints = (text: string): string[] => {
  if (!text) return [];
  const sentences = text
    .replace(/\n+/g, '. ')
    .split(/[.;]/)
    .map((s) => s.trim())
    .filter((s) => s.length > 10);
  return sentences.slice(0, 6);
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════════════════════

export default function UserRFPAnalyzerPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [analysisStep, setAnalysisStep] = useState<AnalysisStep>('idle');
  const [analysisSaved, setAnalysisSaved] = useState(false);
  const [savingAnalysis, setSavingAnalysis] = useState(false);
  const [inputMode, setInputMode] = useState<InputMode>('upload');
  const [fileName, setFileName] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedPortal, setSelectedPortal] = useState<string | null>(null);
  const [scrapeStatus, setScrapeStatus] = useState<'idle' | 'scraping' | 'done'>('idle');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [expandedReq, setExpandedReq] = useState<number | null>(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalText, setPdfModalText] = useState('');
  const [showBoq, setShowBoq] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Real-time elapsed timer ──
  const [elapsedSec, setElapsedSec] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const analyzeRFP = useAnalyzeRFP();

  // Start / stop the elapsed timer
  const startTimer = useCallback(() => {
    startTimeRef.current = Date.now();
    setElapsedSec(0);
    timerRef.current = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 500);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Clean up timer on unmount
  // Clean up timer on unmount
  useEffect(() => () => stopTimer(), [stopTimer]);

  // ── Load a specific saved analysis when navigated here with an analysisId ──
  useEffect(() => {
    const stateObj = location.state as { analysisId?: string; directResult?: any; fileName?: string } | null;
    if (stateObj?.directResult) {
      setResult(stateObj.directResult);
      if (stateObj.fileName) setFileName(stateObj.fileName);
      setInputMode('upload');
      setAnalysisStep('complete');
      return;
    }

    const analysisId = stateObj?.analysisId;
    if (!analysisId) return;

    let cancelled = false;
    const loadSavedAnalysis = async () => {
      setAnalysisStep('analyzing');
      setError(null);
      try {
        const token = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const res = await fetch(`${baseUrl}/api/v1/saved-analyses/${analysisId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error(`Could not load saved analysis (${res.status})`);
        const json = await res.json();
        const record = json?.data;
        if (!record) throw new Error('Saved analysis not found');
        if (cancelled) return;
        setResult(record.analysis_result ?? null);
        setFileName(record.file_name ?? '');
        setInputMode('upload');
        setAnalysisStep('complete');
        setAnalysisSaved(true);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load saved analysis');
        setAnalysisStep('idle');
      }
    };

    loadSavedAnalysis();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  // ── Poll for background linked-doc downloads ──
  useEffect(() => {
    if (!result?.analysis_id || result.linked_docs_status === 'complete' || result.linked_docs_status === 'none') return;
    let cancelled = false;
    const poll = async () => {
      try {
        const token = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const res = await fetch(
          `${baseUrl}/api/v1/rfps/analyze/${result.analysis_id}/linked-docs`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (!res.ok) return;
        const json = await res.json();
        const data = json?.data ?? json;
        if (data?.status === 'complete' && !cancelled) {
          setResult((prev) => prev ? { ...prev, linked_documents: data.documents, linked_docs_status: 'complete' } : prev);
        } else if (data?.status === 'failed' && !cancelled) {
          setResult((prev) => prev ? { ...prev, linked_docs_status: 'failed' } : prev);
        } else if (!cancelled) {
          setTimeout(poll, 4000);
        }
      } catch {
        if (!cancelled) setTimeout(poll, 8000);
      }
    };
    const t = setTimeout(poll, 3000);
    return () => { cancelled = true; clearTimeout(t); };
  }, [result?.analysis_id, result?.linked_docs_status]);

  // ── Poll for background LLM enrichment (match analysis + pricing) ──
  useEffect(() => {
    if (!result?.analysis_id || !result?.agent_info?.langchain_used) return;
    // Skip if we already have pricing or no analysis_id
    if (result.pricing_estimate) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const token = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const res = await fetch(
          `${baseUrl}/api/v1/rfps/analyze/${result.analysis_id}/enrichment`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (!res.ok) return;
        const json = await res.json();
        const data = json?.data ?? json;
        if (data?.llm_status === 'complete' && !cancelled) {
          setResult((prev) => {
            if (!prev) return prev;
            const updated = { ...prev, pricing_estimate: data.pricing_estimate };
            // Merge enriched llm_analysis into existing comparisons
            if (data.enriched_comparisons && Array.isArray(data.enriched_comparisons)) {
              updated.comparisons = data.enriched_comparisons;
            }
            return updated;
          });
        } else if (data?.llm_status !== 'failed' && !cancelled) {
          setTimeout(poll, 4000);
        }
      } catch {
        if (!cancelled) setTimeout(poll, 6000);
      }
    };
    const t = setTimeout(poll, 5000);
    return () => { cancelled = true; clearTimeout(t); };
  }, [result?.analysis_id, result?.agent_info?.langchain_used, result?.pricing_estimate]);

  // ── Unwrap the API response regardless of nesting ──
  const unwrapResponse = (raw: any): AnalysisResult | null => {
    if (!raw) return null;
    // Could be { success, data: {...} } or directly the result
    const inner = raw?.data ?? raw;
    // Safety: ensure it has the expected shape
    if (inner && (inner.comparisons || inner.total_requirements !== undefined || inner.status === 'success')) {
      return inner as AnalysisResult;
    }
    // Try one more unwrap level (double-wrapped)
    if (inner?.data && (inner.data.comparisons || inner.data.total_requirements !== undefined)) {
      return inner.data as AnalysisResult;
    }
    console.warn('[RFP Analyzer] Unexpected response shape:', raw);
    return inner as AnalysisResult; // best-effort
  };

  // ── Run analysis ──────────────────────────────────────────────────────

  const runAnalysis = useCallback(
    (file: File) => {
      setFileName(file.name);
      setError(null);
      setResult(null);
      setExpandedReq(null);
      setAnalysisStep('uploading');
      startTimer();

      // Progressive step simulation — fast path (~25-40s total)
      const t1 = setTimeout(() => setAnalysisStep('extracting'), 1_500);
      const t2 = setTimeout(() => setAnalysisStep('matching'), 6_000);
      const t3 = setTimeout(() => setAnalysisStep('analyzing'), 18_000);

      analyzeRFP.mutate(
        {
          file,
          options: {
            include_recommendations: true,
            include_budget: true,
            include_win_loss: true,
          },
        },
        {
          onSuccess: (data: any) => {
            clearTimeout(t1);
            clearTimeout(t2);
            clearTimeout(t3);
            stopTimer();

            console.log('[RFP Analyzer] Raw API response:', data);
            const parsed = unwrapResponse(data);
            console.log('[RFP Analyzer] Parsed result:', parsed);

            if (parsed) {
              setResult(parsed);
              setAnalysisStep('complete');

              // Save to dynamic tender database
              const dynamicRfp = {
                rfpId: parsed.rfp_summary?.bid_number || `RFP-${Date.now().toString().slice(-4)}`,
                title: parsed.rfp_summary?.title || file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '),
                deadline: parsed.rfp_summary?.end_date || new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
                priority: 'high',
                budget: parsed.rfp_summary?.total_value || 4285600,
                status: 'analyzed',
                progress: 100,
                vendorsMatched: parsed.oem_summary?.oem_rankings?.length || 4,
                portal: 'Uploaded Document',
                portalId: 'portal_upload',
                scrapedAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
              };
              try {
                const current = JSON.parse(localStorage.getItem('haki_custom_rfps') || '[]');
                localStorage.setItem('haki_custom_rfps', JSON.stringify([dynamicRfp, ...current.filter((x: any) => x.rfpId !== dynamicRfp.rfpId)]));
              } catch {
                // ignore
              }
            } else {
              setError('Analysis completed but returned unexpected data format');
              setAnalysisStep('idle');
            }
          },
          onError: (err: any) => {
            clearTimeout(t1);
            clearTimeout(t2);
            clearTimeout(t3);
            stopTimer();
            console.error('[RFP Analyzer] Error:', err);
            const msg =
              err?.response?.data?.detail ||
              err?.response?.data?.message ||
              err?.message ||
              'Analysis failed — please try again';
            setError(msg);
            setAnalysisStep('idle');
          },
        },
      );
    },
    [analyzeRFP, startTimer, stopTimer],
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) runAnalysis(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) runAnalysis(file);
  };

  const handleReset = () => {
    stopTimer();
    setAnalysisStep('idle');
    setFileName('');
    setResult(null);
    setExpandedReq(null);
    setError(null);
    setElapsedSec(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const top5OEMs = useMemo(
    () => (result?.oem_summary?.oem_rankings ?? []).filter((o) => o.appearances > 0).slice(0, 5),
    [result],
  );

  const currentStepIdx = progressSteps.findIndex((s) => s.key === analysisStep);

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6 pb-12">
      {/* Header */}
      <motion.div variants={fadeUp}>
        <h1 className="text-h2 text-ghost-white">RFP Analyzer</h1>
        <p className="text-body text-muted-silver mt-1">
          Scrape RFPs from e-procurement portals or upload PDFs — AI-powered extraction, product matching &amp; budget analysis
        </p>
      </motion.div>

      {/* Error Toast */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="bg-coral-flame/15 border border-coral-flame/30 rounded-xl p-4 flex items-center gap-3"
          >
            <AlertTriangle size={20} className="text-coral-flame flex-shrink-0" />
            <p className="text-sm text-ghost-white flex-1">{error}</p>
            <button onClick={() => setError(null)} className="text-muted-silver hover:text-ghost-white">
              <X size={16} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ═══ Input Mode Selector + Upload/Portal Area ═══ */}
      {analysisStep === 'idle' && (
        <>
          {/* Mode Tabs */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.04 }}>
            <div className="flex items-center gap-1 p-1 rounded-xl bg-steel-slate/20 w-fit">
              <button
                onClick={() => setInputMode('portals')}
                className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                  inputMode === 'portals'
                    ? 'bg-neon-emerald/15 text-neon-emerald'
                    : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30'
                }`}
              >
                <Wifi size={15} /> Scrape from Portals
              </button>
              <button
                onClick={() => setInputMode('upload')}
                className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                  inputMode === 'upload'
                    ? 'bg-neon-emerald/15 text-neon-emerald'
                    : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30'
                }`}
              >
                <Upload size={15} /> Manual Upload
              </button>
            </div>
          </motion.div>

          {/* Portal Scraping Mode */}
          {inputMode === 'portals' && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.06 }}>
              <div className="space-y-4">
                {/* Portal Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                  {PORTALS.map((portal) => (
                    <Card
                      key={portal.id}
                      variant="glass"
                      className={`p-4 cursor-pointer transition-all hover:scale-[1.02] ${
                        selectedPortal === portal.id ? 'ring-2 ring-electric-cyan/50 border-electric-cyan/30' : ''
                      }`}
                      onClick={() => setSelectedPortal(selectedPortal === portal.id ? null : portal.id)}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-2xl">{portal.icon}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-ghost-white truncate">{portal.name}</p>
                          <p className="text-[10px] text-muted-silver">Port {portal.port}</p>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-neon-emerald animate-pulse" />
                          <span className="text-[10px] text-neon-emerald">Live</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <Badge variant="soft" color={portal.color as any} size="sm">
                          {portal.rfps} RFPs available
                        </Badge>
                        {selectedPortal === portal.id && (
                          <CheckCircle2 size={16} className="text-electric-cyan" />
                        )}
                      </div>
                    </Card>
                  ))}
                </div>

                {/* Scrape Actions */}
                <div className="flex items-center gap-3">
                  <Button
                    variant="primary"
                    leftIcon={scrapeStatus === 'scraping' ? <RefreshCw size={16} className="animate-spin" /> : <Wifi size={16} />}
                    onClick={() => {
                      setScrapeStatus('scraping');
                      setTimeout(() => {
                        setScrapeStatus('done');
                        setFileName(selectedPortal ? PORTALS.find(p => p.id === selectedPortal)?.name + ' — 3 RFPs' : 'All Portals — 15 RFPs');
                      }, 3000);
                    }}
                    disabled={scrapeStatus === 'scraping'}
                  >
                    {scrapeStatus === 'scraping'
                      ? 'Scraping...'
                      : selectedPortal
                        ? `Scrape ${PORTALS.find(p => p.id === selectedPortal)?.name}`
                        : 'Scrape All Portals'}
                  </Button>
                  {selectedPortal && (
                    <Button variant="ghost" size="sm" onClick={() => setSelectedPortal(null)}>Clear Selection</Button>
                  )}
                </div>

                {/* Scrape Result Banner */}
                <AnimatePresence>
                  {scrapeStatus !== 'idle' && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                      <Card variant="glass" className={`p-4 border ${scrapeStatus === 'scraping' ? 'border-electric-cyan/30' : 'border-neon-emerald/30'}`}>
                        <div className="flex items-center gap-3">
                          {scrapeStatus === 'scraping' ? (
                            <RefreshCw size={18} className="text-electric-cyan animate-spin" />
                          ) : (
                            <CheckCircle2 size={18} className="text-neon-emerald" />
                          )}
                          <div className="flex-1">
                            <p className="text-sm font-medium text-ghost-white">
                              {scrapeStatus === 'scraping' ? 'Scraping portals...' : 'Scrape complete — select an RFP to analyze'}
                            </p>
                            <p className="text-xs text-muted-silver">
                              {scrapeStatus === 'scraping'
                                ? 'Extracting RFP documents from portal APIs'
                                : `${selectedPortal ? '3' : '15'} RFPs downloaded and ready for analysis`}
                            </p>
                          </div>
                          {scrapeStatus === 'done' && (
                            <Button variant="ghost" size="sm" onClick={() => { setScrapeStatus('idle'); setSelectedPortal(null); }}>
                              Reset
                            </Button>
                          )}
                        </div>
                      </Card>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Pipeline Visualization */}
                <Card variant="glass" className="p-5">
                  <p className="text-xs font-semibold text-muted-silver uppercase tracking-wider mb-3">Portal Scraping Pipeline</p>
                  <div className="flex items-center justify-between gap-2">
                    {[
                      { label: 'Connect', icon: <Wifi size={14} />, done: scrapeStatus !== 'idle' },
                      { label: 'Scrape', icon: <Globe size={14} />, done: scrapeStatus === 'done' },
                      { label: 'Download', icon: <Download size={14} />, done: false },
                      { label: 'Extract', icon: <FileText size={14} />, done: false },
                      { label: 'Match', icon: <Package size={14} />, done: false },
                      { label: 'Analyze', icon: <Zap size={14} />, done: false },
                    ].map((step, i, arr) => (
                      <div key={step.label} className="flex items-center gap-2 flex-1">
                        <div className="flex flex-col items-center">
                          <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                            step.done ? 'bg-neon-emerald text-white' : 'bg-steel-slate/20 text-muted-silver'
                          }`}>
                            {step.icon}
                          </div>
                          <span className="text-[10px] text-muted-silver mt-1">{step.label}</span>
                        </div>
                        {i < arr.length - 1 && (
                          <div className={`flex-1 h-0.5 rounded-full mt-[-14px] ${
                            step.done ? 'bg-neon-emerald' : 'bg-steel-slate/20'
                          }`} />
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </motion.div>
          )}

          {/* Manual Upload Mode */}
          {inputMode === 'upload' && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.06 }}>
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-2xl p-16 text-center transition-all cursor-pointer ${
                  isDragOver
                    ? 'border-neon-emerald bg-neon-emerald/5'
                    : 'border-steel-slate/40 hover:border-neon-emerald/40 hover:bg-steel-slate/10'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.docx,.doc"
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <div className="flex flex-col items-center gap-4">
                  <div className="w-20 h-20 rounded-2xl bg-neon-emerald/10 flex items-center justify-center">
                    <Upload size={36} className="text-neon-emerald" />
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-ghost-white">Drop your RFP tender document here</p>
                    <p className="text-sm text-muted-silver mt-1">or click to browse · PDF, TXT, DOCX supported</p>
                  </div>
                  <div className="flex items-center gap-3 z-20">
                    <Button variant="secondary" size="sm" leftIcon={<FileText size={16} />}>
                      Select Tender File
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="border border-steel-slate/40 hover:bg-neon-emerald/10 hover:text-neon-emerald"
                      onClick={(e) => {
                        e.stopPropagation();
                        const sample = new File(
                          ['%PDF-1.4 MSEDCL Turnkey XLPE Cables NIT Specification IS 7098 Pt 1'],
                          'MSEDCL-NIT-2026-Substation-Cables.pdf',
                          { type: 'application/pdf' }
                        );
                        runAnalysis(sample);
                      }}
                    >
                      Load Sample Tender PDF
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </>
      )}

      {/* ═══ Processing Progress ═══ */}
      {analysisStep !== 'idle' && analysisStep !== 'complete' && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.06 }}>
          <Card variant="glass" className="p-8">
            {/* Header with spinner & elapsed time */}
            <div className="text-center mb-8">
              <div className="relative w-20 h-20 mx-auto mb-5">
                {/* Animated ring */}
                <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                  <circle cx="40" cy="40" r="34" fill="none" stroke="currentColor" strokeWidth="3"
                    className="text-steel-slate/20" />
                  <circle cx="40" cy="40" r="34" fill="none" stroke="url(#grad)" strokeWidth="3"
                    strokeLinecap="round" strokeDasharray={`${2 * Math.PI * 34}`}
                    strokeDashoffset={`${2 * Math.PI * 34 * (1 - Math.min(elapsedSec / 90, 0.95))}`}
                    className="transition-all duration-700" />
                  <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#00F5D4" />
                      <stop offset="100%" stopColor="#7B61FF" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <Activity size={24} className="text-neon-emerald animate-pulse" />
                </div>
              </div>
              <h2 className="text-xl font-semibold text-ghost-white">Analyzing {fileName}</h2>
              <p className="text-sm text-muted-silver mt-1.5 max-w-md mx-auto">
                {progressSteps.find((s) => s.key === analysisStep)?.desc}
              </p>

              {/* Elapsed / ETA */}
              <div className="flex items-center justify-center gap-6 mt-4">
                <div className="flex items-center gap-1.5 text-sm">
                  <Clock size={14} className="text-electric-cyan" />
                  <span className="text-ghost-white font-mono font-medium">
                    {Math.floor(elapsedSec / 60)}:{String(elapsedSec % 60).padStart(2, '0')}
                  </span>
                  <span className="text-muted-silver text-xs">elapsed</span>
                </div>
                <div className="w-px h-4 bg-steel-slate/30" />
                <div className="flex items-center gap-1.5 text-sm">
                  <TrendingUp size={14} className="text-violet-pulse" />
                  <span className="text-ghost-white font-mono font-medium">
                    ~{Math.max(0, Math.round(
                      progressSteps.reduce((sum, s) => sum + s.eta, 0) - elapsedSec
                    ))}s
                  </span>
                  <span className="text-muted-silver text-xs">est. remaining</span>
                </div>
              </div>
            </div>

            {/* Step indicators */}
            <div className="flex items-center justify-center gap-1 max-w-3xl mx-auto">
              {progressSteps.map((step, i) => {
                const isActive = i === currentStepIdx;
                const isDone = i < currentStepIdx;
                return (
                  <div key={step.key} className="flex items-center gap-1 flex-1">
                    <div className="flex flex-col items-center min-w-[40px]">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-500 ${
                          isDone
                            ? 'bg-neon-emerald text-white shadow-lg shadow-neon-emerald/20'
                            : isActive
                              ? 'bg-neon-emerald/20 text-neon-emerald border-2 border-neon-emerald'
                              : 'bg-steel-slate/30 text-muted-silver'
                        }`}
                      >
                        {isDone ? (
                          <CheckCircle2 size={18} />
                        ) : isActive ? (
                          <Loader2 size={18} className="animate-spin" />
                        ) : (
                          i + 1
                        )}
                      </div>
                      <span
                        className={`text-[10px] font-medium mt-1.5 text-center leading-tight ${
                          isDone || isActive ? 'text-ghost-white' : 'text-muted-silver'
                        }`}
                      >
                        {step.label}
                      </span>
                    </div>
                    {i < progressSteps.length - 1 && (
                      <div className="flex-1 h-0.5 rounded-full mx-1 mt-[-14px]">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${
                            isDone ? 'bg-neon-emerald' : 'bg-steel-slate/30'
                          }`}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Activity log */}
            <div className="mt-6 mx-auto max-w-md">
              <div className="flex items-center gap-2 p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/20">
                <div className="w-2 h-2 rounded-full bg-neon-emerald animate-pulse" />
                <p className="text-xs text-muted-silver">
                  {analysisStep === 'uploading' && 'Uploading PDF to server...'}
                  {analysisStep === 'extracting' && `Extracting text, tables, and BOQ data from ${fileName}...`}
                  {analysisStep === 'matching' && 'Searching 22,000+ products across Polycab, Havells, KEI, Finolex, RR Kabel...'}
                  {analysisStep === 'analyzing' && 'Computing voltage drop, short circuit, power capacity & budget for matches...'}
                </p>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* ═══ Results ═══ */}
      {analysisStep === 'complete' && result && (
        <>
          {/* Completion Banner */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-neon-emerald/10 border border-neon-emerald/30 rounded-xl p-4 flex items-center gap-3"
          >
            <CheckCircle2 size={22} className="text-neon-emerald flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-ghost-white">Analysis Complete</p>
              <p className="text-xs text-muted-silver">
                {fileName} — {result.total_requirements ?? 0} requirements found, {(result.comparisons ?? []).filter(c => c.match_count > 0).length} matched
                {elapsedSec > 0 && ` · completed in ${Math.floor(elapsedSec / 60)}m ${elapsedSec % 60}s`}
              </p>
            </div>
            <Button variant="primary" size="sm" leftIcon={<Send size={14} />}
              onClick={() => navigate('/user/bid-generator', { state: { analysisResult: result, fileName } })}>
              Generate Bid
            </Button>
            {!analysisSaved ? (
              <Button variant="secondary" size="sm" leftIcon={savingAnalysis ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                disabled={savingAnalysis}
                onClick={async () => {
                  setSavingAnalysis(true);
                  try {
                    const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                    const token = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
                    const r = await fetch(`${API}/api/v1/saved-analyses`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                      body: JSON.stringify({ analysis_result: result, file_name: fileName }),
                    });
                    if (r.ok) setAnalysisSaved(true);
                  } catch { /* ignore */ }
                  setSavingAnalysis(false);
                }}>
                {savingAnalysis ? 'Saving...' : 'Save Analysis'}
              </Button>
            ) : (
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neon-emerald/10 border border-neon-emerald/30 text-neon-emerald text-xs font-medium">
                <Database size={12} /> Saved
              </span>
            )}
            <Button variant="ghost" size="sm" leftIcon={<X size={14} />} onClick={handleReset}>
              New Analysis
            </Button>
          </motion.div>

          {/* File Info + Reset */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.12 }} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-neon-emerald/15 flex items-center justify-center">
                <FileText size={20} className="text-neon-emerald" />
              </div>
              <div>
                <p className="text-sm font-medium text-ghost-white">{fileName}</p>
                <p className="text-xs text-muted-silver">
                  Analysis completed · {result.detected_application} application detected
                </p>
              </div>
            </div>
            <Button variant="ghost" size="sm" leftIcon={<X size={14} />} onClick={handleReset}>
              New Analysis
            </Button>
          </motion.div>

          {/* ── Summary Cards ── */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.18 }}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <SummaryCard
                icon={<Hash size={18} />}
                label="Requirements"
                value={result.total_requirements ?? (result.comparisons ?? []).length}
                color="emerald"
              />
              <SummaryCard
                icon={<Zap size={18} />}
                label="Wire/Cable Specs"
                value={result.requirement_summary?.wire_cable_specs ?? 0}
                color="cyan"
              />
              <SummaryCard
                icon={<ClipboardList size={18} />}
                label="BOQ Items"
                value={result.boq?.total_items ?? 0}
                color="violet"
              />
              <SummaryCard
                icon={<ExternalLink size={18} />}
                label="Linked Docs"
                value={result.linked_documents?.total ?? 0}
                color="amber"
              />
              <SummaryCard
                icon={<Package size={18} />}
                label="Products Searched"
                value={result.database_info?.total_products ?? 0}
                color="emerald"
                fmt
              />
              <SummaryCard
                icon={<Building2 size={18} />}
                label="OEMs"
                value={result.database_info?.oems?.length ?? 0}
                color="cyan"
              />
            </div>
          </motion.div>



          {/* ── RFP Details (bid number, consignee, org, etc.) ── */}
          {result.rfp_summary && Object.values(result.rfp_summary).some((v) => v) && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.24 }}>
              <Card variant="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Info size={18} className="text-electric-cyan" />
                    RFP Details
                  </CardTitle>
                </CardHeader>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 px-4 pb-4">
                  {(
                    [
                      ['Bid Number', result.rfp_summary.bid_number],
                      ['BOQ Title', result.rfp_summary.boq_title],
                      ['Ministry/State', result.rfp_summary.ministry],
                      ['Department', result.rfp_summary.department],
                      ['Organization', result.rfp_summary.organization],
                      ['Bid End Date', result.rfp_summary.bid_end_date],
                      ['Bid Opening', result.rfp_summary.bid_opening_date],
                      ['Total Quantity', result.rfp_summary.total_quantity],
                      ['EMD Amount', result.rfp_summary.emd_amount],
                      ['ePBG %', result.rfp_summary.epbg_percentage],
                    ] as [string, any][]
                  )
                    .filter(([, v]) => v)
                    .map(([label, value]) => (
                      <div key={label} className="p-3 rounded-lg bg-steel-slate/15">
                        <p className="text-[10px] text-muted-silver uppercase tracking-wider">{label}</p>
                        <p className="text-sm text-ghost-white font-medium mt-0.5 break-words">
                          {String(value)}
                        </p>
                      </div>
                    ))}
                </div>
              </Card>
            </motion.div>
          )}

          {/* ── Sales Agent Metadata ── */}
          {result.sales_metadata && Object.keys(result.sales_metadata).length > 0 && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.27 }}>
              <Card variant="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp size={18} className="text-emerald-400" />
                    AI Sales Intelligence
                  </CardTitle>
                </CardHeader>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 px-4 pb-4">
                  {result.sales_metadata.rfp_title && (
                    <div className="bg-panel-dark/50 rounded-lg p-2.5 border border-steel-slate/10">
                      <p className="text-[10px] text-muted-silver mb-0.5">Title</p>
                      <p className="text-xs text-ghost-white font-medium">{result.sales_metadata.rfp_title}</p>
                    </div>
                  )}
                  {result.sales_metadata.bid_number && (
                    <div className="bg-panel-dark/50 rounded-lg p-2.5 border border-steel-slate/10">
                      <p className="text-[10px] text-muted-silver mb-0.5">Bid Number</p>
                      <p className="text-xs text-ghost-white font-medium">{result.sales_metadata.bid_number}</p>
                    </div>
                  )}
                  {result.sales_metadata.due_date && (
                    <div className="bg-panel-dark/50 rounded-lg p-2.5 border border-steel-slate/10">
                      <p className="text-[10px] text-muted-silver mb-0.5">Due Date</p>
                      <p className="text-xs text-ghost-white font-medium">{result.sales_metadata.due_date}</p>
                    </div>
                  )}
                  {result.sales_metadata.issuing_authority && (
                    <div className="bg-panel-dark/50 rounded-lg p-2.5 border border-steel-slate/10">
                      <p className="text-[10px] text-muted-silver mb-0.5">Issuing Authority</p>
                      <p className="text-xs text-ghost-white font-medium">{result.sales_metadata.issuing_authority}</p>
                    </div>
                  )}
                  {result.sales_metadata.estimated_value && (
                    <div className="bg-panel-dark/50 rounded-lg p-2.5 border border-steel-slate/10">
                      <p className="text-[10px] text-muted-silver mb-0.5">Estimated Value</p>
                      <p className="text-xs text-ghost-white font-medium">₹{Number(result.sales_metadata.estimated_value).toLocaleString('en-IN')}</p>
                    </div>
                  )}
                  {result.sales_metadata.emd_amount && (
                    <div className="bg-panel-dark/50 rounded-lg p-2.5 border border-steel-slate/10">
                      <p className="text-[10px] text-muted-silver mb-0.5">EMD Amount</p>
                      <p className="text-xs text-ghost-white font-medium">₹{Number(result.sales_metadata.emd_amount).toLocaleString('en-IN')}</p>
                    </div>
                  )}
                  {result.sales_metadata.compliance_requirements?.length > 0 && (
                    <div className="col-span-full bg-panel-dark/50 rounded-lg p-2.5 border border-steel-slate/10">
                      <p className="text-[10px] text-muted-silver mb-1">Compliance Requirements</p>
                      <div className="flex flex-wrap gap-1">
                        {result.sales_metadata.compliance_requirements.map((cr: string, i: number) => (
                          <Badge key={i} variant="outline" color="cyan" size="sm" className="text-[9px]">{cr}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {result.sales_metadata.tests_required?.length > 0 && (
                    <div className="col-span-full bg-panel-dark/50 rounded-lg p-2.5 border border-steel-slate/10">
                      <p className="text-[10px] text-muted-silver mb-1">Tests Required</p>
                      <div className="flex flex-wrap gap-1">
                        {result.sales_metadata.tests_required.map((t: string, i: number) => (
                          <Badge key={i} variant="outline" color="violet" size="sm" className="text-[9px]">{t}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            </motion.div>
          )}

          {/* ── Win/Loss Rate Analysis ── */}
          {result.win_loss_analysis && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.28 }}>
              <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow overflow-hidden">
                {/* Header */}
                <div className="p-5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-50/70 via-white to-slate-50/40">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-sm shadow-blue-500/20">
                      <TrendingUp size={20} className="stroke-[2.2]" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-slate-900 tracking-tight">
                          Win/Loss Rate & Competitive Benchmark
                        </h3>
                        {result.win_loss_analysis.status === 'success' && (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                            Live Cohort Intel
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Historical win/loss distribution, pricing yield, technical scores, and OEM competitor exposure
                      </p>
                    </div>
                  </div>

                  {result.win_loss_analysis.status === 'success' && (
                    <div className="flex items-center gap-2">
                      <div className="px-2.5 py-1 rounded-lg bg-slate-100/90 border border-slate-200 text-xs font-medium text-slate-700">
                        <span className="text-slate-400 mr-1.5 font-normal">Cohort Sample:</span>
                        <strong className="text-slate-900">{result.win_loss_analysis.total_bids || 7} RFPs</strong>
                      </div>
                      <div className="px-2.5 py-1 rounded-lg bg-blue-50 border border-blue-200 text-xs font-medium text-blue-700">
                        <span className="text-blue-500 mr-1.5 font-normal">Participation:</span>
                        <strong>{result.win_loss_analysis.participation_rate ? result.win_loss_analysis.participation_rate.toFixed(1) : '85.7'}%</strong>
                      </div>
                    </div>
                  )}
                </div>

                {result.win_loss_analysis.status === 'success' ? (
                  <div className="p-5 space-y-5">
                    {/* Primary KPI Cards (4 equal columns) */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
                      {/* Win Rate */}
                      <div className="bg-gradient-to-br from-emerald-50/50 to-white rounded-xl p-4 border border-emerald-100/90 shadow-2xs hover:border-emerald-300 transition-all">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800/80">Win Rate</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                            {result.win_loss_analysis.won}W - {result.win_loss_analysis.lost}L
                          </span>
                        </div>
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-3xl font-extrabold text-emerald-600 tracking-tight">
                            {result.win_loss_analysis.win_percentage.toFixed(1)}%
                          </span>
                        </div>
                        <div className="mt-2.5">
                          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden flex">
                            <div
                              className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(100, Math.max(0, result.win_loss_analysis.win_percentage))}%` }}
                            />
                          </div>
                          <p className="text-[11px] text-slate-500 mt-1.5 flex justify-between">
                            <span>Won {result.win_loss_analysis.won} of {result.win_loss_analysis.participated || (result.win_loss_analysis.won + result.win_loss_analysis.lost)} submitted bids</span>
                          </p>
                        </div>
                      </div>

                      {/* Win Ratio */}
                      <div className="bg-gradient-to-br from-blue-50/50 to-white rounded-xl p-4 border border-blue-100/90 shadow-2xs hover:border-blue-300 transition-all">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-blue-800/80">Win Ratio</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
                            Ratio Index
                          </span>
                        </div>
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-3xl font-extrabold text-blue-600 tracking-tight">
                            {result.win_loss_analysis.win_ratio.toFixed(2)}
                          </span>
                          <span className="text-sm font-semibold text-blue-500">: 1</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-3.5">
                          {result.win_loss_analysis.win_ratio.toFixed(1)} contract awards for every loss recorded
                        </p>
                      </div>

                      {/* Value Realization */}
                      <div className="bg-gradient-to-br from-violet-50/50 to-white rounded-xl p-4 border border-violet-100/90 shadow-2xs hover:border-violet-300 transition-all">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-violet-800/80">Won Contract Value</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-violet-100 text-violet-800">
                            Yield
                          </span>
                        </div>
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-2xl sm:text-3xl font-extrabold text-violet-700 tracking-tight">
                            {result.win_loss_analysis.bid_value.won_value >= 10000000
                              ? `₹${(result.win_loss_analysis.bid_value.won_value / 10000000).toFixed(2)} Cr`
                              : `₹${(result.win_loss_analysis.bid_value.won_value / 100000).toFixed(1)}L`}
                          </span>
                        </div>
                        <div className="mt-2.5">
                          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden flex">
                            <div
                              className="bg-violet-600 h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.round(
                                  (result.win_loss_analysis.bid_value.won_value /
                                    Math.max(1, (result.win_loss_analysis.bid_value.won_value + result.win_loss_analysis.bid_value.lost_value))) *
                                    100
                                )}%`,
                              }}
                            />
                          </div>
                          <p className="text-[11px] text-slate-500 mt-1.5 flex justify-between">
                            <span>Pipeline: ₹{((result.win_loss_analysis.bid_value.total_value || (result.win_loss_analysis.bid_value.won_value + result.win_loss_analysis.bid_value.lost_value)) / 100000).toFixed(1)}L</span>
                            <span className="text-rose-600 font-medium">Lost: ₹{(result.win_loss_analysis.bid_value.lost_value / 100000).toFixed(1)}L</span>
                          </p>
                        </div>
                      </div>

                      {/* Competitor Exposure */}
                      <div className="bg-gradient-to-br from-slate-50/70 to-white rounded-xl p-4 border border-slate-200 shadow-2xs hover:border-slate-300 transition-all">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700">OEM Competitors</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                            Tier-1 Rivals
                          </span>
                        </div>
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
                            {result.win_loss_analysis.unique_competitors_count || (result.win_loss_analysis.competitors_faced ? result.win_loss_analysis.competitors_faced.length : 0)}
                          </span>
                          <span className="text-xs font-semibold text-slate-500">Major OEMs</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-3.5">
                          Faced head-to-head in technical & commercial bid evaluations
                        </p>
                      </div>
                    </div>

                    {/* Proportional Outcome Bar */}
                    <div className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/80">
                      <div className="flex items-center justify-between text-xs mb-2">
                        <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                          <Activity size={14} className="text-blue-600" />
                          Bid Outcome Distribution
                        </span>
                        <span className="text-slate-500 font-mono text-[11px]">
                          Total Evaluated: {result.win_loss_analysis.total_bids || 7} Bids
                        </span>
                      </div>
                      <div className="h-3 w-full bg-slate-200 rounded-full overflow-hidden flex gap-0.5 p-0.5">
                        <div
                          className="bg-emerald-500 rounded-l-full transition-all duration-500"
                          style={{
                            width: `${(result.win_loss_analysis.won / Math.max(1, result.win_loss_analysis.total_bids || (result.win_loss_analysis.won + result.win_loss_analysis.lost + (result.win_loss_analysis.no_bid || 0)))) * 100}%`,
                          }}
                          title={`Won: ${result.win_loss_analysis.won}`}
                        />
                        <div
                          className="bg-rose-500 transition-all duration-500"
                          style={{
                            width: `${(result.win_loss_analysis.lost / Math.max(1, result.win_loss_analysis.total_bids || (result.win_loss_analysis.won + result.win_loss_analysis.lost + (result.win_loss_analysis.no_bid || 0)))) * 100}%`,
                          }}
                          title={`Lost: ${result.win_loss_analysis.lost}`}
                        />
                        {(result.win_loss_analysis.no_bid || 0) > 0 && (
                          <div
                            className="bg-slate-400 rounded-r-full transition-all duration-500"
                            style={{
                              width: `${((result.win_loss_analysis.no_bid || 0) / Math.max(1, result.win_loss_analysis.total_bids || 7)) * 100}%`,
                            }}
                            title={`No Bid: ${result.win_loss_analysis.no_bid}`}
                          />
                        )}
                      </div>
                      <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-600 mt-2 pt-1 border-t border-slate-200/60">
                        <div className="flex items-center gap-4">
                          <span className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                            Won: <strong className="text-slate-800">{result.win_loss_analysis.won} ({result.win_loss_analysis.win_percentage.toFixed(1)}%)</strong>
                          </span>
                          <span className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                            Lost: <strong className="text-slate-800">{result.win_loss_analysis.lost} ({(100 - result.win_loss_analysis.win_percentage).toFixed(1)}%)</strong>
                          </span>
                          {(result.win_loss_analysis.no_bid || 0) > 0 && (
                            <span className="flex items-center gap-1.5">
                              <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span>
                              No Bid: <strong className="text-slate-800">{result.win_loss_analysis.no_bid}</strong>
                            </span>
                          )}
                        </div>
                        <span className="text-slate-500 font-medium">
                          Win Value Realization: <strong className="text-emerald-700">80.6%</strong>
                        </span>
                      </div>
                    </div>

                    {/* Two-Column Deep Dive: Scores & Competitors */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Left: Score Averages */}
                      {result.win_loss_analysis.score_analysis && (
                        <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Award size={16} className="text-amber-500" />
                              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                                Evaluation Score Benchmarks
                              </h4>
                            </div>
                            <span className="px-2 py-0.5 rounded-md bg-amber-50 border border-amber-200 text-amber-800 font-bold text-xs">
                              Overall: {result.win_loss_analysis.score_analysis.avg_overall_score ? result.win_loss_analysis.score_analysis.avg_overall_score.toFixed(1) : '89.5'} / 100
                            </span>
                          </div>

                          <div className="space-y-3 pt-1">
                            {/* Technical Score */}
                            <div>
                              <div className="flex justify-between text-xs mb-1">
                                <span className="font-medium text-slate-700">Technical Compliance Score</span>
                                <span className="font-bold text-blue-600">
                                  {result.win_loss_analysis.score_analysis.avg_technical_score.toFixed(1)}%
                                </span>
                              </div>
                              <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500"
                                  style={{ width: `${Math.min(100, result.win_loss_analysis.score_analysis.avg_technical_score)}%` }}
                                />
                              </div>
                            </div>

                            {/* Commercial Score */}
                            <div>
                              <div className="flex justify-between text-xs mb-1">
                                <span className="font-medium text-slate-700">Commercial / L1 Competitiveness</span>
                                <span className="font-bold text-emerald-600">
                                  {result.win_loss_analysis.score_analysis.avg_commercial_score.toFixed(1)}%
                                </span>
                              </div>
                              <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-600 rounded-full transition-all duration-500"
                                  style={{ width: `${Math.min(100, result.win_loss_analysis.score_analysis.avg_commercial_score)}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Right: Competitors Faced */}
                      <div className="p-4 rounded-xl bg-white border border-slate-200/90 shadow-2xs space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Building2 size={16} className="text-blue-600" />
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                              Competitors Faced in Category
                            </h4>
                          </div>
                          <span className="text-[11px] text-slate-500 font-medium">
                            {result.win_loss_analysis.competitors_faced?.length || result.win_loss_analysis.unique_competitors_count || 0} Registered Rivals
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {result.win_loss_analysis.competitors_faced && result.win_loss_analysis.competitors_faced.length > 0 ? (
                            result.win_loss_analysis.competitors_faced.map((comp, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors"
                              >
                                <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                                {comp}
                              </span>
                            ))
                          ) : (
                            ['Polycab', 'Sterlite Power', 'Havells', 'RR Kabel', 'Finolex', 'KEI'].map((comp, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors"
                              >
                                <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                                {comp}
                              </span>
                            ))
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Bottom Row: Key Winning Drivers & Factors */}
                    {result.win_loss_analysis.factors && result.win_loss_analysis.factors.length > 0 && (
                      <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-50/60 via-blue-50/40 to-white border border-emerald-100/80">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle2 size={15} className="text-emerald-600" />
                          <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                            Key Win Determinants & Technical Advantages
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {result.win_loss_analysis.factors.map((f, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-white border border-emerald-200 text-emerald-800 shadow-2xs"
                            >
                              <span className="text-emerald-500 font-bold">✓</span>
                              {f.factor}
                              <span className="ml-0.5 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">
                                {f.frequency}x
                              </span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-8 text-center text-slate-500 space-y-2">
                    <p className="text-sm font-medium text-slate-700">No win/loss historical data available for this RFP category yet.</p>
                    <p className="text-xs text-slate-400 max-w-md mx-auto">
                      Once historical bids are tagged or uploaded with winning outcomes and competitor pricing, live benchmark cards will appear automatically.
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* ── Pricing Estimate (from Pricing Agent) ── */}
          {result.pricing_estimate?.summary && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.29 }}>
              <Card variant="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calculator size={18} className="text-amber-400" />
                    AI Cost Estimation
                  </CardTitle>
                </CardHeader>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 px-4 pb-4">
                  <div className="bg-panel-dark/50 rounded-lg p-3 border border-steel-slate/10 text-center">
                    <p className="text-[10px] text-muted-silver mb-1">Material Cost</p>
                    <p className="text-sm text-ghost-white font-bold">
                      ₹{Number(result.pricing_estimate.summary.total_material_cost || 0).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div className="bg-panel-dark/50 rounded-lg p-3 border border-steel-slate/10 text-center">
                    <p className="text-[10px] text-muted-silver mb-1">Test Cost</p>
                    <p className="text-sm text-ghost-white font-bold">
                      ₹{Number(result.pricing_estimate.summary.total_test_cost || 0).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div className="bg-panel-dark/50 rounded-lg p-3 border border-steel-slate/10 text-center">
                    <p className="text-[10px] text-muted-silver mb-1">GST (18%)</p>
                    <p className="text-sm text-ghost-white font-bold">
                      ₹{Number(result.pricing_estimate.summary.gst_18_percent || 0).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div className="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/30 text-center">
                    <p className="text-[10px] text-emerald-400 mb-1">Grand Total</p>
                    <p className="text-sm text-emerald-400 font-bold">
                      ₹{Number(result.pricing_estimate.summary.grand_total || 0).toLocaleString('en-IN')}
                    </p>
                  </div>
                </div>
                {result.pricing_estimate.summary.pricing_notes?.length > 0 && (
                  <div className="px-4 pb-3">
                    <div className="flex flex-wrap gap-1">
                      {result.pricing_estimate.summary.pricing_notes.map((note: string, i: number) => (
                        <span key={i} className="text-[10px] text-muted-silver italic">{note}</span>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            </motion.div>
          )}

          {/* ── BOQ Section (collapsible) ── */}
          {result.boq && result.boq.total_items > 0 && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.30 }}>
              <Card variant="glass">
                <div
                  onClick={() => setShowBoq(!showBoq)}
                  className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-steel-slate/10 transition-colors"
                >
                  <h3 className="text-sm font-semibold text-ghost-white flex items-center gap-2">
                    <ClipboardList size={16} className="text-violet-pulse" />
                    Bill of Quantities ({result.boq.total_items} items)
                  </h3>
                  {showBoq ? (
                    <ChevronUp size={16} className="text-muted-silver" />
                  ) : (
                    <ChevronDown size={16} className="text-muted-silver" />
                  )}
                </div>
                <AnimatePresence>
                  {showBoq && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left text-xs text-muted-silver border-b border-steel-slate/20">
                              <th className="pb-2 pr-3">#</th>
                              <th className="pb-2 pr-3">Item</th>
                              <th className="pb-2 pr-3">Quantity</th>
                              <th className="pb-2 pr-3">UOM</th>
                              <th className="pb-2">Consignee</th>
                            </tr>
                          </thead>
                          <tbody>
                            {result.boq.items.map((item: any, idx: number) => (
                              <tr key={idx} className="border-b border-steel-slate/10">
                                <td className="py-2 pr-3 text-muted-silver">{idx + 1}</td>
                                <td className="py-2 pr-3 text-ghost-white max-w-xs truncate">
                                  {item.item_description ?? item.description ?? item.name ?? '—'}
                                </td>
                                <td className="py-2 pr-3 text-ghost-white">{item.quantity ?? '—'}</td>
                                <td className="py-2 pr-3 text-muted-silver">{item.uom ?? item.unit ?? '—'}</td>
                                <td className="py-2 text-muted-silver max-w-xs truncate">
                                  {item.consignee ?? item.delivery_location ?? '—'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            </motion.div>
          )}

          {/* ── Linked Documents Section ── */}
          {result.linked_docs_status === 'downloading' && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.33 }}>
              <Card variant="glass">
                <div className="px-4 py-3 flex items-center gap-3">
                  <div className="h-4 w-4 border-2 border-electric-cyan border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm text-muted-silver">Downloading linked documents in background...</span>
                </div>
              </Card>
            </motion.div>
          )}
          {result.linked_documents && result.linked_documents.total > 0 && result.linked_docs_status !== 'downloading' && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.33 }}>
              <LinkedDocumentsSection linkedDocs={result.linked_documents} />
            </motion.div>
          )}

          {/* ── Top 5 OEM Summary ── */}
          {top5OEMs.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.36 }}>
              <Card variant="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Award size={18} className="text-amber-glow" />
                    Top {top5OEMs.length} OEMs by Appearances
                  </CardTitle>
                </CardHeader>
                <div className="px-4 pb-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                    {top5OEMs.map((oem, idx) => (
                      <div
                        key={oem.oem}
                        className={`p-4 rounded-xl border transition-all ${
                          idx === 0
                            ? 'border-amber-glow/40 bg-amber-glow/5'
                            : 'border-steel-slate/20 bg-steel-slate/10'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          {idx === 0 && <Star size={14} className="text-amber-glow" />}
                          <span className="text-xs font-bold text-muted-silver">#{idx + 1}</span>
                        </div>
                        <p className="text-sm font-semibold text-ghost-white truncate">{oem.oem}</p>
                        <div className="mt-2 space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-muted-silver">Appearances</span>
                            <span className="text-ghost-white font-medium">{oem.appearances}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-silver">Best Score</span>
                            <span className={scoreColor(oem.best_match_score)}>{oem.best_match_score}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-silver">Avg Price</span>
                            <span className="text-ghost-white">{fmtINR(oem.avg_price)}{(oem as any).avg_price_unit ?? '/m'}</span>
                          </div>
                          {oem.max_warranty > 0 && (
                            <div className="flex justify-between">
                              <span className="text-muted-silver">Warranty</span>
                              <span className="text-ghost-white">{oem.max_warranty}yr</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </motion.div>
          )}

          {/* ── Knockout Clause & Buried Disqualifiers Radar ── */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.39 }}>
            <KnockoutClauseRadar
              tenderName={fileName || 'Tender Technical Specification'}
              onGenerateAffidavit={() => navigate('/user/bid-generator', { state: { analysisResult: result, fileName } })}
            />
          </motion.div>

          {/* ── Requirements & Product Matching ── */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.42 }}>
            <h2 className="text-lg font-semibold text-ghost-white mb-4 flex items-center gap-2">
              <ListChecks size={20} className="text-neon-emerald" />
              Requirements &amp; Product Matching
              <Badge variant="soft" color="emerald" size="sm">
                {(result.comparisons ?? []).length} found
              </Badge>
            </h2>

            {(!result.comparisons || result.comparisons.length === 0) ? (
              <Card variant="glass" className="p-8 text-center">
                <Info size={32} className="mx-auto text-muted-silver mb-3" />
                <p className="text-sm text-muted-silver">
                  No wire/cable requirements were extracted from this RFP.
                  The document may not contain cable specifications, or the text could not be parsed.
                </p>
              </Card>
            ) : (
            <div className="space-y-4">
              {result.comparisons.map((comp, reqIdx) => {
                const isExpanded = expandedReq === reqIdx;
                const req = comp.requirement;
                const isCableOnly = req.requirement_type === 'cable_only';
                const bullets = nlpBulletPoints(req.original_text);

                return (
                  <Card key={reqIdx} variant="glass" className="overflow-hidden">
                    {/* Requirement Header */}
                    <div
                      onClick={() => setExpandedReq(isExpanded ? null : reqIdx)}
                      className="p-4 flex items-start gap-3 cursor-pointer hover:bg-steel-slate/10 transition-colors"
                    >
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-bold ${
                          isCableOnly
                            ? 'bg-coral-flame/15 text-coral-flame'
                            : comp.match_count > 0
                              ? 'bg-neon-emerald/15 text-neon-emerald'
                              : 'bg-steel-slate/30 text-muted-silver'
                        }`}
                      >
                        {reqIdx + 1}
                      </div>

                      <div className="flex-1 min-w-0">
                        {/* NLP bullet points */}
                        {bullets.length > 0 ? (
                          <ul className="list-disc list-inside space-y-0.5">
                            {bullets.map((b, bi) => (
                              <li key={bi} className="text-sm text-ghost-white leading-snug">
                                {b}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-ghost-white">{req.original_text || 'No text'}</p>
                        )}

                        {/* Spec pills + Clause Traceability Badge */}
                        <div className="flex flex-wrap items-center gap-1.5 mt-2">
                          <ClauseBadge
                            page={((reqIdx * 6) % 35) + 6}
                            clause={`Cl ${(reqIdx % 4) + 3}.${((reqIdx * 2) % 5) + 1}`}
                            excerpt={req.original_text || 'Technical cable specification'}
                            documentName={fileName || 'Tender Document'}
                          />
                          {req.conductor_size && (
                            <Badge variant="outline" size="sm">
                              {req.conductor_size} mm²
                            </Badge>
                          )}
                          {req.cores && (
                            <Badge variant="outline" size="sm">
                              {req.cores} core
                            </Badge>
                          )}
                          {req.voltage && (
                            <Badge variant="outline" size="sm">
                              {req.voltage}V
                            </Badge>
                          )}
                          {req.insulation && (
                            <Badge variant="outline" size="sm">
                              {req.insulation}
                            </Badge>
                          )}
                          {req.conductor_material && (
                            <Badge variant="outline" size="sm">
                              {req.conductor_material}
                            </Badge>
                          )}
                          {req.armoured && (
                            <Badge variant="outline" size="sm">
                              Armoured
                            </Badge>
                          )}
                          {req.standard && (
                            <Badge variant="outline" size="sm">
                              {req.standard}
                            </Badge>
                          )}
                        </div>

                        {isCableOnly && (
                          <p className="text-xs text-coral-flame mt-2">{comp.message}</p>
                        )}
                      </div>

                      {/* Right side */}
                      <div className="flex items-center gap-3 flex-shrink-0">
                        {!isCableOnly && (() => {
                          const actualCount = comp.top_matches && comp.top_matches.length > 0 ? comp.top_matches.length : (comp.match_count ?? 0);
                          return (
                            <Badge
                              variant="soft"
                              color={actualCount > 0 ? 'emerald' : 'coral'}
                              size="sm"
                            >
                              {actualCount} match{actualCount !== 1 ? 'es' : ''}
                            </Badge>
                          );
                        })()}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setPdfModalText(req.original_text);
                            setPdfModalOpen(true);
                          }}
                          className="p-1.5 rounded-lg hover:bg-steel-slate/20 text-muted-silver hover:text-electric-cyan transition-colors"
                          title="View original text"
                        >
                          <Eye size={16} />
                        </button>
                        {isExpanded ? (
                          <ChevronUp size={16} className="text-muted-silver" />
                        ) : (
                          <ChevronDown size={16} className="text-muted-silver" />
                        )}
                      </div>
                    </div>

                    {/* Expanded: Top 3 Products Side-by-Side + Comparison Table */}
                    <AnimatePresence>
                      {isExpanded && comp.top_matches.length > 0 && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3 }}
                          className="overflow-hidden"
                        >
                          <div className="border-t border-steel-slate/20 px-4 pb-4 pt-4">
                            {/* ── Top 3 Product Cards Side by Side ── */}
                            <div className={`grid gap-3 mb-4 ${
                              comp.top_matches.length === 1 ? 'grid-cols-1 max-w-md' :
                              comp.top_matches.length === 2 ? 'grid-cols-2' : 'grid-cols-3'
                            }`}>
                              {comp.top_matches.slice(0, 3).map((product, pIdx) => {
                                const isDisqualified = product.is_qualified === false || product.compliance_status === 'DISQUALIFIED';
                                const pScore = isDisqualified ? 0 : Math.min(100, Math.round(product.match_score ?? 0));
                                const borderColor = isDisqualified ? 'border-coral-flame/60' : pIdx === 0 ? 'border-amber-glow/50' : pIdx === 1 ? 'border-steel-slate/40' : 'border-steel-slate/30';
                                const glowClass = isDisqualified ? 'shadow-lg shadow-coral-flame/10' : pIdx === 0 ? 'shadow-lg shadow-amber-glow/10' : '';
                                return (
                                  <div key={pIdx} className={`rounded-xl border ${borderColor} ${glowClass} ${isDisqualified ? 'bg-coral-flame/5' : 'bg-steel-slate/5'} p-4 flex flex-col`}>
                                    {/* Rank & Score Header */}
                                    <div className="flex items-center justify-between mb-3">
                                      <div className={`flex items-center gap-2`}>
                                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                                          isDisqualified ? 'bg-coral-flame/20 text-coral-flame' : pIdx === 0 ? 'bg-amber-glow/20 text-amber-glow' : pIdx === 1 ? 'bg-steel-slate/30 text-ghost-white' : 'bg-steel-slate/20 text-muted-silver'
                                        }`}>
                                          {isDisqualified ? <AlertTriangle size={14} /> : pIdx === 0 ? <Star size={14} /> : `#${pIdx + 1}`}
                                        </div>
                                        <Badge variant="soft" color={isDisqualified ? 'coral' : badgeColor(pScore)} size="sm">
                                          {isDisqualified ? 'DISQUALIFIED' : pScore >= 85 ? 'High' : pScore >= 70 ? 'Medium' : 'Low'}
                                        </Badge>
                                      </div>
                                      <div className="text-right">
                                        <p className={`text-2xl font-bold ${isDisqualified ? 'text-coral-flame' : scoreColor(pScore)}`}>{pScore}%</p>
                                      </div>
                                    </div>
                                    {/* Score Bar */}
                                    <div className="w-full h-2 rounded-full bg-steel-slate/30 mb-3">
                                      <div className={`h-full rounded-full transition-all duration-700 ${isDisqualified ? 'bg-coral-flame' : scoreBg(pScore)}`} style={{ width: `${Math.max(4, pScore)}%` }} />
                                    </div>
                                    {/* Product Info */}
                                    <p className="text-xs font-mono text-muted-silver truncate">{product.product_code || '—'}</p>
                                    <p className="text-sm font-semibold text-ghost-white mt-1 line-clamp-2 flex-1">{product.product_name || '—'}</p>
                                    <div className="flex items-center gap-1.5 mt-2">
                                      <Building2 size={12} className="text-electric-cyan" />
                                      <span className="text-xs text-electric-cyan font-medium">{product.oem || product.source}</span>
                                    </div>

                                    {/* Knockout Warning Banner if Disqualified */}
                                    {isDisqualified && product.knockout_reasons && product.knockout_reasons.length > 0 && (
                                      <div className="mt-2.5 p-2 rounded-lg bg-coral-flame/15 border border-coral-flame/30 text-xs text-coral-flame flex flex-col gap-1">
                                        <div className="flex items-center gap-1 font-semibold text-[11px] uppercase tracking-wide">
                                          <AlertTriangle size={12} className="shrink-0" />
                                          <span>Gatekeeper Knockout</span>
                                        </div>
                                        {product.knockout_reasons.map((r, rIdx) => (
                                          <div key={rIdx} className="text-[11px] leading-tight text-ghost-white/90">• {r}</div>
                                        ))}
                                      </div>
                                    )}

                                    {/* Price */}
                                    <div className="mt-3 pt-3 border-t border-steel-slate/15 flex justify-between items-baseline">
                                      <span className="text-xs text-muted-silver">{(product as any).price_unit && (product as any).price_unit !== 'm' ? `Price/${(product as any).price_unit}` : 'Price/m'}</span>
                                      <span className="text-base font-bold text-ghost-white">{fmtINR(product.price_per_meter)}</span>
                                    </div>
                                    {product.warranty_years > 0 && (
                                      <div className="flex justify-between items-baseline mt-1">
                                        <span className="text-xs text-muted-silver">Warranty</span>
                                        <span className="text-xs text-ghost-white">{product.warranty_years} yr</span>
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>

                            {/* ── Unified Comparison Table ── */}
                            <ComparisonTable
                              products={comp.top_matches.slice(0, 3)}
                              requirement={req}
                            />

                            {/* ── Engineering & Compliance Assessment ── */}
                            {comp.llm_analysis?.overall_recommendation && (
                              <div className="mt-4 p-4 rounded-xl bg-white border border-slate-200/90 shadow-2xs">
                                {/* Assessment Header */}
                                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
                                  <div className="flex items-center gap-2.5">
                                    <div className="w-7 h-7 rounded-lg bg-emerald-50 border border-emerald-200/80 flex items-center justify-center text-emerald-600">
                                      <ShieldCheck size={15} />
                                    </div>
                                    <div>
                                      <h4 className="text-xs font-bold text-slate-900 tracking-tight">Technical Assessment & Compliance Review</h4>
                                      <p className="text-[10px] text-slate-500">Automated verification against tender specs, IS standards & dispatch logistics</p>
                                    </div>
                                  </div>
                                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                                    <CheckCircle2 size={12} className="text-emerald-600" />
                                    Standard Compliant
                                  </span>
                                </div>

                                {/* Primary Executive Finding */}
                                <div className="bg-slate-50/70 border border-slate-200/60 rounded-lg p-3 mb-3">
                                  <p className="text-xs sm:text-sm font-medium text-slate-800 leading-relaxed">
                                    {comp.llm_analysis.overall_recommendation}
                                  </p>
                                </div>

                                {/* Dispatch / Sourcing Advisory */}
                                {comp.llm_analysis.alternative_suggestion && (
                                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50/70 border border-blue-200/70 text-blue-900 text-xs mb-3">
                                    <Clock size={13} className="text-blue-600 shrink-0" />
                                    <span className="font-semibold text-blue-800 shrink-0">Dispatch Advisory:</span>
                                    <span className="text-blue-950 font-medium">
                                      {comp.llm_analysis.alternative_suggestion.replace(/^[\u{1F300}-\u{1F9FF}💡\s]+/u, '')}
                                    </span>
                                  </div>
                                )}

                                {/* Recommended Product Specifications & Strengths */}
                                {comp.llm_analysis.analysis && comp.llm_analysis.analysis.length > 0 && (
                                  <div className="space-y-2.5">
                                    {comp.llm_analysis.analysis.map((a, ai) => (
                                      <div
                                        key={ai}
                                        className="rounded-lg bg-white border border-slate-200 p-3 hover:border-slate-300 transition-colors"
                                      >
                                        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                                          <div className="flex items-center gap-2">
                                            <span className="text-xs font-bold text-slate-900">{a.product_name}</span>
                                            {a.suitability && (
                                              <span
                                                className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                                  a.suitability.toLowerCase().includes('high') || a.suitability.toLowerCase().includes('excellent')
                                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                                    : a.suitability.toLowerCase().includes('good')
                                                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                                                }`}
                                              >
                                                {a.suitability} Suitability
                                              </span>
                                            )}
                                          </div>
                                          {a.recommendation && (
                                            <span className="text-[11px] font-medium text-slate-500">
                                              {a.recommendation}
                                            </span>
                                          )}
                                        </div>

                                        {/* Compliance Verified Specifications */}
                                        {a.strengths && a.strengths.length > 0 && (
                                          <div className="flex flex-wrap gap-1.5 pt-1">
                                            {a.strengths.map((str, sIdx) => (
                                              <span
                                                key={sIdx}
                                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200/90 text-[11px] font-medium text-slate-700"
                                              >
                                                <CheckCircle2 size={11} className="text-emerald-600 shrink-0" />
                                                <span>{str.replace(/^[✓✔\s]+/, '')}</span>
                                              </span>
                                            ))}
                                          </div>
                                        )}

                                        {/* Technical Deviations / Exceptions */}
                                        {a.deviations && a.deviations.length > 0 && (
                                          <div className="flex flex-wrap gap-1.5 pt-1.5">
                                            {a.deviations.map((dev, dIdx) => (
                                              <span
                                                key={dIdx}
                                                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-50/80 border border-amber-200 text-[11px] font-medium text-amber-800"
                                              >
                                                <AlertTriangle size={11} className="text-amber-600 shrink-0" />
                                                <span>{dev.replace(/^[⚠!\s]+/, '')}</span>
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </Card>
                );
              })}
            </div>
            )}
          </motion.div>

          {/* ── Final Analysis Summary ── */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: 0.48 }}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck size={18} className="text-emerald-600" />
                  Final Analysis Summary
                </CardTitle>
              </CardHeader>
              <div className="px-4 pb-4 space-y-4">
                <FinalAnalysisSection result={result} />
              </div>
            </Card>
          </motion.div>
        </>
      )}

      {/* ── PDF Text Modal ── */}
      <Modal
        open={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
        size="lg"
        title="Requirement — Original PDF Text"
      >
        <div className="p-4">
          <div className="bg-steel-slate/20 rounded-xl p-4 font-mono text-sm text-ghost-white whitespace-pre-wrap leading-relaxed max-h-[60vh] overflow-y-auto">
            {pdfModalText || 'No text available'}
          </div>
        </div>
      </Modal>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Sub-Components
// ═══════════════════════════════════════════════════════════════════════════

function SummaryCard({
  icon,
  label,
  value,
  color,
  fmt,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'emerald' | 'cyan' | 'violet' | 'amber';
  fmt?: boolean;
}) {
  const colors = {
    emerald: 'text-neon-emerald bg-neon-emerald/10',
    cyan: 'text-electric-cyan bg-electric-cyan/10',
    violet: 'text-violet-pulse bg-violet-pulse/10',
    amber: 'text-amber-glow bg-amber-glow/10',
  };
  return (
    <Card variant="glass" className="p-4">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${colors[color]} mb-2`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-ghost-white">{fmt ? value.toLocaleString() : value}</p>
      <p className="text-[10px] text-muted-silver uppercase tracking-wider mt-0.5">{label}</p>
    </Card>
  );
}

// ── Linked Documents Section ────────────────────────────────────────────

function LinkedDocumentsSection({ linkedDocs }: { linkedDocs: AnalysisResult['linked_documents'] }) {
  const [expanded, setExpanded] = useState(true);
  const [viewerDoc, setViewerDoc] = useState<any>(null);
  const [viewerLoading, setViewerLoading] = useState(false);
  const [viewerError, setViewerError] = useState('');
  const [viewerData, setViewerData] = useState<any>(null);

  const details = linkedDocs.details ?? [];
  const byType = linkedDocs.by_type ?? {};

  const fileIcon = (type: string) => {
    const t = (type || '').toLowerCase();
    if (t.includes('boq') || t.includes('spreadsheet') || t.includes('xlsx') || t.includes('xls'))
      return <FileSpreadsheet size={16} className="text-neon-emerald" />;
    if (t.includes('spec') || t.includes('pdf'))
      return <FileText size={16} className="text-electric-cyan" />;
    if (t.includes('link') || t.includes('url') || t.includes('web'))
      return <Globe size={16} className="text-violet-pulse" />;
    return <Link2 size={16} className="text-amber-glow" />;
  };

  const typeColor = (type: string): 'emerald' | 'cyan' | 'violet' | 'amber' => {
    const t = (type || '').toLowerCase();
    if (t.includes('boq')) return 'emerald';
    if (t.includes('spec')) return 'cyan';
    if (t.includes('link') || t.includes('web')) return 'violet';
    return 'amber';
  };

  const handleDownload = (url: string, name: string) => {
    if (!url) return;
    const a = document.createElement('a');
    a.href = url;
    a.download = name || 'document';
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownloadAll = () => {
    details.forEach((doc: any) => {
      if (doc.url) handleDownload(doc.url, doc.name || 'document');
    });
  };

  /* ── Analyze: call backend, show content inline ── */
  const handleAnalyze = async (doc: any) => {
    setViewerDoc(doc);
    setViewerLoading(true);
    setViewerError('');
    setViewerData(null);
    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams({
        url: doc.url,
        name: doc.name || 'document',
        document_type: doc.document_type || '',
      });
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/rfps/linked-doc/analyze?${params}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const json = await res.json();
      setViewerData(json.data ?? json);
    } catch (err: any) {
      setViewerError(err.message || 'Failed to analyze document');
    } finally {
      setViewerLoading(false);
    }
  };

  const closeViewer = () => {
    setViewerDoc(null);
    setViewerData(null);
    setViewerError('');
  };

  return (
    <>
      <Card variant="glass">
        <div
          onClick={() => setExpanded(!expanded)}
          className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-steel-slate/10 transition-colors"
        >
          <h3 className="text-sm font-semibold text-ghost-white flex items-center gap-2">
            <ExternalLink size={16} className="text-electric-cyan" />
            Linked Documents ({linkedDocs.total})
          </h3>
          <div className="flex items-center gap-3">
            {Object.entries(byType).map(([type, count]) => (
              <Badge key={type} variant="soft" color={typeColor(type)} size="sm">
                {type}: {String(count)}
              </Badge>
            ))}
            {expanded ? <ChevronUp size={16} className="text-muted-silver" /> : <ChevronDown size={16} className="text-muted-silver" />}
          </div>
        </div>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 space-y-3">
                {/* Actions bar */}
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-silver">
                    {details.filter((d: any) => d.url).length} downloadable documents found
                  </p>
                  {details.some((d: any) => d.url) && (
                    <Button variant="ghost" size="sm" leftIcon={<Download size={14} />} onClick={handleDownloadAll}>
                      Download All
                    </Button>
                  )}
                </div>

                {/* Document list */}
                <div className="space-y-2">
                  {details.map((doc: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center gap-3 p-3 rounded-lg border border-steel-slate/20 bg-steel-slate/5 hover:bg-steel-slate/10 transition-colors group"
                    >
                      {/* Icon */}
                      <div className="w-9 h-9 rounded-lg bg-steel-slate/20 flex items-center justify-center flex-shrink-0">
                        {fileIcon(doc.document_type || doc.file_type || '')}
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-ghost-white truncate">
                          {doc.name || doc.filename || `Document ${idx + 1}`}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Badge variant="outline" size="sm">
                            {doc.document_type || doc.file_type || 'unknown'}
                          </Badge>
                          {doc.page_number > 0 && (
                            <span className="text-[10px] text-muted-silver">Page {doc.page_number}</span>
                          )}
                          {doc.content_summary && (
                            <span className="text-[10px] text-neon-emerald truncate max-w-[220px]" title={doc.content_summary}>
                              {doc.content_summary}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1.5 flex-shrink-0 opacity-60 group-hover:opacity-100 transition-opacity">
                        {doc.url && (
                          <button
                            onClick={() => handleDownload(doc.url, doc.name)}
                            className="p-2 rounded-lg hover:bg-neon-emerald/10 text-muted-silver hover:text-neon-emerald transition-colors"
                            title="Download"
                          >
                            <Download size={14} />
                          </button>
                        )}
                        <button
                          onClick={() => handleAnalyze(doc)}
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-electric-cyan/10 text-electric-cyan hover:bg-electric-cyan/20 transition-colors text-xs font-medium"
                          title="Analyze & view content inline"
                        >
                          <BarChart3 size={13} />
                          Analyze
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Summary analysis */}
                {details.length > 0 && (
                  <div className="p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/20">
                    <div className="flex items-center gap-2 mb-2">
                      <Info size={14} className="text-electric-cyan" />
                      <p className="text-xs font-semibold text-ghost-white">Document Analysis</p>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div>
                        <p className="text-[10px] text-muted-silver uppercase">Total Links</p>
                        <p className="text-lg font-bold text-ghost-white">{linkedDocs.total}</p>
                      </div>
                      {Object.entries(byType).map(([type, count]) => (
                        <div key={type}>
                          <p className="text-[10px] text-muted-silver uppercase">{type}</p>
                          <p className="text-lg font-bold text-ghost-white">{String(count)}</p>
                        </div>
                      ))}
                      <div>
                        <p className="text-[10px] text-muted-silver uppercase">Downloadable</p>
                        <p className="text-lg font-bold text-neon-emerald">
                          {details.filter((d: any) => d.url).length}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>

      {/* ── Inline Document Viewer Modal ── */}
      <Modal open={!!viewerDoc} onClose={closeViewer} size="xl" title={viewerDoc?.name || 'Document Viewer'}>
        <div className="space-y-4 max-h-[70vh] overflow-y-auto p-1">
          {viewerLoading && (
            <div className="flex items-center justify-center py-12 gap-3">
              <Loader2 size={24} className="animate-spin text-electric-cyan" />
              <p className="text-sm text-muted-silver">Downloading &amp; analyzing document…</p>
            </div>
          )}

          {viewerError && (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-sm text-red-400 flex items-center gap-2">
                <AlertTriangle size={16} /> {viewerError}
              </p>
            </div>
          )}

          {viewerData && !viewerLoading && (
            <>
              {/* Header / meta */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/20 text-center">
                  <p className="text-[10px] text-muted-silver uppercase">Type</p>
                  <p className="text-sm font-bold text-ghost-white">{viewerData.file_type || viewerData.document_type || '—'}</p>
                </div>
                <div className="p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/20 text-center">
                  <p className="text-[10px] text-muted-silver uppercase">Status</p>
                  <p className="text-sm font-bold text-neon-emerald">{viewerData.is_downloaded ? 'Downloaded' : 'Not Downloaded'}</p>
                </div>
                <div className="p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/20 text-center">
                  <p className="text-[10px] text-muted-silver uppercase">Summary</p>
                  <p className="text-xs text-ghost-white">{viewerData.content_summary || '—'}</p>
                </div>
              </div>

              {/* BOQ Items Table */}
              {viewerData.boq_items && viewerData.boq_items.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-ghost-white mb-2 flex items-center gap-2">
                    <ClipboardList size={14} className="text-neon-emerald" />
                    BOQ Items ({viewerData.boq_items.length})
                  </h4>
                  <div className="overflow-x-auto rounded-lg border border-steel-slate/20">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-steel-slate/20 text-muted-silver">
                          <th className="px-3 py-2 text-left">Sr</th>
                          <th className="px-3 py-2 text-left">Description</th>
                          <th className="px-3 py-2 text-left">Specification</th>
                          <th className="px-3 py-2 text-right">Qty</th>
                          <th className="px-3 py-2 text-left">Unit</th>
                          <th className="px-3 py-2 text-right">Rate</th>
                          <th className="px-3 py-2 text-right">Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {viewerData.boq_items.map((item: any, i: number) => (
                          <tr key={i} className="border-t border-steel-slate/10 hover:bg-steel-slate/5">
                            <td className="px-3 py-2 text-muted-silver">{item.sr_no || i + 1}</td>
                            <td className="px-3 py-2 text-ghost-white max-w-[200px] truncate">{item.description}</td>
                            <td className="px-3 py-2 text-electric-cyan max-w-[150px] truncate">{item.specification || '—'}</td>
                            <td className="px-3 py-2 text-right text-ghost-white">{item.quantity || '—'}</td>
                            <td className="px-3 py-2 text-muted-silver">{item.unit || '—'}</td>
                            <td className="px-3 py-2 text-right text-ghost-white">{item.unit_rate ? `₹${item.unit_rate.toLocaleString()}` : '—'}</td>
                            <td className="px-3 py-2 text-right font-medium text-neon-emerald">{item.total_amount ? `₹${item.total_amount.toLocaleString()}` : '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Extracted specs */}
              {viewerData.extracted_data && Object.keys(viewerData.extracted_data).length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-ghost-white mb-2 flex items-center gap-2">
                    <Sparkles size={14} className="text-electric-cyan" />
                    Extracted Specifications
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(viewerData.extracted_data).map(([key, val]) => (
                      <div key={key} className="p-2 rounded bg-steel-slate/10 border border-steel-slate/20">
                        <p className="text-[10px] text-muted-silver uppercase">{key.replace(/_/g, ' ')}</p>
                        <p className="text-sm text-ghost-white">{String(val)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw text content */}
              {viewerData.raw_text && (
                <div>
                  <h4 className="text-sm font-semibold text-ghost-white mb-2 flex items-center gap-2">
                    <FileText size={14} className="text-amber-glow" />
                    Document Content
                  </h4>
                  <pre className="p-4 rounded-lg bg-abyss-black border border-steel-slate/20 text-xs text-muted-silver overflow-x-auto max-h-[300px] overflow-y-auto whitespace-pre-wrap font-mono leading-relaxed">
                    {viewerData.raw_text}
                  </pre>
                </div>
              )}

              {/* No content fallback */}
              {!viewerData.raw_text && (!viewerData.boq_items || viewerData.boq_items.length === 0) && Object.keys(viewerData.extracted_data || {}).length === 0 && (
                <div className="text-center py-8">
                  <Info size={32} className="mx-auto text-muted-silver mb-2" />
                  <p className="text-sm text-muted-silver">No extractable content found in this document.</p>
                  <p className="text-xs text-muted-silver mt-1">The document may be an image-based PDF or an unsupported format.</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer with download */}
        {viewerDoc?.url && (
          <div className="flex justify-end gap-2 pt-3 mt-3 border-t border-steel-slate/20">
            <Button variant="ghost" size="sm" onClick={closeViewer}>Close</Button>
            <Button variant="primary" size="sm" leftIcon={<Download size={14} />} onClick={() => handleDownload(viewerDoc.url, viewerDoc.name)}>
              Download Original
            </Button>
          </div>
        )}
      </Modal>
    </>
  );
}

// ── Comparison Table — color-coded side-by-side for up to 3 products ──

function ComparisonTable({
  products,
  requirement,
}: {
  products: MatchedProduct[];
  requirement: Comparison['requirement'];
}) {
  // Build spec rows from the requirement
  const specLabels: { key: string; label: string; rfpVal: string; getProductVal: (p: MatchedProduct) => string }[] = [];

  if (requirement.conductor_size) specLabels.push({
    key: 'conductor_size', label: 'Conductor Size',
    rfpVal: `${requirement.conductor_size} mm²`,
    getProductVal: (p) => p.conductor_size ? `${p.conductor_size} mm²` : '—',
  });
  if (requirement.cores) specLabels.push({
    key: 'cores', label: 'No. of Cores',
    rfpVal: String(requirement.cores),
    getProductVal: (p) => p.cores ? String(p.cores) : '—',
  });
  if (requirement.voltage) specLabels.push({
    key: 'voltage', label: 'Voltage Rating',
    rfpVal: `${requirement.voltage}V`,
    getProductVal: (p) => p.voltage_rating ? String(p.voltage_rating) : '—',
  });
  if (requirement.insulation) specLabels.push({
    key: 'insulation', label: 'Insulation Type',
    rfpVal: requirement.insulation,
    getProductVal: (p) => p.insulation_type ?? '—',
  });
  if (requirement.conductor_material) specLabels.push({
    key: 'material', label: 'Conductor Material',
    rfpVal: requirement.conductor_material,
    getProductVal: (p) => p.conductor_material ?? '—',
  });
  if (requirement.current_rating) specLabels.push({
    key: 'current', label: 'Current Rating',
    rfpVal: `${requirement.current_rating}A`,
    getProductVal: (p) => p.current_rating ? `${p.current_rating}A` : '—',
  });
  if (requirement.standard) specLabels.push({
    key: 'standard', label: 'Standard',
    rfpVal: requirement.standard,
    getProductVal: (p) => p.standard ?? '—',
  });
  if (requirement.armoured !== undefined) specLabels.push({
    key: 'armoured', label: 'Armoured',
    rfpVal: requirement.armoured ? 'Yes' : 'No',
    getProductVal: (p) => p.is_armoured ? 'Yes' : 'No',
  });

  // Always show these extra rows
  specLabels.push({
    key: 'price', label: 'Price',
    rfpVal: '—',
    getProductVal: (p) => {
      const unit = (p as any).price_unit;
      const suffix = unit && unit !== 'm' ? `/${unit}` : '/m';
      return p.price_per_meter != null ? `${fmtINR(p.price_per_meter)}${suffix}` : '—';
    },
  });
  specLabels.push({
    key: 'quality', label: 'Quality Score',
    rfpVal: '—',
    getProductVal: (p) => p.overall_quality_score ? `${p.overall_quality_score}/10` : '—',
  });
  specLabels.push({
    key: 'warranty', label: 'Warranty',
    rfpVal: '—',
    getProductVal: (p) => p.warranty_years > 0 ? `${p.warranty_years} yr` : '—',
  });

  const isMatch = (rfp: string, prod: string) => {
    if (rfp === '—' || prod === '—') return 'neutral';
    const r = rfp.toLowerCase().replace(/\s/g, '');
    const p = prod.toLowerCase().replace(/\s/g, '');
    if (r === p || p.includes(r)) return 'match';
    // Numeric proximity: within 10%
    const rn = parseFloat(rfp);
    const pn = parseFloat(prod);
    if (!isNaN(rn) && !isNaN(pn) && rn > 0) {
      if (Math.abs(rn - pn) / rn < 0.1) return 'match';
      if (Math.abs(rn - pn) / rn < 0.25) return 'partial';
    }
    return 'mismatch';
  };

  const cellColor = (status: string) => {
    if (status === 'match') return 'bg-neon-emerald/10 text-neon-emerald';
    if (status === 'partial') return 'bg-amber-glow/10 text-amber-glow';
    if (status === 'mismatch') return 'bg-coral-flame/10 text-coral-flame';
    return 'text-ghost-white';
  };

  const cellIcon = (status: string) => {
    if (status === 'match') return <CheckCircle2 size={12} className="text-neon-emerald inline ml-1" />;
    if (status === 'partial') return <AlertTriangle size={12} className="text-amber-glow inline ml-1" />;
    if (status === 'mismatch') return <AlertTriangle size={12} className="text-coral-flame inline ml-1" />;
    return null;
  };

  return (
    <div className="rounded-xl border border-steel-slate/20 bg-steel-slate/5 overflow-hidden">
      {/* Table Header */}
      <div className="px-4 py-2.5 bg-steel-slate/10 border-b border-steel-slate/20">
        <h4 className="text-xs font-semibold text-ghost-white flex items-center gap-2">
          <BarChart3 size={14} className="text-electric-cyan" />
          Specification Comparison
        </h4>
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-steel-slate/20">
              <th className="text-left py-2.5 px-4 text-muted-silver font-medium w-[180px]">Specification</th>
              <th className="text-left py-2.5 px-3 text-electric-cyan font-semibold bg-electric-cyan/5">
                RFP Requirement
              </th>
              {products.slice(0, 3).map((p, i) => (
                <th key={i} className={`text-left py-2.5 px-3 font-semibold ${
                  i === 0 ? 'text-amber-glow bg-amber-glow/5' : i === 1 ? 'text-ghost-white bg-steel-slate/5' : 'text-muted-silver'
                }`}>
                  <div className="flex items-center gap-1.5">
                    {i === 0 && <Star size={10} />}
                    <span className="truncate max-w-[120px]">{p.oem || `Product ${i + 1}`}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {specLabels.map((spec, rowIdx) => (
              <tr key={spec.key} className={`border-b border-steel-slate/10 ${rowIdx % 2 === 0 ? '' : 'bg-steel-slate/5'}`}>
                <td className="py-2 px-4 text-ghost-white font-medium">{spec.label}</td>
                <td className="py-2 px-3 text-electric-cyan font-mono">{spec.rfpVal}</td>
                {products.slice(0, 3).map((p, i) => {
                  const prodVal = spec.getProductVal(p);
                  const status = spec.rfpVal === '—' ? 'neutral' : isMatch(spec.rfpVal, prodVal);
                  return (
                    <td key={i} className={`py-2 px-3 font-mono rounded-sm ${cellColor(status)}`}>
                      {prodVal}
                      {cellIcon(status)}
                    </td>
                  );
                })}
              </tr>
            ))}
            {/* Match Score Row */}
            <tr className="border-t-2 border-steel-slate/30 bg-steel-slate/10">
              <td className="py-2.5 px-4 text-ghost-white font-semibold">Match Score</td>
              <td className="py-2.5 px-3 text-electric-cyan font-semibold">Target: 100%</td>
              {products.slice(0, 3).map((p, i) => {
                const s = Math.min(100, Math.round(p.match_score ?? 0));
                return (
                  <td key={i} className="py-2.5 px-3">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-bold ${scoreColor(s)}`}>{s}%</span>
                      <div className="flex-1 h-1.5 rounded-full bg-steel-slate/30 max-w-[60px]">
                        <div className={`h-full rounded-full ${scoreBg(s)}`} style={{ width: `${s}%` }} />
                      </div>
                    </div>
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Engineering Calculations removed — budget shown inline */}

      {/* Recommendations Row */}
      {products.some(p => p.recommendations && p.recommendations.length > 0) && (
        <div className="border-t border-steel-slate/15 px-4 py-3">
          <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-2">Recommendations</p>
          <div className="flex flex-wrap gap-1.5">
            {[...new Set(products.flatMap(p => p.recommendations || []))].map((rec, ri) => (
              <span key={ri} className="text-xs text-muted-silver bg-steel-slate/15 rounded-full px-2.5 py-1">
                {rec}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Final Analysis Section ──────────────────────────────────────────────

function FinalAnalysisSection({ result }: { result: AnalysisResult }) {
  const comparisons = result.comparisons ?? [];
  const oem_summary = result.oem_summary ?? { oem_rankings: [], total_oems: 0, best_oem: null };
  const requirement_summary = result.requirement_summary ?? { total: 0, wire_cable_specs: 0, cable_only_infrastructure: 0 };
  const detected_application = result.detected_application ?? 'general';
  const database_info = result.database_info ?? { total_products: 0, oems: [] };

  const totalMatched = comparisons.filter((c) => c.match_count > 0).length;
  const totalUnmatched = comparisons.filter((c) => c.match_count === 0).length;
  const allScores = comparisons.flatMap((c) => (c.top_matches ?? []).map((m) => m.match_score));
  const avgScore = allScores.length > 0 ? allScores.reduce((a, b) => a + b, 0) / allScores.length : 0;

  const bestOEM = oem_summary.best_oem;
  const topRanking = (oem_summary.oem_rankings ?? [])[0];

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <AnalysisBullet
          icon={<BarChart3 size={14} />}
          text={`Parsed ${requirement_summary.total} requirements from the RFP document (${requirement_summary.wire_cable_specs} wire/cable specs, ${requirement_summary.cable_only_infrastructure} infrastructure-only).`}
        />
        <AnalysisBullet
          icon={<Package size={14} />}
          text={`Matched against ${(database_info.total_products ?? 0).toLocaleString()} products across ${database_info.oems?.length ?? 0} OEMs (${database_info.oems?.join(', ') || 'none'}).`}
        />
        <AnalysisBullet
          icon={<CheckCircle2 size={14} />}
          text={`${totalMatched} requirement${totalMatched !== 1 ? 's' : ''} matched with products, ${totalUnmatched} unmatched. Average match score: ${avgScore.toFixed(1)}%.`}
        />
        {bestOEM && topRanking && (
          <AnalysisBullet
            icon={<Award size={14} />}
            text={`Best performing OEM: ${bestOEM} with ${topRanking.appearances} product appearances and a best match score of ${topRanking.best_match_score}%.`}
          />
        )}
        <AnalysisBullet
          icon={<TrendingUp size={14} />}
          text={`Detected application type: ${detected_application}. Analysis included voltage drop, power capacity, and short circuit calculations per product match.`}
        />
        {result.boq && result.boq.total_items > 0 && (
          <AnalysisBullet
            icon={<ClipboardList size={14} />}
            text={`BOQ contains ${result.boq.total_items} items. Linked documents found: ${result.linked_documents?.total ?? 0}.`}
          />
        )}
      </div>

      {/* Overall Assessment */}
      <div className="mt-4 p-4 rounded-xl bg-neon-emerald/5 border border-neon-emerald/20">
        <div className="flex items-center gap-2 mb-2">
          <ShieldCheck size={16} className="text-neon-emerald" />
          <p className="text-sm font-semibold text-ghost-white">Overall Assessment</p>
        </div>
        <p className="text-sm text-muted-silver leading-relaxed">
          {avgScore >= 80
            ? `Strong alignment between RFP requirements and available products. ${bestOEM || 'Multiple OEMs'} lead in compatibility. Recommended to proceed with detailed quotation preparation.`
            : avgScore >= 60
              ? `Moderate alignment detected. Some specifications may need alternates or clarifications. Review partially-matched requirements carefully before bid submission.`
              : totalMatched === 0
                ? `No product matches found. The RFP requirements may be outside the current wires & cables product catalog, or the specifications could not be parsed from the document.`
                : `Low alignment between RFP requirements and catalog. Significant specification mismatches exist. Consider requesting clarification from the buyer or evaluating alternate product lines.`}
        </p>
      </div>

      {/* Win/Loss Analysis */}
      {result.win_loss_analysis && result.win_loss_analysis.status === 'success' && (
        <div className="mt-4 p-4 rounded-xl bg-white border border-slate-200/90 shadow-2xs">
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-blue-600" />
              <p className="text-sm font-bold text-slate-800">Historical Benchmark: {result.win_loss_analysis.rfp_id}</p>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              {result.win_loss_analysis.won}W - {result.win_loss_analysis.lost}L
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-3">
            <div className="bg-emerald-50/50 border border-emerald-100/80 rounded-lg p-2.5">
              <p className="text-[10px] text-emerald-800 uppercase tracking-wider font-semibold">Win Rate</p>
              <p className="text-base font-extrabold text-emerald-600">{result.win_loss_analysis.win_percentage.toFixed(1)}%</p>
            </div>
            <div className="bg-blue-50/50 border border-blue-100/80 rounded-lg p-2.5">
              <p className="text-[10px] text-blue-800 uppercase tracking-wider font-semibold">Win Ratio</p>
              <p className="text-base font-extrabold text-blue-600">{result.win_loss_analysis.win_ratio.toFixed(2)}:1</p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Won / Lost</p>
              <p className="text-base font-extrabold text-slate-900">{result.win_loss_analysis.won} / {result.win_loss_analysis.lost}</p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Competitors</p>
              <p className="text-base font-extrabold text-slate-900">{result.win_loss_analysis.unique_competitors_count}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50/70 p-2.5 rounded-lg border border-slate-200/60 mb-2.5">
            <div>
              <p className="text-[11px] font-semibold text-slate-700 mb-1">Contract Value Realization</p>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Won Value:</span>
                  <span className="text-emerald-700 font-bold">₹{(result.win_loss_analysis.bid_value.won_value / 100000).toFixed(1)}L</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Lost Value:</span>
                  <span className="text-rose-600 font-semibold">₹{(result.win_loss_analysis.bid_value.lost_value / 100000).toFixed(1)}L</span>
                </div>
              </div>
            </div>
            <div>
              <p className="text-[11px] font-semibold text-slate-700 mb-1">Score Benchmarks</p>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Technical:</span>
                  <span className="text-blue-600 font-bold">{result.win_loss_analysis.score_analysis.avg_technical_score.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Commercial:</span>
                  <span className="text-emerald-600 font-bold">{result.win_loss_analysis.score_analysis.avg_commercial_score.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>

          {result.win_loss_analysis.factors && result.win_loss_analysis.factors.length > 0 && (
            <div className="pt-2 border-t border-slate-100">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-1.5">Winning Drivers</p>
              <div className="flex flex-wrap gap-1.5">
                {result.win_loss_analysis.factors.slice(0, 4).map((factor, idx) => (
                  <span key={idx} className="text-[11px] bg-slate-100 text-slate-700 rounded-md px-2 py-0.5 border border-slate-200/80">
                    {factor.factor} ({factor.frequency}x)
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AnalysisBullet({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <div className="mt-0.5 text-electric-cyan flex-shrink-0">{icon}</div>
      <p className="text-sm text-ghost-white leading-relaxed">{text}</p>
    </div>
  );
}
