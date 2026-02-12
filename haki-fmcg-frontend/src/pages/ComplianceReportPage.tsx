import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Download,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Shield,
  Printer,
  CalendarDays,
  Building2,
  ChevronDown,
  ChevronRight,
  Search,
  Loader2,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface Standard {
  code: string;
  name: string;
  status: 'pass' | 'fail' | 'warning';
  details: string;
  risk: 'low' | 'medium' | 'high' | 'critical';
  recommendation?: string;
}

interface ReportData {
  product: string;
  sku: string;
  vendor: string;
  generatedAt: string;
  overallScore: number;
  standards: Standard[];
  riskSummary: { low: number; medium: number; high: number; critical: number };
  signoff: { name: string; role: string; date: string }[];
}

/* ─── mock data ─── */
const PRODUCTS = [
  { sku: 'FNX-LT-4C185', name: 'Finolex LT 4C×185 sq mm XLPE Cable', vendor: 'Finolex Cables Ltd' },
  { sku: 'PLR-HT-1C400', name: 'Polycab HT 1C×400 sq mm Cable', vendor: 'Polycab India Ltd' },
  { sku: 'KEI-CC-10P15', name: 'KEI Control Cable 10P×1.5 sq mm', vendor: 'KEI Industries' },
  { sku: 'HAV-FR-1C6', name: 'Havells FR 1C×6 sq mm House Wire', vendor: 'Havells India Ltd' },
];

const buildReport = (sku: string): ReportData => {
  const prod = PRODUCTS.find((p) => p.sku === sku)!;
  const standards: Standard[] = [
    { code: 'IS 7098-1', name: 'XLPE Insulated PVC Sheathed Cables', status: 'pass', risk: 'low', details: 'Conductor resistance, insulation thickness, and voltage test within limits.' },
    { code: 'IS 1554-1', name: 'PVC Insulated Cables', status: 'pass', risk: 'low', details: 'PVC sheath compliant with thickness and ageing requirements.' },
    { code: 'IEC 60502', name: 'Power Cables 1-30 kV', status: 'pass', risk: 'low', details: 'Partial discharge, bending test, and impulse voltage test passed.' },
    { code: 'IS 694', name: 'PVC Insulated Switch Wires', status: 'warning', risk: 'medium', details: 'Flame retardancy test borderline — 24s self-extinguish time (limit 30s).', recommendation: 'Request updated type-test report from vendor; consider FR-LSH variant.' },
    { code: 'BIS CM/L-2345', name: 'BIS License Verification', status: 'pass', risk: 'low', details: 'License active, last renewed Jan 2025, valid until Dec 2026.' },
    { code: 'RoHS 2011/65/EU', name: 'Restriction of Hazardous Substances', status: 'fail', risk: 'high', details: 'Lead content in solder 0.12% (limit 0.1%). Non-compliant.', recommendation: 'Vendor must provide RoHS declaration with updated test certificate. Reject lot if export-bound.' },
    { code: 'ISO 9001:2015', name: 'Quality Management System', status: 'pass', risk: 'low', details: 'QMS certificate valid. Last audit: Aug 2025.' },
    { code: 'CPRI Type Test', name: 'Central Power Research Inst. Test', status: 'pass', risk: 'low', details: 'Type test report available — Report No. CPRI/ET/2024/1123, dated 15 Nov 2024.' },
    { code: 'IS 10810-3', name: 'Cable Fire Performance', status: 'warning', risk: 'medium', details: 'Smoke density above IS 10810-3 threshold: 1.08 OD/m (limit 1.0).', recommendation: 'Suitable for non-fire-critical zones only. Flag for tunnel installations.' },
  ];
  const riskSummary = { low: standards.filter((s) => s.risk === 'low').length, medium: standards.filter((s) => s.risk === 'medium').length, high: standards.filter((s) => s.risk === 'high').length, critical: 0 };
  return {
    product: prod.name, sku: prod.sku, vendor: prod.vendor,
    generatedAt: new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }),
    overallScore: 78,
    standards,
    riskSummary,
    signoff: [
      { name: 'Rajesh Kumar', role: 'QA Manager', date: '' },
      { name: 'Priya Sharma', role: 'Compliance Head', date: '' },
    ],
  };
};

const riskColor: Record<string, string> = {
  low: 'text-neon-emerald bg-neon-emerald/10 border-neon-emerald/25',
  medium: 'text-amber-glow bg-amber-glow/10 border-amber-glow/25',
  high: 'text-coral-flame bg-coral-flame/10 border-coral-flame/25',
  critical: 'text-coral-flame bg-coral-flame/15 border-coral-flame/40 animate-pulse',
};

const statusIcon = (s: string) => s === 'pass' ? <CheckCircle2 size={14} className="text-neon-emerald" /> : s === 'fail' ? <XCircle size={14} className="text-coral-flame" /> : <AlertTriangle size={14} className="text-amber-glow" />;

export default function ComplianceReportPage() {
  const [selectedSku, setSelectedSku] = useState('');
  const [report, setReport] = useState<ReportData | null>(null);
  const [generating, setGenerating] = useState(false);
  const [expanded, setExpanded] = useState<string[]>([]);
  const [search, setSearch] = useState('');

  const generate = () => {
    if (!selectedSku) return;
    setGenerating(true);
    setTimeout(() => {
      setReport(buildReport(selectedSku));
      setGenerating(false);
    }, 1400);
  };

  const toggleExpand = (code: string) => setExpanded((p) => p.includes(code) ? p.filter((c) => c !== code) : [...p, code]);

  const filteredStandards = report?.standards.filter((s) => s.name.toLowerCase().includes(search.toLowerCase()) || s.code.toLowerCase().includes(search.toLowerCase()));

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/compliance" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
          <ArrowLeft size={18} className="text-muted-silver" />
        </Link>
        <div className="flex-1">
          <h1 className="text-h1 text-ghost-white">Compliance Report Generator</h1>
          <p className="text-body text-muted-silver">Generate official compliance reports for products</p>
        </div>
        {report && (
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" leftIcon={<Printer size={14} />}>Print</Button>
            <Button size="sm" leftIcon={<Download size={14} />}>Export PDF</Button>
          </div>
        )}
      </div>

      {/* Product Selector */}
      <Card variant="glass" className="p-4">
        <div className="flex flex-col md:flex-row gap-3 items-end">
          <div className="flex-1">
            <label className="text-xs text-muted-silver mb-1 block">Select Product</label>
            <select
              value={selectedSku}
              onChange={(e) => { setSelectedSku(e.target.value); setReport(null); }}
              className="glass-input w-full rounded-lg px-3 py-2 text-sm text-ghost-white"
            >
              <option value="">— Choose a product —</option>
              {PRODUCTS.map((p) => <option key={p.sku} value={p.sku}>{p.name} ({p.sku})</option>)}
            </select>
          </div>
          <Button onClick={generate} disabled={!selectedSku || generating} leftIcon={generating ? <Loader2 size={14} className="animate-spin" /> : <Shield size={14} />}>
            {generating ? 'Generating...' : 'Generate Report'}
          </Button>
        </div>
      </Card>

      <AnimatePresence mode="wait">
        {report && (
          <motion.div key="report" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
            {/* Report Header */}
            <Card variant="glass" className="p-5">
              <div className="flex flex-col md:flex-row md:items-center gap-4">
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <FileText size={16} className="text-electric-cyan" />
                    <h2 className="text-sm font-bold text-ghost-white">Compliance Assessment Report</h2>
                  </div>
                  <p className="text-xs text-muted-silver">{report.product}</p>
                  <div className="flex flex-wrap gap-3 text-[11px] text-muted-silver">
                    <span className="flex items-center gap-1"><Building2 size={11} />{report.vendor}</span>
                    <span className="font-mono">{report.sku}</span>
                    <span className="flex items-center gap-1"><CalendarDays size={11} />{report.generatedAt}</span>
                  </div>
                </div>
                {/* Overall Score */}
                <div className="text-center">
                  <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center mx-auto ${report.overallScore >= 80 ? 'border-neon-emerald text-neon-emerald' : report.overallScore >= 60 ? 'border-amber-glow text-amber-glow' : 'border-coral-flame text-coral-flame'}`}>
                    <span className="text-lg font-bold">{report.overallScore}</span>
                  </div>
                  <span className="text-[10px] text-muted-silver">Overall Score</span>
                </div>
              </div>

              {/* Risk Summary */}
              <div className="grid grid-cols-4 gap-2 mt-4">
                {(['low', 'medium', 'high', 'critical'] as const).map((level) => (
                  <div key={level} className={`p-2 rounded-lg border text-center text-xs ${riskColor[level]}`}>
                    <span className="text-lg font-bold block">{report.riskSummary[level]}</span>
                    <span className="uppercase text-[9px] tracking-wider">{level}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Standards Results */}
            <Card variant="glass" className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-ghost-white">Standards Checked ({report.standards.length})</h3>
                <div className="relative w-48">
                  <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-silver" />
                  <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search standards..." className="glass-input w-full rounded-lg pl-7 pr-3 py-1.5 text-xs text-ghost-white" />
                </div>
              </div>
              <div className="space-y-1.5">
                {filteredStandards?.map((std) => {
                  const isExpanded = expanded.includes(std.code);
                  return (
                    <div key={std.code} className="rounded-lg border border-steel-slate/15 overflow-hidden">
                      <button onClick={() => toggleExpand(std.code)} className="w-full flex items-center gap-3 p-3 hover:bg-steel-slate/5 text-left transition-colors">
                        {statusIcon(std.status)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono text-electric-cyan">{std.code}</span>
                            <span className="text-xs text-ghost-white truncate">{std.name}</span>
                          </div>
                        </div>
                        <Badge variant="soft" color={std.risk === 'low' ? 'green' : std.risk === 'medium' ? 'amber' : 'red'} size="sm">{std.risk.toUpperCase()}</Badge>
                        {isExpanded ? <ChevronDown size={12} className="text-muted-silver" /> : <ChevronRight size={12} className="text-muted-silver" />}
                      </button>
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
                            <div className="px-3 pb-3 pt-0 space-y-2">
                              <p className="text-xs text-muted-silver leading-relaxed">{std.details}</p>
                              {std.recommendation && (
                                <div className="flex items-start gap-2 p-2 rounded-lg bg-amber-glow/5 border border-amber-glow/15">
                                  <AlertTriangle size={12} className="text-amber-glow flex-shrink-0 mt-0.5" />
                                  <p className="text-[11px] text-amber-glow">{std.recommendation}</p>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </div>
            </Card>

            {/* Sign-off Section */}
            <Card variant="glass" className="p-4">
              <h3 className="text-sm font-semibold text-ghost-white mb-3">Authorization Sign-off</h3>
              <div className="grid md:grid-cols-2 gap-3">
                {report.signoff.map((s) => (
                  <div key={s.name} className="p-3 rounded-lg border border-dashed border-steel-slate/25 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-violet-pulse/15 flex items-center justify-center text-violet-pulse text-xs font-bold">{s.name.split(' ').map((w) => w[0]).join('')}</div>
                    <div className="flex-1">
                      <p className="text-xs text-ghost-white font-semibold">{s.name}</p>
                      <p className="text-[10px] text-muted-silver">{s.role}</p>
                    </div>
                    <div className="border-b border-muted-silver/20 w-20 text-center">
                      <span className="text-[9px] text-muted-silver">Signature</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
