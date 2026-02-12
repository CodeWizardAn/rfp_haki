import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Building2,
  Send,
  Download,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Star,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Award,
  Calculator,
  Package,
  Briefcase,
  Edit3,
  Printer,
  Copy,
  Landmark,
  ScrollText,
  Eye,
  DollarSign,
  TrendingUp,
  PieChart,
  BarChart3,
  Banknote,
  Receipt,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Badge, Button, Modal } from '@/components/ui';

// ─── Types ───

interface CompanyProfile {
  id: string;
  company_name: string;
  is_default: boolean;
  [key: string]: any;
}

interface BidDocument {
  id: string;
  status: string;
  generated_at: string;
  valid_until: string;
  company: Record<string, any>;
  rfp_reference: Record<string, any>;
  bid_terms: Record<string, any>;
  line_items: any[];
  financial_summary: Record<string, any>;
  oem_summary: Record<string, any>;
  technical_compliance: Record<string, any>;
  send_options: Record<string, any>;
  sent_to?: string;
  sent_at?: string;
}

// ─── Animations ───

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.04 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

// ─── API ───

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const hdrs = () => {
  const t = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` };
};

async function fetchProfiles(): Promise<CompanyProfile[]> {
  try {
    const r = await fetch(`${API}/api/v1/company-profiles`, { headers: hdrs() });
    if (!r.ok) return [];
    const j = await r.json();
    return j.data ?? j ?? [];
  } catch { return []; }
}

async function generateBid(payload: any): Promise<BidDocument | null> {
  try {
    const r = await fetch(`${API}/api/v1/bid-documents/generate`, {
      method: 'POST', headers: hdrs(), body: JSON.stringify(payload),
    });
    if (!r.ok) return null;
    const j = await r.json();
    return j.data ?? j;
  } catch { return null; }
}

async function sendBidEmail(bidId: string, payload: any): Promise<any> {
  try {
    const r = await fetch(`${API}/api/v1/bid-documents/${bidId}/send`, {
      method: 'POST', headers: hdrs(), body: JSON.stringify(payload),
    });
    if (!r.ok) return null;
    const j = await r.json();
    return j.data ?? j;
  } catch { return null; }
}

async function downloadBidPdf(bidId: string): Promise<void> {
  const t = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
  const r = await fetch(`${API}/api/v1/bid-documents/${bidId}/pdf`, {
    headers: { Authorization: `Bearer ${t}` },
  });
  if (!r.ok) throw new Error('PDF download failed');
  const blob = await r.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${bidId}_Tender_Response.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// ─── Helpers ───

const fmtINR = (v: number | null | undefined) => {
  if (!v || v < 0.01) return '—';
  return `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
};

const scoreColor = (s: number) =>
  s >= 85 ? 'text-neon-emerald' : s >= 70 ? 'text-amber-glow' : 'text-coral-flame';

// ═══════════════════════════════════════════════════════════════════
//  Main Component
// ═══════════════════════════════════════════════════════════════════

export default function BidGeneratorPage() {
  const location = useLocation();
  const navigate = useNavigate();

  // Analysis result — from location.state OR loaded from saved analyses
  const [analysisResult, setAnalysisResult] = useState<any>((location.state as any)?.analysisResult ?? null);
  const [fileName, setFileName] = useState<string>((location.state as any)?.fileName ?? '');

  // Saved analyses selector state
  const [savedAnalyses, setSavedAnalyses] = useState<any[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(false);
  const [savedSearch, setSavedSearch] = useState('');

  // State
  const [step, setStep] = useState<'configure' | 'generating' | 'preview' | 'sent'>('configure');
  const [profiles, setProfiles] = useState<CompanyProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [loadingProfiles, setLoadingProfiles] = useState(true);
  const [bidDoc, setBidDoc] = useState<BidDocument | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [sendModal, setSendModal] = useState(false);
  const [sendEmail, setSendEmail] = useState('');
  const [sendCc, setSendCc] = useState('');
  const [sendMessage, setSendMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [showLineItems, setShowLineItems] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [viewResponseModal, setViewResponseModal] = useState(false);
  const [showBudgetBreakdown, setShowBudgetBreakdown] = useState(true);

  // Bid options
  const [validityDays, setValidityDays] = useState(90);
  const [discountPct, setDiscountPct] = useState(0);
  const [deliveryTimeline, setDeliveryTimeline] = useState('6-8 weeks from PO');
  const [paymentTerms, setPaymentTerms] = useState('Net 30 days from delivery');
  const [warrantyPeriod, setWarrantyPeriod] = useState('As per manufacturer standards');
  const [freightTerms, setFreightTerms] = useState('FOR Destination');
  const [currency, setCurrency] = useState('INR');
  const [gstRate, setGstRate] = useState(18);
  const [notes, setNotes] = useState('');

  // Load profiles on mount
  useEffect(() => {
    (async () => {
      setLoadingProfiles(true);
      const p = await fetchProfiles();
      setProfiles(p);
      const def = p.find((x) => x.is_default);
      if (def) setSelectedProfile(def.id);
      else if (p.length > 0 && p[0]) setSelectedProfile(p[0].id);
      setLoadingProfiles(false);
    })();
  }, []);

  useEffect(() => {
    if (toast) { const t = setTimeout(() => setToast(null), 4000); return () => clearTimeout(t); }
  }, [toast]);

  // Load saved analyses when no analysis result is provided
  useEffect(() => {
    if (!analysisResult) {
      (async () => {
        setLoadingSaved(true);
        try {
          const r = await fetch(`${API}/api/v1/saved-analyses`, { headers: hdrs() });
          if (r.ok) {
            const j = await r.json();
            setSavedAnalyses(j.data ?? j ?? []);
          }
        } catch { /* empty */ }
        setLoadingSaved(false);
      })();
    }
  }, [analysisResult]);

  const handleSelectSavedAnalysis = (item: any) => {
    setAnalysisResult(item.analysis_result);
    setFileName(item.file_name || '');
    setToast({ type: 'success', msg: `Loaded analysis: ${item.file_name}` });
  };

  const filteredSaved = savedAnalyses.filter(s => {
    if (!savedSearch) return true;
    const q = savedSearch.toLowerCase();
    return (s.file_name ?? '').toLowerCase().includes(q)
      || (s.rfp_title ?? '').toLowerCase().includes(q)
      || (s.organization ?? '').toLowerCase().includes(q);
  });

  // No analysis result — show saved analyses picker
  if (!analysisResult) {
    return (
      <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
        <motion.div variants={fadeUp} className="flex items-center justify-between">
          <div>
            <h1 className="text-h2 text-ghost-white">Bid Generator</h1>
            <p className="text-body text-muted-silver mt-1">Select a saved analysis to generate a bid document</p>
          </div>
          <Button variant="secondary" leftIcon={<FileText size={16} />} onClick={() => navigate('/user/rfp-analyzer')}>
            New Analysis
          </Button>
        </motion.div>

        {loadingSaved && (
          <motion.div variants={fadeUp} className="text-center py-12">
            <Loader2 size={32} className="mx-auto text-electric-cyan animate-spin mb-4" />
            <p className="text-sm text-muted-silver">Loading saved analyses...</p>
          </motion.div>
        )}

        {!loadingSaved && savedAnalyses.length === 0 && (
          <motion.div variants={fadeUp}>
            <Card variant="glass" className="p-12 text-center">
              <FileText size={48} className="mx-auto text-steel-slate/40 mb-4" />
              <h2 className="text-lg font-semibold text-ghost-white mb-2">No Saved Analyses</h2>
              <p className="text-sm text-muted-silver mb-4">
                Analyze an RFP first, save the analysis, then return here to generate a bid document.
              </p>
              <div className="flex gap-3 justify-center">
                <Button variant="primary" onClick={() => navigate('/user/rfp-analyzer')}>Go to Analyzer</Button>
                <Button variant="secondary" onClick={() => navigate('/user/rfp-processing')}>RFP Processing</Button>
              </div>
            </Card>
          </motion.div>
        )}

        {!loadingSaved && savedAnalyses.length > 0 && (
          <>
            {/* Search */}
            <motion.div variants={fadeUp} className="relative">
              <input
                type="text"
                placeholder="Search saved analyses..."
                value={savedSearch}
                onChange={(e) => setSavedSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/60 focus:outline-none focus:border-neon-emerald/40 transition-colors"
              />
              <FileText size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
            </motion.div>

            {/* Saved analyses grid */}
            <motion.div variants={fadeUp} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {filteredSaved.map((item: any) => (
                <Card key={item.id} variant="glass"
                  className="p-4 cursor-pointer hover:border-electric-cyan/30 hover:scale-[1.01] transition-all"
                  onClick={() => handleSelectSavedAnalysis(item)}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-electric-cyan/10 flex items-center justify-center flex-shrink-0">
                      <FileText size={20} className="text-electric-cyan" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-ghost-white truncate">{item.file_name || 'Untitled'}</h3>
                      {item.rfp_title && <p className="text-xs text-muted-silver truncate mt-0.5">{item.rfp_title}</p>}
                      <div className="flex items-center gap-3 mt-2 text-[11px] text-muted-silver">
                        <span>{item.total_requirements ?? 0} requirements</span>
                        <span>·</span>
                        <span>{item.matched_requirements ?? 0} matched</span>
                      </div>
                      {item.organization && (
                        <div className="flex items-center gap-1 mt-1 text-[11px] text-muted-silver">
                          <Building2 size={10} /> {item.organization}
                        </div>
                      )}
                      <p className="text-[10px] text-muted-silver/60 mt-1.5">
                        Saved {item.saved_at ? new Date(item.saved_at).toLocaleDateString() : '—'}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </motion.div>
          </>
        )}
      </motion.div>
    );
  }

  const handleGenerate = async () => {
    if (!selectedProfile) {
      setToast({ type: 'error', msg: 'Select a company profile first' });
      return;
    }
    setStep('generating');
    const doc = await generateBid({
      analysis_result: analysisResult,
      profile_id: selectedProfile,
      bid_options: {
        validity_days: validityDays,
        discount_percentage: discountPct,
        delivery_timeline: deliveryTimeline,
        payment_terms: paymentTerms,
        warranty_period: warrantyPeriod,
        freight_terms: freightTerms,
        currency,
        gst_rate: gstRate,
        notes,
      },
    });
    if (doc) {
      setBidDoc(doc);
      setStep('preview');
      setToast({ type: 'success', msg: 'Bid document generated! Downloading PDF...' });
      // Auto-download the PDF
      try {
        await downloadBidPdf(doc.id);
        setToast({ type: 'success', msg: 'Bid generated & PDF downloaded!' });
      } catch {
        setToast({ type: 'success', msg: 'Bid generated! Click Download PDF to get the file.' });
      }
    } else {
      setStep('configure');
      setToast({ type: 'error', msg: 'Failed to generate bid — check your profile and try again' });
    }
  };

  const handleSend = async () => {
    if (!bidDoc || !sendEmail) return;
    setSending(true);
    const result = await sendBidEmail(bidDoc.id, {
      email_to: sendEmail, email_cc: sendCc, message: sendMessage,
    });
    setSending(false);
    if (result?.success) {
      setSendModal(false);
      setStep('sent');
      setToast({ type: 'success', msg: `Bid sent to ${sendEmail}` });
    } else {
      setToast({ type: 'error', msg: 'Failed to send bid' });
    }
  };

  const handlePrint = () => { window.print(); };
  const handleCopyId = () => {
    if (bidDoc) navigator.clipboard.writeText(bidDoc.id);
    setToast({ type: 'success', msg: 'Bid ID copied!' });
  };

  const handleDownloadPdf = async () => {
    if (!bidDoc) return;
    setDownloadingPdf(true);
    try {
      await downloadBidPdf(bidDoc.id);
      setToast({ type: 'success', msg: 'PDF downloaded!' });
    } catch {
      setToast({ type: 'error', msg: 'PDF download failed — try again' });
    } finally {
      setDownloadingPdf(false);
    }
  };

  // ─── Render ───

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6 pb-12">
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
          <h1 className="text-h2 text-ghost-white">Bid Generator</h1>
          <p className="text-body text-muted-silver mt-1">
            {step === 'configure' && 'Configure bid terms, select company profile, and generate your RFP response'}
            {step === 'generating' && 'Generating your bid document...'}
            {step === 'preview' && 'Review your bid document before sending'}
            {step === 'sent' && 'Bid sent successfully!'}
          </p>
        </div>
        {step === 'preview' && bidDoc && (
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" leftIcon={<Copy size={14} />} onClick={handleCopyId}>Copy ID</Button>
            <Button variant="ghost" size="sm" leftIcon={<Printer size={14} />} onClick={handlePrint}>Print</Button>
            <Button variant="secondary" size="sm" leftIcon={<Eye size={14} />} onClick={() => setViewResponseModal(true)}>View Response</Button>
            <Button variant="secondary" size="sm"
              leftIcon={downloadingPdf ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
              onClick={handleDownloadPdf} disabled={downloadingPdf}>
              {downloadingPdf ? 'Generating PDF...' : 'Download PDF'}
            </Button>
            <Button variant="primary" leftIcon={<Send size={16} />} onClick={() => setSendModal(true)}>Send Bid</Button>
          </div>
        )}
      </motion.div>

      {/* ═══ Step: Configure ═══ */}
      {step === 'configure' && (
        <>
          {/* Source Info */}
          <motion.div variants={fadeUp}>
            <Card variant="glass" className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-neon-emerald/15 flex items-center justify-center">
                  <FileText size={20} className="text-neon-emerald" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-ghost-white">Source: {fileName || 'RFP Analysis'}</p>
                  <p className="text-xs text-muted-silver">
                    {analysisResult.total_requirements ?? 0} requirements · {(analysisResult.comparisons ?? []).filter((c: any) => c.match_count > 0).length} matched · {analysisResult.detected_application} application
                  </p>
                </div>
                <Badge variant="soft" color="emerald" size="sm">Analysis Complete</Badge>
              </div>
            </Card>
          </motion.div>

          {/* Select Company Profile */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 size={18} className="text-electric-cyan" />
                  Company Profile
                </CardTitle>
              </CardHeader>
              <div className="px-4 pb-4">
                {loadingProfiles ? (
                  <div className="flex items-center gap-2 py-4">
                    <Loader2 size={16} className="animate-spin text-electric-cyan" />
                    <span className="text-sm text-muted-silver">Loading profiles...</span>
                  </div>
                ) : profiles.length === 0 ? (
                  <div className="text-center py-6">
                    <Building2 size={32} className="mx-auto text-steel-slate/40 mb-3" />
                    <p className="text-sm text-muted-silver mb-3">No company profiles found</p>
                    <Button variant="primary" size="sm" onClick={() => navigate('/user/profiles')}>Create Profile</Button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {profiles.map((p) => (
                      <div
                        key={p.id}
                        onClick={() => setSelectedProfile(p.id)}
                        className={`p-4 rounded-xl border cursor-pointer transition-all ${
                          selectedProfile === p.id
                            ? 'border-electric-cyan/50 bg-electric-cyan/5 ring-1 ring-electric-cyan/30'
                            : 'border-steel-slate/20 bg-steel-slate/5 hover:border-steel-slate/40'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-electric-cyan/10 flex items-center justify-center">
                            <Building2 size={18} className="text-electric-cyan" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-semibold text-ghost-white truncate">{p.company_name}</p>
                              {p.is_default && <Badge variant="soft" color="amber" size="sm"><Star size={10} /></Badge>}
                            </div>
                            <p className="text-xs text-muted-silver truncate">{p.industry || p.email || p.id}</p>
                          </div>
                          {selectedProfile === p.id && <CheckCircle2 size={18} className="text-electric-cyan" />}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Bid Options */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ScrollText size={18} className="text-amber-glow" />
                  Bid Terms &amp; Options
                </CardTitle>
              </CardHeader>
              <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <OptField label="Validity (Days)" value={String(validityDays)} onChange={(v) => setValidityDays(parseInt(v) || 90)} />
                <OptField label="Discount %" value={String(discountPct)} onChange={(v) => setDiscountPct(parseFloat(v) || 0)} />
                <OptField label="GST Rate %" value={String(gstRate)} onChange={(v) => setGstRate(parseFloat(v) || 18)} />
                <OptField label="Delivery Timeline" value={deliveryTimeline} onChange={setDeliveryTimeline} />
                <OptField label="Payment Terms" value={paymentTerms} onChange={setPaymentTerms} />
                <OptField label="Warranty" value={warrantyPeriod} onChange={setWarrantyPeriod} />
                <OptField label="Freight Terms" value={freightTerms} onChange={setFreightTerms} />
                <OptSelect label="Currency" value={currency} onChange={setCurrency} options={['INR', 'USD', 'EUR', 'KES']} />
                <div className="sm:col-span-2 lg:col-span-3">
                  <label className="text-xs text-muted-silver uppercase tracking-wider mb-1.5 block">Notes / Special Instructions</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/40 focus:outline-none focus:border-neon-emerald/40 transition-colors resize-none"
                    placeholder="Any additional notes for the bid..."
                  />
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Generate Button */}
          <motion.div variants={fadeUp} className="flex justify-center">
            <Button variant="primary" size="lg" leftIcon={<FileText size={18} />}
              onClick={handleGenerate} disabled={!selectedProfile || loadingProfiles}
              className="px-12">
              Generate Bid Document
            </Button>
          </motion.div>
        </>
      )}

      {/* ═══ Step: Generating ═══ */}
      {step === 'generating' && (
        <motion.div variants={fadeUp}>
          <Card variant="glass" className="p-12 text-center">
            <div className="w-16 h-16 border-2 border-electric-cyan border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <h2 className="text-xl font-semibold text-ghost-white mb-2">Generating Bid Document</h2>
            <p className="text-sm text-muted-silver">
              Building formatted RFP response from analysis data and company profile...
            </p>
          </Card>
        </motion.div>
      )}

      {/* ═══ Step: Preview ═══ */}
      {step === 'preview' && bidDoc && (
        <>
          {/* Bid Header Banner */}
          <motion.div variants={fadeUp}>
            <Card variant="glass" className="p-5 border-neon-emerald/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-neon-emerald/15 flex items-center justify-center">
                    <FileText size={24} className="text-neon-emerald" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-ghost-white">
                      Bid Document — {bidDoc.id}
                    </h2>
                    <p className="text-xs text-muted-silver">
                      Generated {new Date(bidDoc.generated_at).toLocaleString()} · Valid until {new Date(bidDoc.valid_until).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <Badge variant="soft" color={bidDoc.status === 'sent' ? 'emerald' : 'cyan'} size="sm">
                  {bidDoc.status}
                </Badge>
              </div>
            </Card>
          </motion.div>

          {/* Company Info */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 size={18} className="text-electric-cyan" />
                  Bidder Information
                </CardTitle>
              </CardHeader>
              <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <InfoCell label="Company" value={bidDoc.company.name} />
                <InfoCell label="Registration" value={bidDoc.company.registration_number} />
                <InfoCell label="GST No." value={bidDoc.company.gst_number} />
                <InfoCell label="Address" value={bidDoc.company.address} className="sm:col-span-2" />
                <InfoCell label="Industry" value={bidDoc.company.industry} />
                <InfoCell label="Contact" value={`${bidDoc.company.email} · ${bidDoc.company.phone}`} className="sm:col-span-2" />
                <InfoCell label="Signatory" value={`${bidDoc.company.authorized_signatory}, ${bidDoc.company.signatory_designation}`} />
                <InfoCell label="Experience" value={`${bidDoc.company.experience_years} years · Turnover ${bidDoc.company.annual_turnover}`} className="sm:col-span-2" />
                {bidDoc.company.certifications?.length > 0 && (
                  <div className="sm:col-span-3">
                    <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-1">Certifications</p>
                    <div className="flex flex-wrap gap-1.5">
                      {bidDoc.company.certifications.map((c: string) => (
                        <Badge key={c} variant="outline" size="sm">{c}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* RFP Reference */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ScrollText size={18} className="text-violet-pulse" />
                  RFP Reference
                </CardTitle>
              </CardHeader>
              <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <InfoCell label="Bid Number" value={bidDoc.rfp_reference.bid_number || '—'} />
                <InfoCell label="Title" value={bidDoc.rfp_reference.title} className="sm:col-span-2" />
                <InfoCell label="Organization" value={bidDoc.rfp_reference.organization || '—'} />
                <InfoCell label="Ministry/Dept" value={`${bidDoc.rfp_reference.ministry || '—'} / ${bidDoc.rfp_reference.department || '—'}`} />
                <InfoCell label="Bid End" value={bidDoc.rfp_reference.bid_end_date || '—'} />
                <InfoCell label="Requirements" value={`${bidDoc.rfp_reference.total_requirements} total, ${bidDoc.rfp_reference.matched_requirements} matched`} />
                <InfoCell label="Application" value={bidDoc.rfp_reference.detected_application} />
                <InfoCell label="Source" value={bidDoc.rfp_reference.source_file} />
              </div>
            </Card>
          </motion.div>

          {/* Bid Terms */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Briefcase size={18} className="text-amber-glow" />
                  Bid Terms &amp; Conditions
                </CardTitle>
              </CardHeader>
              <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <InfoCell label="Validity" value={`${bidDoc.bid_terms.validity_days} days`} />
                <InfoCell label="Delivery" value={bidDoc.bid_terms.delivery_timeline} />
                <InfoCell label="Payment" value={bidDoc.bid_terms.payment_terms} />
                <InfoCell label="Warranty" value={bidDoc.bid_terms.warranty} />
                <InfoCell label="Freight" value={bidDoc.bid_terms.freight_terms} />
                <InfoCell label="Discount" value={`${bidDoc.bid_terms.discount_percentage}%`} />
                <InfoCell label="Inspection" value={bidDoc.bid_terms.inspection_terms} />
                <InfoCell label="P&F" value={bidDoc.bid_terms.packing_forwarding} />
                <InfoCell label="LD Clause" value={bidDoc.bid_terms.liquidated_damages} />
                {bidDoc.bid_terms.notes && (
                  <div className="sm:col-span-3">
                    <InfoCell label="Notes" value={bidDoc.bid_terms.notes} />
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Line Items */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <div
                onClick={() => setShowLineItems(!showLineItems)}
                className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-steel-slate/10 transition-colors"
              >
                <h3 className="text-sm font-semibold text-ghost-white flex items-center gap-2">
                  <Package size={16} className="text-neon-emerald" />
                  Product Line Items ({bidDoc.line_items.length})
                </h3>
                {showLineItems ? <ChevronUp size={16} className="text-muted-silver" /> : <ChevronDown size={16} className="text-muted-silver" />}
              </div>
              <AnimatePresence>
                {showLineItems && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4 overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-left text-muted-silver border-b border-steel-slate/20">
                            <th className="pb-2 pr-3">#</th>
                            <th className="pb-2 pr-3">Product</th>
                            <th className="pb-2 pr-3">OEM</th>
                            <th className="pb-2 pr-3">Specification</th>
                            <th className="pb-2 pr-3 text-center">Match</th>
                            <th className="pb-2 pr-3 text-right">Qty</th>
                            <th className="pb-2 pr-3 text-right">Unit Price</th>
                            <th className="pb-2 pr-3 text-right">Discount</th>
                            <th className="pb-2 text-right">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {bidDoc.line_items.map((li: any) => (
                            <tr key={li.sr_no} className="border-b border-steel-slate/10 hover:bg-steel-slate/5">
                              <td className="py-2 pr-3 text-muted-silver">{li.sr_no}</td>
                              <td className="py-2 pr-3 text-ghost-white max-w-[200px]">
                                <p className="font-medium truncate">{li.product_name}</p>
                                <p className="text-[10px] text-muted-silver font-mono">{li.product_code}</p>
                              </td>
                              <td className="py-2 pr-3 text-electric-cyan">{li.oem}</td>
                              <td className="py-2 pr-3 text-muted-silver max-w-[150px] truncate">{li.specification}</td>
                              <td className="py-2 pr-3 text-center">
                                <span className={`font-bold ${scoreColor(li.match_score)}`}>{Math.round(li.match_score)}%</span>
                              </td>
                              <td className="py-2 pr-3 text-right text-ghost-white">{Number(li.quantity).toLocaleString()}</td>
                              <td className="py-2 pr-3 text-right text-ghost-white">{fmtINR(li.unit_price)}</td>
                              <td className="py-2 pr-3 text-right text-amber-glow">{li.discount_percent}%</td>
                              <td className="py-2 text-right font-medium text-neon-emerald">{fmtINR(li.total_price)}</td>
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

          {/* Financial Summary */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator size={18} className="text-neon-emerald" />
                  Financial Summary
                </CardTitle>
              </CardHeader>
              <div className="px-4 pb-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                  <FinCard label="Subtotal" value={fmtINR(bidDoc.financial_summary.subtotal)} />
                  <FinCard label={`GST (${bidDoc.financial_summary.gst_rate}%)`} value={fmtINR(bidDoc.financial_summary.gst_amount)} />
                  <FinCard label={`Discount (${bidDoc.financial_summary.discount_percentage}%)`} value={`${bidDoc.financial_summary.discount_percentage}%`} />
                  <FinCard label="Grand Total" value={fmtINR(bidDoc.financial_summary.grand_total)} highlight />
                </div>
                {bidDoc.financial_summary.amount_in_words && (
                  <p className="text-xs text-muted-silver italic">
                    Amount in words: {bidDoc.financial_summary.amount_in_words}
                  </p>
                )}
                {bidDoc.financial_summary.ai_pricing_available && bidDoc.financial_summary.ai_grand_total > 0 && (
                  <div className="mt-3 p-3 rounded-lg bg-violet-pulse/5 border border-violet-pulse/20">
                    <p className="text-xs text-ghost-white flex items-center gap-1.5">
                      <Award size={12} className="text-violet-pulse" />
                      AI Pricing Agent estimate: {fmtINR(bidDoc.financial_summary.ai_grand_total)}
                      <span className="text-muted-silver ml-1">(material: {fmtINR(bidDoc.financial_summary.ai_material_cost)} + test: {fmtINR(bidDoc.financial_summary.ai_test_cost)})</span>
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* ── Budget Breakdown (Enhanced) ── */}
          {(bidDoc as any).budget_breakdown && (
            <motion.div variants={fadeUp}>
              <Card variant="glass">
                <div
                  onClick={() => setShowBudgetBreakdown(!showBudgetBreakdown)}
                  className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-steel-slate/10 transition-colors"
                >
                  <h3 className="text-sm font-semibold text-ghost-white flex items-center gap-2">
                    <Banknote size={16} className="text-amber-glow" />
                    Detailed Budget Breakdown
                  </h3>
                  {showBudgetBreakdown ? <ChevronUp size={16} className="text-muted-silver" /> : <ChevronDown size={16} className="text-muted-silver" />}
                </div>
                <AnimatePresence>
                  {showBudgetBreakdown && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                      <div className="px-4 pb-4 space-y-4">
                        {/* RFP Budget Info */}
                        {((bidDoc as any).budget_breakdown.rfp_estimated_value || (bidDoc as any).budget_breakdown.emd_amount) && (
                          <div className="p-3 rounded-xl bg-electric-cyan/5 border border-electric-cyan/20">
                            <p className="text-[10px] text-electric-cyan uppercase tracking-wider mb-2 flex items-center gap-1">
                              <Receipt size={10} /> RFP Budget Reference
                            </p>
                            <div className="grid grid-cols-2 gap-3">
                              {(bidDoc as any).budget_breakdown.rfp_estimated_value && (
                                <div><p className="text-[10px] text-muted-silver">Estimated Value</p><p className="text-sm font-semibold text-electric-cyan">{(bidDoc as any).budget_breakdown.rfp_estimated_value}</p></div>
                              )}
                              {(bidDoc as any).budget_breakdown.emd_amount && (
                                <div><p className="text-[10px] text-muted-silver">EMD / Bid Security</p><p className="text-sm font-semibold text-amber-glow">{(bidDoc as any).budget_breakdown.emd_amount}</p></div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Cost Stats Row */}
                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                          <BudgetStat icon={<Package size={14} />} label="Items" value={String((bidDoc as any).budget_breakdown.total_line_items)} color="cyan" />
                          <BudgetStat icon={<BarChart3 size={14} />} label="Total Qty" value={Number((bidDoc as any).budget_breakdown.total_quantity).toLocaleString()} color="cyan" />
                          <BudgetStat icon={<DollarSign size={14} />} label="Avg Unit" value={fmtINR((bidDoc as any).budget_breakdown.avg_unit_price)} color="emerald" />
                          <BudgetStat icon={<ArrowDownRight size={14} />} label="Min Unit" value={fmtINR((bidDoc as any).budget_breakdown.min_unit_price)} color="amber" />
                          <BudgetStat icon={<ArrowUpRight size={14} />} label="Max Unit" value={fmtINR((bidDoc as any).budget_breakdown.max_unit_price)} color="amber" />
                        </div>

                        {/* Discount Savings */}
                        {(bidDoc as any).budget_breakdown.discount_savings > 0 && (
                          <div className="p-3 rounded-xl bg-neon-emerald/5 border border-neon-emerald/20 flex items-center gap-3">
                            <div className="w-9 h-9 rounded-lg bg-neon-emerald/15 flex items-center justify-center flex-shrink-0">
                              <TrendingUp size={16} className="text-neon-emerald" />
                            </div>
                            <div>
                              <p className="text-[10px] text-muted-silver uppercase tracking-wider">Discount Savings</p>
                              <p className="text-sm font-bold text-neon-emerald">{fmtINR((bidDoc as any).budget_breakdown.discount_savings)}</p>
                            </div>
                          </div>
                        )}

                        {/* OEM-wise Breakdown */}
                        {(bidDoc as any).budget_breakdown.oem_breakdown?.length > 0 && (
                          <div>
                            <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-2 flex items-center gap-1"><PieChart size={10} /> Cost by OEM</p>
                            <div className="space-y-2">
                              {(bidDoc as any).budget_breakdown.oem_breakdown.map((ob: any) => (
                                <div key={ob.oem} className="flex items-center gap-3">
                                  <span className="text-xs text-electric-cyan font-medium w-28 truncate">{ob.oem}</span>
                                  <div className="flex-1 h-2 rounded-full bg-steel-slate/20 overflow-hidden">
                                    <div className="h-full rounded-full bg-electric-cyan/60" style={{ width: `${Math.min(ob.percentage, 100)}%` }} />
                                  </div>
                                  <span className="text-xs text-ghost-white font-mono w-24 text-right">{fmtINR(ob.total)}</span>
                                  <span className="text-[10px] text-muted-silver w-12 text-right">{ob.percentage}%</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Category Breakdown */}
                        {(bidDoc as any).budget_breakdown.category_breakdown?.length > 0 && (
                          <div>
                            <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-2 flex items-center gap-1"><BarChart3 size={10} /> Cost by Voltage Category</p>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                              {(bidDoc as any).budget_breakdown.category_breakdown.map((cb: any) => (
                                <div key={cb.category} className="p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/15 text-center">
                                  <p className="text-[10px] text-muted-silver truncate">{cb.category}</p>
                                  <p className="text-sm font-bold text-ghost-white mt-0.5">{fmtINR(cb.total)}</p>
                                  <p className="text-[10px] text-electric-cyan">{cb.percentage}%</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* AI Margin Comparison */}
                        {(bidDoc as any).budget_breakdown.ai_estimated_total && (
                          <div className="p-3 rounded-xl bg-violet-pulse/5 border border-violet-pulse/20">
                            <p className="text-[10px] text-violet-pulse uppercase tracking-wider mb-2 flex items-center gap-1">
                              <Award size={10} /> AI Cost Comparison
                            </p>
                            <div className="grid grid-cols-3 gap-3">
                              <div>
                                <p className="text-[10px] text-muted-silver">AI Estimated</p>
                                <p className="text-sm font-semibold text-violet-pulse">{fmtINR((bidDoc as any).budget_breakdown.ai_estimated_total)}</p>
                              </div>
                              <div>
                                <p className="text-[10px] text-muted-silver">Your Bid</p>
                                <p className="text-sm font-semibold text-neon-emerald">{fmtINR((bidDoc as any).budget_breakdown.grand_total)}</p>
                              </div>
                              <div>
                                <p className="text-[10px] text-muted-silver">Margin</p>
                                <p className={`text-sm font-semibold flex items-center gap-1 ${
                                  ((bidDoc as any).budget_breakdown.margin_vs_ai ?? 0) >= 0 ? 'text-neon-emerald' : 'text-coral-flame'
                                }`}>
                                  {((bidDoc as any).budget_breakdown.margin_vs_ai ?? 0) >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                                  {fmtINR(Math.abs((bidDoc as any).budget_breakdown.margin_vs_ai ?? 0))}
                                  <span className="text-[10px] text-muted-silver ml-1">({(bidDoc as any).budget_breakdown.margin_pct_vs_ai}%)</span>
                                </p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Grand Total Recap */}
                        <div className="grid grid-cols-3 gap-3">
                          <FinCard label="Subtotal" value={fmtINR((bidDoc as any).budget_breakdown.subtotal_before_tax)} />
                          <FinCard label={`GST (${(bidDoc as any).budget_breakdown.gst_rate}%)`} value={fmtINR((bidDoc as any).budget_breakdown.gst_amount)} />
                          <FinCard label="Grand Total" value={fmtINR((bidDoc as any).budget_breakdown.grand_total)} highlight />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            </motion.div>
          )}

          {/* Technical Compliance */}
          <motion.div variants={fadeUp}>
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck size={18} className="text-electric-cyan" />
                  Technical Compliance Summary
                </CardTitle>
              </CardHeader>
              <div className="px-4 pb-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <InfoCell label="Total Requirements" value={String(bidDoc.technical_compliance.total_requirements)} />
                <InfoCell label="Wire/Cable Specs" value={String(bidDoc.technical_compliance.wire_cable_specs)} />
                <InfoCell label="Products Matched" value={String(bidDoc.technical_compliance.matched_products)} />
                <InfoCell label="Avg Match Score" value={`${bidDoc.technical_compliance.average_match_score}%`} />
                {bidDoc.technical_compliance.standards_offered?.length > 0 && (
                  <div className="sm:col-span-4">
                    <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-1">Standards Offered</p>
                    <div className="flex flex-wrap gap-1.5">
                      {bidDoc.technical_compliance.standards_offered.map((s: string) => (
                        <Badge key={s} variant="outline" color="cyan" size="sm">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>

          {/* Bank Details */}
          {bidDoc.company.bank_details && (
            <motion.div variants={fadeUp}>
              <Card variant="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Landmark size={18} className="text-amber-glow" />
                    Bank Details (for payment reference)
                  </CardTitle>
                </CardHeader>
                <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  <InfoCell label="Bank" value={bidDoc.company.bank_details.name} />
                  <InfoCell label="Branch" value={bidDoc.company.bank_details.branch} />
                  <InfoCell label="Account" value={bidDoc.company.bank_details.account} />
                  <InfoCell label="IFSC" value={bidDoc.company.bank_details.ifsc} />
                  <InfoCell label="SWIFT" value={bidDoc.company.bank_details.swift} />
                </div>
              </Card>
            </motion.div>
          )}

          {/* Action bar */}
          <motion.div variants={fadeUp} className="flex items-center justify-center gap-4 flex-wrap">
            <Button variant="ghost" leftIcon={<Edit3 size={16} />} onClick={() => setStep('configure')}>
              Edit Options
            </Button>
            <Button variant="secondary" size="lg" leftIcon={<Eye size={18} />} onClick={() => setViewResponseModal(true)} className="px-8">
              View Response
            </Button>
            <Button variant="secondary" size="lg"
              leftIcon={downloadingPdf ? <Loader2 size={18} className="animate-spin" /> : <Download size={18} />}
              onClick={handleDownloadPdf} disabled={downloadingPdf} className="px-8">
              {downloadingPdf ? 'Generating PDF...' : 'Download PDF'}
            </Button>
            <Button variant="primary" size="lg" leftIcon={<Send size={18} />} onClick={() => setSendModal(true)} className="px-10">
              Send Bid
            </Button>
            <Button variant="ghost" leftIcon={<Printer size={16} />} onClick={handlePrint}>
              Print
            </Button>
          </motion.div>
        </>
      )}

      {/* ═══ Step: Sent ═══ */}
      {step === 'sent' && bidDoc && (
        <motion.div variants={fadeUp}>
          <Card variant="glass" className="p-12 text-center">
            <div className="w-20 h-20 rounded-full bg-neon-emerald/15 flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 size={40} className="text-neon-emerald" />
            </div>
            <h2 className="text-2xl font-semibold text-ghost-white mb-2">Bid Sent Successfully!</h2>
            <p className="text-sm text-muted-silver mb-1">
              Bid <span className="text-electric-cyan font-mono">{bidDoc.id}</span> has been sent to {bidDoc.sent_to || sendEmail}
            </p>
            <p className="text-xs text-muted-silver mb-8">
              Sent at {bidDoc.sent_at ? new Date(bidDoc.sent_at).toLocaleString() : 'just now'}
            </p>
            <div className="flex items-center justify-center gap-3">
              <Button variant="ghost" onClick={() => navigate('/user/rfp-analyzer')}>Analyze Another RFP</Button>
              <Button variant="secondary"
                leftIcon={downloadingPdf ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                onClick={handleDownloadPdf} disabled={downloadingPdf}>
                {downloadingPdf ? 'Generating...' : 'Download PDF'}
              </Button>
              <Button variant="primary" onClick={() => navigate('/user/rfps')}>View RFPs</Button>
            </div>
          </Card>
        </motion.div>
      )}

      {/* ═══ View Response Modal ═══ */}
      {bidDoc && (
        <Modal open={viewResponseModal} onClose={() => setViewResponseModal(false)} title="" size="full">
          <BidResponseDocument bid={bidDoc} fmtINR={fmtINR} onDownload={handleDownloadPdf} downloading={downloadingPdf} />
        </Modal>
      )}

      {/* ═══ Send Modal ═══ */}
      <Modal open={sendModal} onClose={() => setSendModal(false)} title="Send Bid Document" size="md">
        <div className="p-4 space-y-4">
          <div>
            <label className="text-xs text-muted-silver uppercase tracking-wider mb-1.5 block">To (Email) *</label>
            <input
              type="email" value={sendEmail} onChange={(e) => setSendEmail(e.target.value)}
              placeholder="recipient@company.com"
              className="w-full px-3 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/40 focus:outline-none focus:border-neon-emerald/40"
            />
          </div>
          <div>
            <label className="text-xs text-muted-silver uppercase tracking-wider mb-1.5 block">CC</label>
            <input
              type="text" value={sendCc} onChange={(e) => setSendCc(e.target.value)}
              placeholder="cc1@company.com, cc2@company.com"
              className="w-full px-3 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/40 focus:outline-none focus:border-neon-emerald/40"
            />
          </div>
          <div>
            <label className="text-xs text-muted-silver uppercase tracking-wider mb-1.5 block">Message</label>
            <textarea
              value={sendMessage} onChange={(e) => setSendMessage(e.target.value)}
              rows={4}
              placeholder="Please find attached our bid in response to the referenced RFP..."
              className="w-full px-3 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/40 focus:outline-none focus:border-neon-emerald/40 resize-none"
            />
          </div>
          {bidDoc && (
            <div className="p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/20">
              <p className="text-xs text-muted-silver mb-1">Subject Preview</p>
              <p className="text-sm text-ghost-white">{bidDoc.send_options.email_subject}</p>
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setSendModal(false)}>Cancel</Button>
            <Button variant="primary" leftIcon={sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
              onClick={handleSend} disabled={!sendEmail || sending}>
              {sending ? 'Sending...' : 'Send Now'}
            </Button>
          </div>
        </div>
      </Modal>
    </motion.div>
  );
}

// ─── Sub-components ───

function InfoCell({ label, value, className = '' }: { label: string; value: string; className?: string }) {
  return (
    <div className={`p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/15 ${className}`}>
      <p className="text-[10px] text-muted-silver uppercase tracking-wider">{label}</p>
      <p className="text-sm text-ghost-white font-medium mt-0.5 break-words">{value || '—'}</p>
    </div>
  );
}

function FinCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`p-4 rounded-xl border text-center ${
      highlight ? 'border-neon-emerald/30 bg-neon-emerald/5' : 'border-steel-slate/20 bg-steel-slate/10'
    }`}>
      <p className={`text-[10px] uppercase tracking-wider mb-1 ${highlight ? 'text-neon-emerald' : 'text-muted-silver'}`}>{label}</p>
      <p className={`text-lg font-bold ${highlight ? 'text-neon-emerald' : 'text-ghost-white'}`}>{value}</p>
    </div>
  );
}

const budgetColors: Record<string, string> = {
  cyan: 'text-electric-cyan bg-electric-cyan/10',
  emerald: 'text-neon-emerald bg-neon-emerald/10',
  amber: 'text-amber-glow bg-amber-glow/10',
};

function BudgetStat({ icon, label, value, color = 'cyan' }: { icon: React.ReactNode; label: string; value: string; color?: string }) {
  const c = budgetColors[color] ?? budgetColors.cyan;
  return (
    <div className="p-3 rounded-xl border border-steel-slate/15 bg-steel-slate/10 flex items-center gap-2.5">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${c}`}>{icon}</div>
      <div className="min-w-0">
        <p className="text-[10px] text-muted-silver uppercase tracking-wider leading-none">{label}</p>
        <p className="text-sm font-bold text-ghost-white truncate mt-0.5">{value}</p>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────
//  Bid Response Document — full formal view for the modal
// ──────────────────────────────────────────────────────────────────────

function BidResponseDocument({
  bid,
  fmtINR: fmt,
  onDownload,
  downloading,
}: {
  bid: BidDocument;
  fmtINR: (v: number | null | undefined) => string;
  onDownload: () => void;
  downloading: boolean;
}) {
  const bb = (bid as any).budget_breakdown ?? {};

  return (
    <div className="max-w-4xl mx-auto space-y-6 print:space-y-4 text-ghost-white">
      {/* ── Letterhead ── */}
      <div className="text-center border-b-2 border-electric-cyan/40 pb-5">
        <h1 className="text-2xl font-bold tracking-wide">{bid.company.name}</h1>
        <p className="text-xs text-muted-silver mt-1">{bid.company.address}</p>
        <p className="text-xs text-muted-silver">
          {[bid.company.phone, bid.company.email, bid.company.website].filter(Boolean).join('  |  ')}
        </p>
        <p className="text-[10px] text-muted-silver mt-1 font-mono">
          Reg: {bid.company.registration_number} &nbsp;|&nbsp; GST: {bid.company.gst_number}
        </p>
      </div>

      {/* Title */}
      <div className="text-center">
        <h2 className="text-xl font-bold text-electric-cyan uppercase tracking-widest">Bid / Tender Response</h2>
        <p className="text-sm text-muted-silver mt-1">{bid.rfp_reference.title}</p>
      </div>

      {/* Quick Ref */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-steel-slate/10 border border-steel-slate/20">
        <KV label="Bid Ref" value={bid.id} />
        <KV label="RFP / Tender No." value={bid.rfp_reference.bid_number || '—'} />
        <KV label="Date" value={new Date(bid.generated_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })} />
        <KV label="Valid Until" value={new Date(bid.valid_until).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })} />
      </div>

      {/* ── Section 1: Bidder Info ── */}
      <DocSection num={1} title="BIDDER INFORMATION">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2">
          <KV label="Company" value={bid.company.name} />
          <KV label="Trading Name" value={(bid.company as any).trading_name} />
          <KV label="Registration" value={bid.company.registration_number} />
          <KV label="GST No." value={bid.company.gst_number} />
          <KV label="Industry" value={bid.company.industry} />
          <KV label="Experience" value={`${bid.company.experience_years} years`} />
          <KV label="Annual Turnover" value={bid.company.annual_turnover} className="sm:col-span-2" />
          <KV label="Contact" value={`${bid.company.email}  |  ${bid.company.phone}`} className="sm:col-span-3" />
          <KV label="Address" value={bid.company.address} className="sm:col-span-3" />
        </div>
        {bid.company.certifications?.length > 0 && (
          <div className="mt-3">
            <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-1">Certifications</p>
            <p className="text-xs text-ghost-white">{bid.company.certifications.join(', ')}</p>
          </div>
        )}
        {bid.company.key_clients?.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-1">Key Clients</p>
            <p className="text-xs text-ghost-white">{bid.company.key_clients.join(', ')}</p>
          </div>
        )}
      </DocSection>

      {/* ── Section 2: RFP Reference ── */}
      <DocSection num={2} title="RFP REFERENCE DETAILS">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2">
          <KV label="Bid / Tender No." value={bid.rfp_reference.bid_number || '—'} />
          <KV label="Organization" value={bid.rfp_reference.organization || '—'} />
          <KV label="Ministry / Dept" value={`${bid.rfp_reference.ministry || '—'} / ${bid.rfp_reference.department || '—'}`} />
          <KV label="Bid End Date" value={bid.rfp_reference.bid_end_date || '—'} />
          <KV label="EMD Amount" value={bid.rfp_reference.emd_amount || bb.emd_amount || '—'} />
          <KV label="Estimated Value" value={bb.rfp_estimated_value || '—'} />
          <KV label="Requirements" value={`${bid.rfp_reference.total_requirements} total, ${bid.rfp_reference.matched_requirements} matched`} />
          <KV label="Application" value={bid.rfp_reference.detected_application} />
          <KV label="Source" value={bid.rfp_reference.source_file} />
        </div>
      </DocSection>

      {/* ── Section 3: Terms & Conditions ── */}
      <DocSection num={3} title="BID TERMS & CONDITIONS">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2">
          <KV label="Validity" value={`${bid.bid_terms.validity_days} days`} />
          <KV label="Delivery" value={bid.bid_terms.delivery_timeline} />
          <KV label="Payment" value={bid.bid_terms.payment_terms} />
          <KV label="Warranty" value={bid.bid_terms.warranty} />
          <KV label="Freight" value={bid.bid_terms.freight_terms} />
          <KV label="Inspection" value={bid.bid_terms.inspection_terms} />
          <KV label="P&F" value={bid.bid_terms.packing_forwarding} />
          <KV label="LD Clause" value={bid.bid_terms.liquidated_damages} />
          <KV label="Force Majeure" value={bid.bid_terms.force_majeure} />
          <KV label="Discount" value={`${bid.bid_terms.discount_percentage}%`} />
        </div>
        {bid.bid_terms.notes && <p className="text-xs text-ghost-white mt-3"><span className="text-muted-silver">Notes:</span> {bid.bid_terms.notes}</p>}
      </DocSection>

      {/* ── Section 4: Bill of Quantities ── */}
      <DocSection num={4} title="BILL OF QUANTITIES / PRICE SCHEDULE">
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="bg-steel-slate/30 text-muted-silver">
                <th className="p-2 text-left border border-steel-slate/20">#</th>
                <th className="p-2 text-left border border-steel-slate/20">Product</th>
                <th className="p-2 text-left border border-steel-slate/20">OEM</th>
                <th className="p-2 text-left border border-steel-slate/20">Specification</th>
                <th className="p-2 text-center border border-steel-slate/20">Match</th>
                <th className="p-2 text-right border border-steel-slate/20">Qty</th>
                <th className="p-2 text-right border border-steel-slate/20">Unit Price</th>
                <th className="p-2 text-center border border-steel-slate/20">Disc%</th>
                <th className="p-2 text-right border border-steel-slate/20">Total</th>
              </tr>
            </thead>
            <tbody>
              {bid.line_items.map((li: any, i: number) => (
                <tr key={li.sr_no} className={i % 2 === 0 ? '' : 'bg-steel-slate/5'}>
                  <td className="p-2 border border-steel-slate/10 text-muted-silver">{li.sr_no}</td>
                  <td className="p-2 border border-steel-slate/10 text-ghost-white">
                    <p className="font-medium truncate max-w-[180px]">{li.product_name}</p>
                    <p className="text-[10px] text-muted-silver font-mono">{li.product_code}</p>
                  </td>
                  <td className="p-2 border border-steel-slate/10 text-electric-cyan">{li.oem}</td>
                  <td className="p-2 border border-steel-slate/10 text-muted-silver truncate max-w-[140px]">{li.specification}</td>
                  <td className="p-2 border border-steel-slate/10 text-center font-bold">
                    <span className={li.match_score >= 85 ? 'text-neon-emerald' : li.match_score >= 70 ? 'text-amber-glow' : 'text-coral-flame'}>{Math.round(li.match_score)}%</span>
                  </td>
                  <td className="p-2 border border-steel-slate/10 text-right text-ghost-white">{Number(li.quantity).toLocaleString()}</td>
                  <td className="p-2 border border-steel-slate/10 text-right text-ghost-white">{fmt(li.unit_price)}</td>
                  <td className="p-2 border border-steel-slate/10 text-center text-amber-glow">{li.discount_percent}%</td>
                  <td className="p-2 border border-steel-slate/10 text-right font-medium text-neon-emerald">{fmt(li.total_price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DocSection>

      {/* ── Section 5: Financial Summary & Budget ── */}
      <DocSection num={5} title="FINANCIAL SUMMARY & BUDGET BREAKDOWN">
        {/* Main totals */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          <FinCard label="Subtotal" value={fmt(bid.financial_summary.subtotal)} />
          <FinCard label={`Discount (${bid.financial_summary.discount_percentage}%)`} value={`${bid.financial_summary.discount_percentage}%`} />
          <FinCard label={`GST (${bid.financial_summary.gst_rate}%)`} value={fmt(bid.financial_summary.gst_amount)} />
          <FinCard label="Grand Total" value={fmt(bid.financial_summary.grand_total)} highlight />
        </div>
        {bid.financial_summary.amount_in_words && (
          <p className="text-xs text-muted-silver italic mb-4">In words: {bid.financial_summary.amount_in_words}</p>
        )}

        {/* Per-unit stats */}
        {bb.avg_unit_price != null && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4">
            <BudgetStat icon={<Package size={14} />} label="Items" value={String(bb.total_line_items)} color="cyan" />
            <BudgetStat icon={<BarChart3 size={14} />} label="Total Qty" value={Number(bb.total_quantity).toLocaleString()} color="cyan" />
            <BudgetStat icon={<DollarSign size={14} />} label="Avg Unit" value={fmt(bb.avg_unit_price)} color="emerald" />
            <BudgetStat icon={<Minus size={14} />} label="Min Unit" value={fmt(bb.min_unit_price)} color="amber" />
            <BudgetStat icon={<ArrowUpRight size={14} />} label="Max Unit" value={fmt(bb.max_unit_price)} color="amber" />
          </div>
        )}

        {/* RFP Estimated Value & EMD */}
        {(bb.rfp_estimated_value || bb.emd_amount) && (
          <div className="p-3 rounded-xl bg-electric-cyan/5 border border-electric-cyan/20 mb-4">
            <p className="text-[10px] text-electric-cyan uppercase tracking-wider mb-2">RFP Budget Reference</p>
            <div className="grid grid-cols-2 gap-3">
              {bb.rfp_estimated_value && <KV label="Estimated Value" value={bb.rfp_estimated_value} />}
              {bb.emd_amount && <KV label="EMD / Bid Security" value={bb.emd_amount} />}
            </div>
          </div>
        )}

        {/* OEM Cost Breakdown */}
        {bb.oem_breakdown?.length > 0 && (
          <div className="mb-4">
            <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-2">Cost by OEM / Manufacturer</p>
            <div className="space-y-1.5">
              {bb.oem_breakdown.map((ob: any) => (
                <div key={ob.oem} className="flex items-center gap-3">
                  <span className="text-xs text-electric-cyan font-medium w-28 truncate">{ob.oem}</span>
                  <div className="flex-1 h-2 rounded-full bg-steel-slate/20 overflow-hidden">
                    <div className="h-full rounded-full bg-electric-cyan/50" style={{ width: `${Math.min(ob.percentage, 100)}%` }} />
                  </div>
                  <span className="text-xs text-ghost-white font-mono w-24 text-right">{fmt(ob.total)}</span>
                  <span className="text-[10px] text-muted-silver w-14 text-right">{ob.items} items · {ob.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Category Breakdown */}
        {bb.category_breakdown?.length > 0 && (
          <div className="mb-4">
            <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-2">Cost by Voltage Category</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {bb.category_breakdown.map((cb: any) => (
                <div key={cb.category} className="p-3 rounded-lg bg-steel-slate/10 border border-steel-slate/15 text-center">
                  <p className="text-[10px] text-muted-silver truncate">{cb.category}</p>
                  <p className="text-sm font-bold text-ghost-white mt-0.5">{fmt(cb.total)}</p>
                  <p className="text-[10px] text-electric-cyan">{cb.percentage}%</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Pricing Comparison */}
        {bb.ai_estimated_total && (
          <div className="p-3 rounded-xl bg-violet-pulse/5 border border-violet-pulse/20">
            <p className="text-[10px] text-violet-pulse uppercase tracking-wider mb-2">AI Cost Comparison</p>
            <div className="grid grid-cols-3 gap-3">
              <KV label="AI Estimated" value={fmt(bb.ai_estimated_total)} />
              <KV label="Your Bid" value={fmt(bb.grand_total)} />
              <div>
                <p className="text-[10px] text-muted-silver">Margin</p>
                <p className={`text-sm font-semibold ${(bb.margin_vs_ai ?? 0) >= 0 ? 'text-neon-emerald' : 'text-coral-flame'}`}>
                  {fmt(Math.abs(bb.margin_vs_ai ?? 0))} ({bb.margin_pct_vs_ai}%)
                </p>
              </div>
            </div>
          </div>
        )}
      </DocSection>

      {/* ── Section 6: Technical Compliance ── */}
      <DocSection num={6} title="TECHNICAL COMPLIANCE SUMMARY">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <KV label="Total Requirements" value={String(bid.technical_compliance.total_requirements)} />
          <KV label="Wire/Cable Specs" value={String(bid.technical_compliance.wire_cable_specs)} />
          <KV label="Products Matched" value={String(bid.technical_compliance.matched_products)} />
          <KV label="Avg Match Score" value={`${bid.technical_compliance.average_match_score}%`} />
        </div>
        {bid.technical_compliance.standards_offered?.length > 0 && (
          <div className="mt-3">
            <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-1">Standards Offered</p>
            <p className="text-xs text-ghost-white">{bid.technical_compliance.standards_offered.join(', ')}</p>
          </div>
        )}
      </DocSection>

      {/* ── Section 7: OEM Summary ── */}
      {bid.oem_summary.total_oems > 0 && (
        <DocSection num={7} title="OEM / MANUFACTURER SUMMARY">
          <p className="text-xs text-ghost-white mb-2">
            <span className="text-muted-silver">Total OEMs:</span> {bid.oem_summary.total_oems} &nbsp;|&nbsp;
            <span className="text-muted-silver">Best OEM:</span> <span className="text-electric-cyan font-medium">{bid.oem_summary.best_oem}</span>
          </p>
          {bid.oem_summary.rankings?.length > 0 && (
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-steel-slate/30 text-muted-silver">
                  <th className="p-2 text-left border border-steel-slate/20">#</th>
                  <th className="p-2 text-left border border-steel-slate/20">OEM</th>
                  <th className="p-2 text-center border border-steel-slate/20">Products</th>
                  <th className="p-2 text-center border border-steel-slate/20">Avg Score</th>
                </tr>
              </thead>
              <tbody>
                {bid.oem_summary.rankings.map((r: any, i: number) => (
                  <tr key={i} className={i % 2 === 0 ? '' : 'bg-steel-slate/5'}>
                    <td className="p-2 border border-steel-slate/10 text-muted-silver">{i + 1}</td>
                    <td className="p-2 border border-steel-slate/10 text-electric-cyan font-medium">{r.oem}</td>
                    <td className="p-2 border border-steel-slate/10 text-center text-ghost-white">{r.product_count}</td>
                    <td className="p-2 border border-steel-slate/10 text-center text-ghost-white">{r.average_score?.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </DocSection>
      )}

      {/* ── Section 8: Bank Details ── */}
      {bid.company.bank_details?.name && (
        <DocSection num={8} title="BANK DETAILS (For Payment Reference)">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2">
            <KV label="Bank" value={bid.company.bank_details.name} />
            <KV label="Branch" value={bid.company.bank_details.branch} />
            <KV label="Account No." value={bid.company.bank_details.account} />
            <KV label="IFSC" value={bid.company.bank_details.ifsc} />
            <KV label="SWIFT" value={bid.company.bank_details.swift} />
          </div>
        </DocSection>
      )}

      {/* ── Section 9: Declaration ── */}
      <DocSection num={9} title="DECLARATION & AUTHORIZED SIGNATORY">
        <p className="text-xs text-muted-silver leading-relaxed mb-6">
          We hereby declare that the information furnished above is true and correct to the best of our
          knowledge and belief. We agree to abide by the terms and conditions mentioned in this bid document
          and the tender/RFP referenced herein. This bid is valid for the period stated above from the date of
          submission.
        </p>
        <div className="grid grid-cols-2 gap-8 mt-4">
          <div>
            <p className="text-[10px] text-muted-silver">For and on behalf of</p>
            <p className="text-sm font-bold text-ghost-white mt-1">{bid.company.name}</p>
            <div className="mt-8 border-t border-steel-slate/30 pt-2">
              <p className="text-sm font-semibold text-ghost-white">{bid.company.authorized_signatory}</p>
              <p className="text-xs text-muted-silver">{bid.company.signatory_designation}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-muted-silver">Date</p>
            <p className="text-sm text-ghost-white mt-1">
              {new Date(bid.generated_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })}
            </p>
            <p className="text-[10px] text-muted-silver mt-6">Seal / Stamp</p>
          </div>
        </div>
      </DocSection>

      {/* Footer action bar */}
      <div className="flex items-center justify-center gap-4 pt-4 border-t border-steel-slate/20">
        <button
          onClick={onDownload}
          disabled={downloading}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-electric-cyan/10 border border-electric-cyan/30 text-electric-cyan text-sm font-medium hover:bg-electric-cyan/20 transition-colors disabled:opacity-50"
        >
          {downloading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
          {downloading ? 'Generating...' : 'Download PDF'}
        </button>
        <p className="text-[10px] text-muted-silver">CONFIDENTIAL — For Addressee Only</p>
      </div>
    </div>
  );
}

function DocSection({ num, title, children }: { num: number; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-lg bg-electric-cyan/15 flex items-center justify-center text-xs font-bold text-electric-cyan">{num}</div>
        <h3 className="text-sm font-bold text-ghost-white uppercase tracking-wider">{title}</h3>
      </div>
      <div className="pl-9">{children}</div>
    </div>
  );
}

function KV({ label, value, className = '' }: { label: string; value: string; className?: string }) {
  return (
    <div className={className}>
      <p className="text-[10px] text-muted-silver uppercase tracking-wider">{label}</p>
      <p className="text-xs text-ghost-white font-medium mt-0.5 break-words">{value || '—'}</p>
    </div>
  );
}

function OptField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="text-xs text-muted-silver uppercase tracking-wider mb-1.5 block">{label}</label>
      <input
        type="text" value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/40 focus:outline-none focus:border-neon-emerald/40 transition-colors"
      />
    </div>
  );
}

function OptSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <div>
      <label className="text-xs text-muted-silver uppercase tracking-wider mb-1.5 block">{label}</label>
      <select
        value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2.5 rounded-xl glass-input text-sm text-ghost-white bg-transparent focus:outline-none focus:border-neon-emerald/40 transition-colors"
      >
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}
