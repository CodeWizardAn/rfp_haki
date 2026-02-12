import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Eye,
  Play,
  ChevronDown,
  ChevronUp,
  Building2,
  Calendar,
  Hash,
  Globe,
  Wifi,
  RefreshCw,
  WifiOff,
  Save,
  Send,
  FileText,
  Zap,
  Database,
  BarChart3,
  ShieldCheck,
  Package,
  Award,
} from 'lucide-react';
import { Card, Badge, Button, Modal } from '@/components/ui';

/*  Types  */

type RFPStatus = 'scraped' | 'analyzing' | 'analyzed' | 'failed';

interface PortalRFP {
  rfp_id: string;
  filename: string;
  title: string;
  category: string;
  organization: string;
  publish_date: string;
  deadline: string;
  status: string;
  estimated_value: string;
  location: string;
  source_portal: string;
  source_portal_id: string;
  source_url: string;
  download_url: string;
  local_pdf_path?: string;
  scraped_at: string;
  analysis_saved?: boolean;
  saved_analysis_id?: string;
  _status?: RFPStatus;
  _analysis?: any;
  _analyzing?: boolean;
  _error?: string;
}

/*  Constants  */

const PORTALS = [
  { id: 'portal_1', name: 'GovProcure India', icon: '⚡', color: 'cyan' },
  { id: 'portal_2', name: 'TenderConnect', icon: '🔮', color: 'emerald' },
  { id: 'portal_3', name: 'eProcure Hub', icon: '🛡️', color: 'amber' },
  { id: 'portal_4', name: 'BidMarket Pro', icon: '💎', color: 'violet' },
  { id: 'portal_5', name: 'PublicBids Online', icon: '🚀', color: 'coral' },
];

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const hdrs = () => {
  const t = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` } as Record<string, string>;
};
const authOnly = () => {
  const t = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
  return { Authorization: `Bearer ${t}` } as Record<string, string>;
};
const fmtINR = (v: number | string | null | undefined) => {
  if (!v) return '\u2014';
  const n = typeof v === 'string' ? parseFloat(v.replace(/[^0-9.]/g, '')) : v;
  if (!n || n < 0.01) return '\u2014';
  return `\u20B9${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
};

const statusConfig: Record<RFPStatus, { icon: React.ReactNode; bg: string; text: string; label: string }> = {
  scraped: { icon: <Zap size={14} />, bg: 'bg-electric-cyan/15', text: 'text-electric-cyan', label: 'Scraped' },
  analyzing: { icon: <Loader2 size={14} className="animate-spin" />, bg: 'bg-amber-glow/15', text: 'text-amber-glow', label: 'Analyzing' },
  analyzed: { icon: <ShieldCheck size={14} />, bg: 'bg-neon-emerald/15', text: 'text-neon-emerald', label: 'Analyzed' },
  failed: { icon: <AlertTriangle size={14} />, bg: 'bg-coral-flame/15', text: 'text-coral-flame', label: 'Failed' },
};

const tabs: { key: RFPStatus | 'all'; label: string; emoji: string }[] = [
  { key: 'all', label: 'All', emoji: '🌐' },
  { key: 'scraped', label: 'Scraped', emoji: '📡' },
  { key: 'analyzing', label: 'Analyzing', emoji: '⚙️' },
  { key: 'analyzed', label: 'Analyzed', emoji: '✅' },
  { key: 'failed', label: 'Failed', emoji: '⛔' },
];

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

/* 
 *  Component
 *  */

export default function UserRFPProcessingPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<RFPStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'portal'>('date');
  const [portalFilter, setPortalFilter] = useState('all');

  const [scrapeStatus, setScrapeStatus] = useState<'idle' | 'scraping' | 'done'>('idle');
  const [scrapeInfo, setScrapeInfo] = useState<{ portals_done: number; total_rfps: number; errors: string[] } | null>(null);

  const [rfps, setRfps] = useState<PortalRFP[]>([]);
  const [loadingRfps, setLoadingRfps] = useState(true);

  const analyzingRef = useRef<Set<string>>(new Set());
  const [, forceUpdate] = useState(0);

  const [viewRfp, setViewRfp] = useState<PortalRFP | null>(null);
  const [saving, setSaving] = useState(false);

  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  useEffect(() => { if (toast) { const t = setTimeout(() => setToast(null), 4000); return () => clearTimeout(t); } }, [toast]);

  /*  Load scraped RFPs  */
  const loadRfps = useCallback(async () => {
    setLoadingRfps(true);
    try {
      const r = await fetch(`${API}/api/v1/portals/rfps`, { headers: hdrs() });
      if (r.ok) {
        const j = await r.json();
        const items: PortalRFP[] = (j.data ?? j ?? []).map((item: any) => ({
          ...item,
          _status: item.analysis_saved ? ('analyzed' as RFPStatus) : ('scraped' as RFPStatus),
        }));
        setRfps(items);
      }
    } catch { /* will show empty state */ }
    setLoadingRfps(false);
  }, []);

  useEffect(() => { loadRfps(); }, [loadRfps]);

  /*  Scrape all portals  */
  const handleScrapeAll = useCallback(async () => {
    setScrapeStatus('scraping');
    setScrapeInfo(null);
    try {
      await fetch(`${API}/api/v1/portals/scrape`, { method: 'POST', headers: hdrs() });
      const poll = async () => {
        try {
          const r = await fetch(`${API}/api/v1/portals/scrape/status`, { headers: hdrs() });
          if (!r.ok) return;
          const j = await r.json();
          const d = j.data ?? j;
          setScrapeInfo({ portals_done: d.portals_done ?? 0, total_rfps: d.total_rfps ?? 0, errors: d.errors ?? [] });
          if (d.running) { setTimeout(poll, 2000); }
          else { setScrapeStatus('done'); loadRfps(); }
        } catch { /* ignore */ }
      };
      setTimeout(poll, 2000);
    } catch {
      setScrapeStatus('idle');
      setToast({ type: 'error', msg: 'Failed to start scrape' });
    }
  }, [loadRfps]);

  /*  Analyze single RFP  */
  const handleAnalyze = useCallback(async (rfp: PortalRFP) => {
    if (analyzingRef.current.has(rfp.rfp_id)) return;
    analyzingRef.current.add(rfp.rfp_id);
    setRfps(prev => prev.map(r => r.rfp_id === rfp.rfp_id ? { ...r, _status: 'analyzing' as RFPStatus, _analyzing: true } : r));
    forceUpdate(n => n + 1);
    try {
      const pdfRes = await fetch(`${API}/api/v1/portals/rfps/${rfp.rfp_id}/pdf`, { headers: authOnly() });
      if (!pdfRes.ok) throw new Error('PDF not found \u2014 run scrape first');
      const pdfBlob = await pdfRes.blob();
      const pdfFile = new File([pdfBlob], rfp.filename || `${rfp.rfp_id}.pdf`, { type: 'application/pdf' });
      const formData = new FormData();
      formData.append('file', pdfFile);
      const token = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
      const analysisRes = await fetch(
        `${API}/api/v1/rfps/analyze?include_recommendations=true&include_budget=true`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: formData },
      );
      if (!analysisRes.ok) throw new Error(`Analysis failed (${analysisRes.status})`);
      const analysisJson = await analysisRes.json();
      const result = analysisJson.data ?? analysisJson;
      setRfps(prev => prev.map(r => r.rfp_id === rfp.rfp_id ? { ...r, _status: 'analyzed' as RFPStatus, _analyzing: false, _analysis: result } : r));
      setToast({ type: 'success', msg: `${rfp.rfp_id} analyzed \u2014 ${result.total_requirements ?? 0} requirements found` });
    } catch (err: any) {
      setRfps(prev => prev.map(r => r.rfp_id === rfp.rfp_id ? { ...r, _status: 'failed' as RFPStatus, _analyzing: false, _error: err.message } : r));
      setToast({ type: 'error', msg: `Analysis failed: ${err.message}` });
    } finally {
      analyzingRef.current.delete(rfp.rfp_id);
    }
  }, []);

  /*  Save analysis  */
  const handleSaveAnalysis = useCallback(async (rfp: PortalRFP) => {
    if (!rfp._analysis) return;
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/v1/saved-analyses`, {
        method: 'POST',
        headers: hdrs(),
        body: JSON.stringify({ analysis_result: rfp._analysis, file_name: rfp.filename || rfp.rfp_id }),
      });
      if (!r.ok) throw new Error('Save failed');
      setRfps(prev => prev.map(rr => rr.rfp_id === rfp.rfp_id ? { ...rr, analysis_saved: true } : rr));
      if (viewRfp?.rfp_id === rfp.rfp_id) setViewRfp(prev => prev ? { ...prev, analysis_saved: true } : null);
      setToast({ type: 'success', msg: 'Analysis saved \u2014 use it in Bid Generator' });
    } catch (err: any) {
      setToast({ type: 'error', msg: err.message });
    }
    setSaving(false);
  }, [viewRfp]);

  /*  Filtering  */
  const filtered = useMemo(() => {
    let list = [...rfps];
    if (activeTab !== 'all') list = list.filter(r => (r._status ?? 'scraped') === activeTab);
    if (portalFilter !== 'all') list = list.filter(r => r.source_portal_id === portalFilter);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(r =>
        r.rfp_id.toLowerCase().includes(q) ||
        (r.title ?? '').toLowerCase().includes(q) ||
        (r.organization ?? '').toLowerCase().includes(q) ||
        (r.source_portal ?? '').toLowerCase().includes(q)
      );
    }
    list.sort((a, b) => {
      if (sortBy === 'date') return new Date(b.scraped_at || 0).getTime() - new Date(a.scraped_at || 0).getTime();
      if (sortBy === 'portal') return (a.source_portal ?? '').localeCompare(b.source_portal ?? '');
      return (a.title ?? '').localeCompare(b.title ?? '');
    });
    return list;
  }, [rfps, activeTab, search, sortBy, portalFilter]);

  const counts = useMemo(() => ({
    all: rfps.length,
    scraped: rfps.filter(r => (r._status ?? 'scraped') === 'scraped').length,
    analyzing: rfps.filter(r => r._status === 'analyzing').length,
    analyzed: rfps.filter(r => r._status === 'analyzed').length,
    failed: rfps.filter(r => r._status === 'failed').length,
  }), [rfps]);

  /*  Render  */

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl border flex items-center gap-2 shadow-xl ${
              toast.type === 'success' ? 'bg-neon-emerald/15 border-neon-emerald/30' : 'bg-coral-flame/15 border-coral-flame/30'
            }`}>
            {toast.type === 'success' ? <CheckCircle2 size={16} className="text-neon-emerald" /> : <AlertTriangle size={16} className="text-coral-flame" />}
            <span className="text-sm text-ghost-white">{toast.msg}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <motion.div variants={fadeUp} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-h2 text-ghost-white">RFP Processing</h1>
          <p className="text-body text-muted-silver mt-1">Scrape portals, analyze RFPs inline, save &amp; generate bids</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="primary"
            leftIcon={scrapeStatus === 'scraping' ? <RefreshCw size={16} className="animate-spin" /> : <Wifi size={16} />}
            onClick={handleScrapeAll}
            disabled={scrapeStatus === 'scraping'}
          >
            {scrapeStatus === 'scraping' ? 'Scraping...' : 'Scrape All Portals'}
          </Button>
          <Button variant="secondary" leftIcon={<Globe size={16} />} onClick={() => navigate('/user/rfp-analyzer')}>
            Manual Analyzer
          </Button>
        </div>
      </motion.div>

      {/* Portal Filter Cards */}
      <motion.div variants={fadeUp} className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {PORTALS.map((portal) => {
          const portalCount = rfps.filter(r => r.source_portal_id === portal.id).length;
          return (
            <Card
              key={portal.id}
              variant="glass"
              className={`p-3 cursor-pointer transition-all hover:scale-[1.02] ${
                portalFilter === portal.id ? 'ring-2 ring-electric-cyan/50' : ''
              }`}
              onClick={() => setPortalFilter(portalFilter === portal.id ? 'all' : portal.id)}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-lg">{portal.icon}</span>
                <span className="text-xs font-medium text-ghost-white truncate">{portal.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <Badge variant="soft" color={portal.color as any} size="sm">
                  {portalCount} RFPs
                </Badge>
                {portalCount > 0 && (
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-neon-emerald animate-pulse" />
                    <span className="text-[10px] text-neon-emerald">Ready</span>
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </motion.div>

      {/* Status Tabs */}
      <motion.div variants={fadeUp} className="flex items-center gap-1 p-1 rounded-xl bg-steel-slate/20 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.key
                ? 'bg-neon-emerald/15 text-neon-emerald'
                : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30'
            }`}
          >
            <span className="mr-1">{tab.emoji}</span>
            {tab.label}
            <span className="ml-1.5 text-xs opacity-60">({counts[tab.key]})</span>
          </button>
        ))}
      </motion.div>

      {/* Search & Sort */}
      <motion.div variants={fadeUp} className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input
            type="text"
            placeholder="Search by RFP ID, title, portal, or organization..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/60 focus:outline-none focus:border-neon-emerald/40 transition-colors"
          />
        </div>
        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="glass-input pl-3 pr-8 py-2.5 rounded-xl text-sm text-ghost-white bg-transparent appearance-none cursor-pointer"
          >
            <option value="date">Sort by Date</option>
            <option value="title">Sort by Title</option>
            <option value="portal">Sort by Portal</option>
          </select>
          <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-silver pointer-events-none" />
        </div>
      </motion.div>

      {/* Scrape Status Banner */}
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
                    {scrapeStatus === 'scraping' ? 'Scraping portals...' : 'Scrape complete'}
                  </p>
                  <p className="text-xs text-muted-silver">
                    {scrapeStatus === 'scraping'
                      ? `${scrapeInfo?.portals_done ?? 0}/5 portals done \u00B7 ${scrapeInfo?.total_rfps ?? 0} RFPs found`
                      : `${scrapeInfo?.total_rfps ?? rfps.length} RFPs scraped from 5 portals${scrapeInfo?.errors?.length ? ` \u00B7 ${scrapeInfo.errors.length} errors` : ''}`}
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading */}
      {loadingRfps && rfps.length === 0 && (
        <motion.div variants={fadeUp} className="text-center py-12">
          <Loader2 size={32} className="mx-auto text-electric-cyan animate-spin mb-4" />
          <p className="text-sm text-muted-silver">Loading scraped RFPs...</p>
        </motion.div>
      )}

      {/* RFP List */}
      <motion.div variants={fadeUp} className="space-y-3">
        <AnimatePresence mode="popLayout">
          {filtered.map((rfp) => {
            const st = rfp._status ?? 'scraped';
            const sc = statusConfig[st];
            const analysis = rfp._analysis;
            return (
              <motion.div key={rfp.rfp_id} layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <Card variant="glass" className="hover:border-neon-emerald/20 transition-colors">
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2 flex-wrap">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${sc.bg} ${sc.text}`}>
                            {sc.icon} {sc.label}
                          </span>
                          <span className="text-xs text-muted-silver font-mono">{rfp.rfp_id}</span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-steel-slate/30 text-muted-silver">{rfp.category || 'General'}</span>
                          {rfp.analysis_saved && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-neon-emerald/15 text-neon-emerald flex items-center gap-1">
                              <Database size={10} /> Saved
                            </span>
                          )}
                        </div>
                        <h3 className="text-base font-semibold text-ghost-white truncate">{rfp.title || rfp.rfp_id}</h3>
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-silver flex-wrap">
                          <span className="flex items-center gap-1"><Building2 size={12} /> {rfp.organization || '\u2014'}</span>
                          <span className="flex items-center gap-1">{PORTALS.find(p => p.id === rfp.source_portal_id)?.icon ?? '\u{1F4C4}'} {rfp.source_portal}</span>
                          <span className="flex items-center gap-1"><Calendar size={12} /> Due: {rfp.deadline || '\u2014'}</span>
                          {rfp.estimated_value && <span className="flex items-center gap-1">{'\u{1F4B0}'} {rfp.estimated_value}</span>}
                        </div>
                        {st === 'analyzed' && analysis && (
                          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
                            <MiniStat icon={<Hash size={12} />} label="Requirements" value={String(analysis.total_requirements ?? 0)} />
                            <MiniStat icon={<Package size={12} />} label="Matched" value={String((analysis.comparisons ?? []).filter((c: any) => c.match_count > 0).length)} />
                            <MiniStat icon={<BarChart3 size={12} />} label="Products" value={String((analysis.database_info?.total_products ?? 0).toLocaleString())} />
                            <MiniStat icon={<Zap size={12} />} label="Application" value={analysis.detected_application || '\u2014'} />
                          </div>
                        )}
                        {st === 'failed' && rfp._error && (
                          <p className="mt-2 text-xs text-coral-flame">{rfp._error}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {st === 'scraped' && (
                          <Button variant="primary" size="sm" leftIcon={<Play size={14} />}
                            onClick={(e: React.MouseEvent) => { e.stopPropagation(); handleAnalyze(rfp); }}>
                            Analyze
                          </Button>
                        )}
                        {st === 'analyzing' && (
                          <div className="flex items-center gap-2">
                            <Loader2 size={16} className="text-amber-glow animate-spin" />
                            <span className="text-xs text-amber-glow">Analyzing...</span>
                          </div>
                        )}
                        {st === 'analyzed' && (
                          <div className="flex items-center gap-2">
                            {!rfp.analysis_saved && (
                              <Button variant="secondary" size="sm" leftIcon={<Save size={14} />}
                                onClick={(e: React.MouseEvent) => { e.stopPropagation(); handleSaveAnalysis(rfp); }}>
                                Save
                              </Button>
                            )}
                            <Button variant="ghost" size="sm" leftIcon={<Eye size={14} />}
                              onClick={(e: React.MouseEvent) => { e.stopPropagation(); setViewRfp(rfp); }}>
                              View
                            </Button>
                            <Button variant="primary" size="sm" leftIcon={<Send size={14} />}
                              onClick={(e: React.MouseEvent) => { e.stopPropagation(); navigate('/user/bid-generator', { state: { analysisResult: rfp._analysis, fileName: rfp.filename || rfp.rfp_id } }); }}>
                              Bid
                            </Button>
                          </div>
                        )}
                        {st === 'failed' && (
                          <Button variant="ghost" size="sm" leftIcon={<RefreshCw size={14} />}
                            onClick={(e: React.MouseEvent) => { e.stopPropagation(); handleAnalyze(rfp); }}>
                            Retry
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {!loadingRfps && filtered.length === 0 && (
          <div className="text-center py-12">
            <WifiOff size={48} className="mx-auto text-steel-slate/40 mb-4" />
            <p className="text-muted-silver">
              {rfps.length === 0 ? 'No RFPs scraped yet \u2014 click "Scrape All Portals" to start' : 'No RFPs match your filters'}
            </p>
            {rfps.length === 0 && (
              <Button variant="primary" size="sm" className="mt-4" leftIcon={<Wifi size={14} />} onClick={handleScrapeAll}>
                Scrape Now
              </Button>
            )}
          </div>
        )}
      </motion.div>

      {/* Analysis Detail Modal */}
      {viewRfp && viewRfp._analysis && (
        <Modal open={!!viewRfp} onClose={() => setViewRfp(null)} title="" size="full">
          <AnalysisDetailView
            rfp={viewRfp}
            analysis={viewRfp._analysis}
            onSave={() => handleSaveAnalysis(viewRfp)}
            onBid={() => { setViewRfp(null); navigate('/user/bid-generator', { state: { analysisResult: viewRfp._analysis, fileName: viewRfp.filename || viewRfp.rfp_id } }); }}
            saving={saving}
            saved={viewRfp.analysis_saved ?? false}
          />
        </Modal>
      )}
    </motion.div>
  );
}

/*  Sub-components  */

function MiniStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-steel-slate/10 border border-steel-slate/15">
      <span className="text-electric-cyan">{icon}</span>
      <div className="min-w-0">
        <p className="text-[10px] text-muted-silver leading-none">{label}</p>
        <p className="text-xs font-bold text-ghost-white truncate">{value}</p>
      </div>
    </div>
  );
}

function AnalysisDetailView({
  rfp, analysis, onSave, onBid, saving, saved,
}: {
  rfp: PortalRFP; analysis: any; onSave: () => void; onBid: () => void; saving: boolean; saved: boolean;
}) {
  const [showComps, setShowComps] = useState(true);
  const comparisons: any[] = analysis.comparisons ?? [];
  const matched = comparisons.filter((c: any) => c.match_count > 0);
  const rfpSummary = analysis.rfp_summary ?? {};
  const oem = analysis.oem_summary ?? {};
  const reqSummary = analysis.requirement_summary ?? {};

  return (
    <div className="max-w-5xl mx-auto space-y-6 text-ghost-white">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 border-b border-steel-slate/20 pb-4">
        <div>
          <h2 className="text-xl font-bold text-ghost-white">{rfp.title || rfp.rfp_id}</h2>
          <p className="text-xs text-muted-silver mt-1">
            {rfp.organization} \u00B7 {rfp.source_portal} \u00B7 Scraped {rfp.scraped_at ? new Date(rfp.scraped_at).toLocaleString() : '\u2014'}
          </p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          {!saved && (
            <button onClick={onSave} disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-glow/10 border border-amber-glow/30 text-amber-glow text-sm font-medium hover:bg-amber-glow/20 transition-colors disabled:opacity-50">
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              {saving ? 'Saving...' : 'Save Analysis'}
            </button>
          )}
          {saved && (
            <span className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neon-emerald/10 border border-neon-emerald/30 text-neon-emerald text-sm font-medium">
              <CheckCircle2 size={14} /> Saved
            </span>
          )}
          <button onClick={onBid}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-electric-cyan/10 border border-electric-cyan/30 text-electric-cyan text-sm font-medium hover:bg-electric-cyan/20 transition-colors">
            <Send size={14} /> Generate Bid
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <SummaryCard icon={<Hash size={16} />} label="Requirements" value={String(analysis.total_requirements ?? 0)} color="cyan" />
        <SummaryCard icon={<Package size={16} />} label="Matched" value={String(matched.length)} color="emerald" />
        <SummaryCard icon={<ShieldCheck size={16} />} label="Cable Specs" value={String(reqSummary.wire_cable_specs ?? 0)} color="violet" />
        <SummaryCard icon={<Zap size={16} />} label="Application" value={analysis.detected_application || '\u2014'} color="amber" />
        <SummaryCard icon={<Database size={16} />} label="DB Products" value={String((analysis.database_info?.total_products ?? 0).toLocaleString())} color="cyan" />
        <SummaryCard icon={<Award size={16} />} label="Best OEM" value={oem.best_oem || '\u2014'} color="emerald" />
      </div>

      {/* RFP Details */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4 rounded-xl bg-steel-slate/10 border border-steel-slate/20">
        <KV label="Bid Number" value={rfpSummary.bid_number || '\u2014'} />
        <KV label="Organization" value={rfpSummary.organization || rfp.organization || '\u2014'} />
        <KV label="Ministry / Dept" value={`${rfpSummary.ministry || '\u2014'} / ${rfpSummary.department || '\u2014'}`} />
        <KV label="Due Date" value={rfpSummary.bid_end_date || rfp.deadline || '\u2014'} />
        <KV label="EMD Amount" value={rfpSummary.emd_amount || '\u2014'} />
        <KV label="Estimated Value" value={rfp.estimated_value || '\u2014'} />
      </div>

      {/* OEM Rankings */}
      {oem.oem_rankings?.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-ghost-white mb-3 flex items-center gap-2">
            <Award size={16} className="text-amber-glow" />
            OEM Rankings ({oem.total_oems} manufacturers)
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {(oem.oem_rankings as any[]).slice(0, 5).map((r: any, i: number) => (
              <div key={r.oem} className={`p-3 rounded-xl border text-center ${i === 0 ? 'border-neon-emerald/30 bg-neon-emerald/5' : 'border-steel-slate/20 bg-steel-slate/10'}`}>
                <p className="text-[10px] text-muted-silver">#{i + 1}</p>
                <p className="text-sm font-bold text-electric-cyan truncate">{r.oem}</p>
                <p className="text-[10px] text-muted-silver">{r.product_count} products \u00B7 {r.average_score?.toFixed(0)}%</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comparisons */}
      <div>
        <div onClick={() => setShowComps(!showComps)}
          className="flex items-center justify-between cursor-pointer p-3 rounded-xl bg-steel-slate/10 border border-steel-slate/20 hover:bg-steel-slate/15 transition-colors">
          <h3 className="text-sm font-semibold text-ghost-white flex items-center gap-2">
            <FileText size={16} className="text-electric-cyan" />
            Requirement Comparisons ({comparisons.length})
          </h3>
          {showComps ? <ChevronUp size={16} className="text-muted-silver" /> : <ChevronDown size={16} className="text-muted-silver" />}
        </div>
        <AnimatePresence>
          {showComps && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
              <div className="mt-3 space-y-2 max-h-[400px] overflow-y-auto pr-1">
                {comparisons.map((comp: any, idx: number) => {
                  const req = comp.requirement ?? {};
                  const topMatch = (comp.top_matches ?? [])[0];
                  return (
                    <div key={idx} className="p-3 rounded-lg bg-steel-slate/5 border border-steel-slate/15">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-ghost-white line-clamp-2">{req.original_text || comp.message || '\u2014'}</p>
                          {topMatch && (
                            <div className="mt-2 flex items-center gap-3 text-[11px] flex-wrap">
                              <span className="text-electric-cyan font-medium">{topMatch.product_name || topMatch.product_code}</span>
                              <span className="text-muted-silver">{topMatch.oem}</span>
                              <span className="text-muted-silver">{topMatch.conductor_size}mm\u00B2 {topMatch.cores}C</span>
                              {topMatch.price_per_meter > 0 && <span className="text-neon-emerald">{fmtINR(topMatch.price_per_meter)}/m</span>}
                            </div>
                          )}
                        </div>
                        <div className="text-right flex-shrink-0">
                          {topMatch ? (
                            <span className={`text-lg font-bold ${topMatch.match_score >= 85 ? 'text-neon-emerald' : topMatch.match_score >= 70 ? 'text-amber-glow' : 'text-coral-flame'}`}>
                              {Math.round(topMatch.match_score)}%
                            </span>
                          ) : (
                            <span className="text-xs text-muted-silver">No match</span>
                          )}
                          <p className="text-[10px] text-muted-silver">{comp.match_count ?? 0} products</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-center gap-4 pt-4 border-t border-steel-slate/20">
        {!saved && (
          <button onClick={onSave} disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-amber-glow/10 border border-amber-glow/30 text-amber-glow text-sm font-medium hover:bg-amber-glow/20 transition-colors disabled:opacity-50">
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            {saving ? 'Saving...' : 'Save Analysis'}
          </button>
        )}
        <button onClick={onBid}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-electric-cyan/10 border border-electric-cyan/30 text-electric-cyan text-sm font-medium hover:bg-electric-cyan/20 transition-colors">
          <Send size={14} /> Generate Bid
        </button>
      </div>
    </div>
  );
}

function SummaryCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  const colors: Record<string, string> = {
    cyan: 'text-electric-cyan bg-electric-cyan/10 border-electric-cyan/20',
    emerald: 'text-neon-emerald bg-neon-emerald/10 border-neon-emerald/20',
    amber: 'text-amber-glow bg-amber-glow/10 border-amber-glow/20',
    violet: 'text-violet-pulse bg-violet-pulse/10 border-violet-pulse/20',
  };
  const c = colors[color] ?? colors.cyan;
  return (
    <div className={`p-3 rounded-xl border text-center ${c}`}>
      <div className="flex items-center justify-center mb-1">{icon}</div>
      <p className="text-lg font-bold">{value}</p>
      <p className="text-[10px] uppercase tracking-wider opacity-70">{label}</p>
    </div>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-muted-silver uppercase tracking-wider">{label}</p>
      <p className="text-xs text-ghost-white font-medium mt-0.5 break-words">{value || '\u2014'}</p>
    </div>
  );
}
