import { useState } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  Download,
  Printer,
  Mail,
  Eye,
  GripVertical,
  Layers,
  CheckCircle2,
  FileCheck2,
  Sun,
  Moon,
  ShieldCheck,
  Building2,
  Check,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface Section {
  id: string;
  title: string;
  visible: boolean;
  content: string;
}

/* ─── template configurations ─── */
interface TemplateConfig {
  id: string;
  name: string;
  desc: string;
  badge: string;
  activeSections: string[];
}

const TEMPLATES: TemplateConfig[] = [
  {
    id: 'standard',
    name: 'Standard Template',
    desc: 'Default commercial & technical layout',
    badge: 'Standard',
    activeSections: ['cover', 'scope', 'pricing', 'terms', 'compliance'],
  },
  {
    id: 'detailed',
    name: 'Detailed Technical',
    desc: 'Extended specs, GTP sheet & compliance',
    badge: 'Technical Dossier',
    activeSections: ['cover', 'exec_summary', 'scope', 'gtp', 'pricing', 'compliance', 'terms', 'annexures'],
  },
  {
    id: 'executive',
    name: 'Executive Summary',
    desc: 'High-level strategy & financials for C-suite',
    badge: 'Executive Brief',
    activeSections: ['cover', 'exec_summary', 'pricing', 'compliance', 'terms'],
  },
];

const GTP_SPECIFICATIONS = [
  { parameter: 'Voltage Grade', tenderReq: '1.1 kV (1100V) Grade', offeredSpec: '1.1 kV Heavy Duty Grade', status: 'Met (100%)' },
  { parameter: 'Conductor Material', tenderReq: 'Electrolytic Grade Aluminum IS 8130', offeredSpec: 'Class-2 Stranded H2/H4 Aluminum', status: 'Met (100%)' },
  { parameter: 'Insulation Type', tenderReq: 'Cross-linked Polyethylene (XLPE)', offeredSpec: 'Virgin XLPE as per IS 7098 (Part 1)', status: 'Met (100%)' },
  { parameter: 'Inner Sheath', tenderReq: 'Extruded PVC Type ST-2', offeredSpec: 'Continuous Extruded Type ST-2 PVC', status: 'Met (100%)' },
  { parameter: 'Armouring Spec', tenderReq: 'Galvanized Steel Strip / Wire IS 3975', offeredSpec: 'Galvanized Steel Formed Wire / Strip', status: 'Met (100%)' },
  { parameter: 'Outer Sheath Flame', tenderReq: 'FRLS (Flame Retardant Low Smoke)', offeredSpec: 'Oxygen Index > 29%, Temp Index > 250°C', status: 'Met (100%)' },
  { parameter: 'Continuous Rating', tenderReq: 'Min 420 Amps in Ground / 460 Amps in Air', offeredSpec: '435 Amps in Ground / 478 Amps in Air', status: 'Exceeds Req' },
];

const PRICING_ITEMS = [
  { item: 'LT Power Cable 240 sq mm 3.5C XLPE Armoured', unit: 'meter', qty: 15000, rate: 1850, gst: 18 },
  { item: 'LT Control Cable 2.5 sq mm 12 Core Copper', unit: 'meter', qty: 5000, rate: 320, gst: 18 },
  { item: 'Straight-Through Jointing Kits (Heat Shrink)', unit: 'nos', qty: 120, rate: 4500, gst: 18 },
  { item: 'Cable Glands (Double Compression, Heavy Brass)', unit: 'nos', qty: 240, rate: 850, gst: 18 },
];

function formatINR(n: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
}

export default function BidDocumentPreviewPage() {
  const { id } = useParams();
  const bidId = id || 'B-4418';
  const rfpRef = bidId.startsWith('B-') ? `RFP-2026-${bidId.replace('B-', '')}` : 'RFP-2026-4418';

  const [template, setTemplate] = useState('standard');
  const [docTheme, setDocTheme] = useState<'paper' | 'dark'>('paper');

  const [sections, setSections] = useState<Section[]>([
    {
      id: 'cover',
      title: 'Cover Page',
      visible: true,
      content: `Saarthi\nBid Response & Commercial Proposal\n\nReference: ${bidId}\nDate of Submission: October 16, 2026\n\nPrepared for: Central Tender Procurement Authority\nRFP Reference: ${rfpRef}\nSubject: Supply of LT Power Cables & Industrial Distribution Hardware`,
    },
    {
      id: 'exec_summary',
      title: 'Executive Summary & Win Strategy',
      visible: false,
      content: `Saarthi Procurement submits this comprehensive proposal engineered to deliver 100% statutory, technical, and logistical compliance for tender ${rfpRef}.\n\nStrategic Highlights:\n  • Zero-Lag Delivery: 60% dispatch within 6 weeks, balance 40% within 10 weeks of Purchase Order.\n  • Full Certification: NABL type-tested cable design, conforming to IS 1554 (Part 1), IS 694, and IEC 60502-1.\n  • Price Assurance: Firm landed prices inclusive of freight, packing, transit insurance, and GST.\n  • Warranty: 18-month comprehensive on-site replacement warranty backed by manufacturer undertaking.`,
    },
    {
      id: 'scope',
      title: 'Scope of Supply & Bill of Quantities',
      visible: true,
      content: `1. LT Power Cable, 240 sq mm, 3.5 Core XLPE — 15,000 meters\n2. LT Control Cable, 2.5 sq mm, 12 Core — 5,000 meters\n3. Jointing Kits (Heat Shrink) — 120 sets\n4. Cable Glands (Double Compression, Brass) — 240 sets\n\nDelivery Milestones:\n  • Phase 1 (60%): Within 6 weeks of PO issuance\n  • Phase 2 (40%): Within 10 weeks of PO issuance\n\nManufacturer: Saarthi Partner Works\nStandard Compliance: IS 1554 Part 1, IS 694, IEC 60502-1`,
    },
    {
      id: 'gtp',
      title: 'Guaranteed Technical Particulars (GTP)',
      visible: false,
      content: 'Detailed specifications comparison table',
    },
    {
      id: 'pricing',
      title: 'Commercial Price Schedule & BOQ',
      visible: true,
      content: 'Commercial pricing breakdown table',
    },
    {
      id: 'compliance',
      title: 'Compliance & Mandatory Certifications',
      visible: true,
      content: `Standards & Norms Compliance:\n  ✅ IS 1554 Part 1 — PVC Insulated Heavy Duty Cables\n  ✅ IS 7098 Part 1 — Cross-Linked Polyethylene Insulated Cables\n  ✅ IS 8130 — Conductors for Insulated Electric Cables\n  ✅ IEC 60502-1 — Extruded Solid Dielectric Power Cables\n\nAccreditations & Certificates:\n  • ISO 9001:2015 Quality Management System (Valid till Dec 2027)\n  • ISO 14001:2015 Environmental System\n  • Bureau of Indian Standards (BIS) License: CM/L-8492019\n  • Type Test Certificate from CPRI / ERDA valid for 5 years`,
    },
    {
      id: 'terms',
      title: 'Commercial Terms & General Conditions',
      visible: true,
      content: `1. Payment Terms: 100% payment within 30 days of receipt and verification of material at site.\n2. Price Validity: 90 calendar days from the date of bid submission.\n3. Warranty Period: 18 months from delivery or 12 months from commissioning, whichever is earlier.\n4. Liquidated Damages: 0.5% per week of delayed portion, capped at maximum 5% of total contract value.\n5. Transit Insurance: Comprehensive door-to-door transit insurance covered by bidder.\n6. Testing & Inspection: Factory Acceptance Test (FAT) by buyer's representative prior to dispatch.\n7. Dispute Resolution: Arbitration in accordance with Indian Arbitration & Conciliation Act, 1996.`,
    },
    {
      id: 'annexures',
      title: 'Annexures & Quality Assurance Plan',
      visible: false,
      content: `Annexure A — Certified CPRI / ERDA Type Test Reports\nAnnexure B — Factory Inspection Routine Test Certificates\nAnnexure C — Bar Chart Project Delivery Schedule\nAnnexure D — Past Performance & Reference Work Orders from Major Utilities`,
    },
  ]);

  const subtotal = PRICING_ITEMS.reduce((s, i) => s + i.qty * i.rate, 0);
  const gstTotal = PRICING_ITEMS.reduce((s, i) => s + i.qty * i.rate * (i.gst / 100), 0);
  const grandTotal = subtotal + gstTotal;

  // Handle template selection and dynamically toggle sections
  const handleTemplateSelect = (templateId: string) => {
    setTemplate(templateId);
    const cfg = TEMPLATES.find((t) => t.id === templateId);
    if (!cfg) return;

    setSections((prev) =>
      prev.map((s) => ({
        ...s,
        visible: cfg.activeSections.includes(s.id),
      }))
    );
    toast.success(`Switched to ${cfg.name} layout!`);
  };

  const toggleSection = (sectionId: string) => {
    setSections((prev) => prev.map((s) => (s.id === sectionId ? { ...s, visible: !s.visible } : s)));
  };

  const handlePrint = () => {
    window.print();
  };

  const handleEmail = () => {
    window.open(
      `mailto:?subject=Bid Proposal ${bidId} (${rfpRef})&body=Attached is the commercial bid proposal generated via Saarthi procurement engine for tender ${rfpRef}.`
    );
    toast.success('Email client opened with draft proposal!');
  };

  const handleExportPDF = () => {
    toast.loading(`Generating PDF document for ${bidId}...`, { duration: 1200 });
    setTimeout(() => {
      window.print();
    }, 700);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/bids"
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-steel-slate/20 dark:hover:bg-steel-slate/30 transition-colors text-slate-700 dark:text-muted-silver"
          >
            <ArrowLeft size={18} />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-ghost-white">
                Bid Document Preview
              </h1>
              <Badge variant="soft" color="cyan" size="sm">
                {bidId}
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-muted-silver mt-0.5">
              RFP Reference: <span className="font-semibold text-slate-900 dark:text-ghost-white">{rfpRef}</span> — Commercial Proposal & Technical Dossier
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Paper View / Dark View Toggle */}
          <div className="flex items-center rounded-xl bg-slate-100 dark:bg-steel-slate/20 p-1 border border-slate-200 dark:border-steel-slate/30">
            <button
              onClick={() => setDocTheme('paper')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                docTheme === 'paper'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 dark:text-muted-silver hover:text-slate-900'
              }`}
              title="Crystal-clear high-contrast document paper view"
            >
              <Sun size={13} className="text-amber-500" />
              Paper Mode
            </button>
            <button
              onClick={() => setDocTheme('dark')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                docTheme === 'dark'
                  ? 'bg-slate-800 text-electric-cyan shadow-sm'
                  : 'text-slate-600 dark:text-muted-silver hover:text-ghost-white'
              }`}
              title="Dark Studio preview"
            >
              <Moon size={13} className="text-electric-cyan" />
              Dark Mode
            </button>
          </div>

          <Button variant="secondary" size="sm" leftIcon={<Printer size={14} />} onClick={handlePrint}>
            Print
          </Button>
          <Button variant="secondary" size="sm" leftIcon={<Mail size={14} />} onClick={handleEmail}>
            Email
          </Button>
          <Button variant="primary" size="sm" leftIcon={<Download size={14} />} onClick={handleExportPDF}>
            Export PDF
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[290px_1fr] gap-6">
        {/* ── Left Sidebar Controls ── */}
        <div className="space-y-4">
          {/* Template Selector */}
          <Card variant="glass" className="p-4 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-ghost-white flex items-center gap-1.5">
              <Layers size={14} className="text-electric-cyan" /> Select Template
            </h3>

            <div className="space-y-2">
              {TEMPLATES.map((t) => {
                const isSelected = template === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => handleTemplateSelect(t.id)}
                    className={`w-full text-left px-3.5 py-2.5 rounded-xl transition-all duration-200 border cursor-pointer ${
                      isSelected
                        ? 'bg-electric-cyan/15 border-electric-cyan text-slate-900 dark:text-ghost-white shadow-sm ring-1 ring-electric-cyan/50'
                        : 'bg-slate-50 dark:bg-steel-slate/10 border-slate-200 dark:border-steel-slate/20 hover:border-slate-300 dark:hover:border-steel-slate/40 text-slate-700 dark:text-muted-silver'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-bold ${isSelected ? 'text-blue-600 dark:text-electric-cyan' : 'text-slate-800 dark:text-ghost-white'}`}>
                        {t.name}
                      </span>
                      {isSelected && <Check size={14} className="text-blue-600 dark:text-electric-cyan" />}
                    </div>
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Section Visibility & Ordering */}
          <Card variant="glass" className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-ghost-white flex items-center gap-1.5">
                <GripVertical size={14} className="text-electric-cyan" /> Sections Order
              </h3>
              <span className="text-[11px] font-semibold text-slate-500 dark:text-muted-silver">
                {sections.filter((s) => s.visible).length}/{sections.length} Active
              </span>
            </div>

            <Reorder.Group values={sections} onReorder={setSections} className="space-y-1.5">
              {sections.map((s) => (
                <Reorder.Item
                  key={s.id}
                  value={s}
                  className={`flex items-center gap-2 p-2 rounded-lg text-xs transition-colors cursor-grab active:cursor-grabbing border ${
                    s.visible
                      ? 'bg-white dark:bg-steel-slate/15 border-slate-200 dark:border-steel-slate/25 text-slate-800 dark:text-ghost-white'
                      : 'bg-slate-100/60 dark:bg-steel-slate/5 border-slate-200/50 dark:border-steel-slate/10 text-slate-400 dark:text-muted-silver/50'
                  }`}
                >
                  <GripVertical size={13} className="text-slate-400 dark:text-muted-silver/40 shrink-0" />
                  <span className={`flex-1 font-medium truncate ${!s.visible ? 'line-through' : ''}`}>
                    {s.title}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSection(s.id);
                    }}
                    className={`p-1 rounded hover:bg-slate-200 dark:hover:bg-steel-slate/30 transition-colors ${
                      s.visible ? 'text-emerald-600 dark:text-neon-emerald' : 'text-slate-400 dark:text-muted-silver/40'
                    }`}
                    title={s.visible ? 'Hide section' : 'Show section'}
                  >
                    <Eye size={13} />
                  </button>
                </Reorder.Item>
              ))}
            </Reorder.Group>
          </Card>

          {/* Bid Summary Meta */}
          <Card variant="glass" className="p-4 space-y-2.5 text-xs">
            <h4 className="font-bold text-slate-900 dark:text-ghost-white flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-emerald-500" /> Commercial Guarantee
            </h4>
            <div className="space-y-1 text-slate-600 dark:text-muted-silver">
              <div className="flex justify-between">
                <span>Total Value:</span>
                <span className="font-bold font-mono text-slate-900 dark:text-ghost-white">{formatINR(grandTotal)}</span>
              </div>
              <div className="flex justify-between">
                <span>Bidder:</span>
                <span className="font-medium text-slate-900 dark:text-ghost-white">Haki FMCG Procurement</span>
              </div>
              <div className="flex justify-between">
                <span>Target RFP:</span>
                <span className="font-mono text-slate-900 dark:text-ghost-white">{rfpRef}</span>
              </div>
            </div>
          </Card>
        </div>

        {/* ── Right Panel — Document Canvas ── */}
        <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-steel-slate/30 shadow-xl bg-slate-100 dark:bg-[#070b19] p-2 sm:p-6">
          <div className="flex items-center justify-between pb-3 px-2 border-b border-slate-200 dark:border-steel-slate/20 text-xs mb-4">
            <div className="flex items-center gap-2">
              <FileCheck2 size={16} className="text-blue-600 dark:text-electric-cyan" />
              <span className="font-bold text-slate-900 dark:text-ghost-white">
                Live Document Preview ({TEMPLATES.find((t) => t.id === template)?.name})
              </span>
            </div>
            <span className="text-[11px] font-semibold text-slate-500 dark:text-muted-silver">
              Page 1 of 1 · Print Ready A4
            </span>
          </div>

          {/* Actual Document Sheet with 100% High Readability */}
          <div
            className={`min-h-[850px] rounded-xl p-6 sm:p-10 shadow-2xl transition-all duration-300 space-y-6 ${
              docTheme === 'paper'
                ? 'bg-white text-slate-900 border border-slate-200'
                : 'bg-[#0f172a] text-slate-100 border border-slate-700'
            }`}
            style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" }}
          >
            <AnimatePresence mode="popLayout">
              {sections
                .filter((s) => s.visible)
                .map((section) => (
                  <motion.div
                    key={section.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className={`rounded-xl overflow-hidden border transition-all ${
                      docTheme === 'paper'
                        ? 'border-slate-200 bg-white shadow-sm'
                        : 'border-slate-700/80 bg-[#141e33] shadow-md'
                    }`}
                  >
                    {/* Section Header */}
                    <div
                      className={`px-5 py-3 border-b flex items-center justify-between ${
                        docTheme === 'paper'
                          ? 'bg-slate-50 border-slate-200 text-slate-900'
                          : 'bg-slate-800/90 border-slate-700 text-cyan-300'
                      }`}
                    >
                      <h3 className="text-sm sm:text-base font-bold tracking-tight flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-600 dark:bg-electric-cyan" />
                        {section.title}
                      </h3>
                    </div>

                    {/* Section Body */}
                    <div className="p-5 sm:p-6">
                      {/* Cover Page */}
                      {section.id === 'cover' && (
                        <div className="text-center py-6 sm:py-8 space-y-4">
                          <div
                            className={`w-16 h-16 rounded-2xl mx-auto flex items-center justify-center shadow-md ${
                              docTheme === 'paper'
                                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                : 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30'
                            }`}
                          >
                            <Building2 size={32} />
                          </div>
                          <div>
                            <h2
                              className={`text-xl sm:text-2xl font-black tracking-tight ${
                                docTheme === 'paper' ? 'text-slate-950' : 'text-white'
                              }`}
                            >
                              Saarthi
                            </h2>
                            <p
                              className={`text-sm sm:text-base font-bold mt-1 ${
                                docTheme === 'paper' ? 'text-blue-700' : 'text-electric-cyan'
                              }`}
                            >
                              Official Bid Response & Commercial Proposal
                            </p>
                          </div>

                          <div
                            className={`max-w-md mx-auto p-4 rounded-xl border text-xs sm:text-sm space-y-1.5 ${
                              docTheme === 'paper'
                                ? 'bg-slate-50 border-slate-200 text-slate-800'
                                : 'bg-slate-800/60 border-slate-700 text-slate-200'
                            }`}
                          >
                            <div className="flex justify-between py-0.5">
                              <span className="font-semibold text-slate-500 dark:text-slate-400">Bid Reference:</span>
                              <span className="font-mono font-bold text-blue-700 dark:text-electric-cyan">{bidId}</span>
                            </div>
                            <div className="flex justify-between py-0.5">
                              <span className="font-semibold text-slate-500 dark:text-slate-400">Target RFP:</span>
                              <span className="font-mono font-bold">{rfpRef}</span>
                            </div>
                            <div className="flex justify-between py-0.5">
                              <span className="font-semibold text-slate-500 dark:text-slate-400">Bidder Name:</span>
                              <span className="font-bold">Saarthi Works Ltd</span>
                            </div>
                            <div className="flex justify-between py-0.5">
                              <span className="font-semibold text-slate-500 dark:text-slate-400">Submission Date:</span>
                              <span>October 16, 2026</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Guaranteed Technical Particulars (GTP) Specification Table */}
                      {section.id === 'gtp' && (
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs sm:text-sm text-left border-collapse">
                            <thead>
                              <tr
                                className={`border-b font-bold text-xs uppercase tracking-wider ${
                                  docTheme === 'paper'
                                    ? 'bg-slate-100 text-slate-800 border-slate-200'
                                    : 'bg-slate-800 text-slate-300 border-slate-700'
                                }`}
                              >
                                <th className="p-3">Technical Parameter</th>
                                <th className="p-3">Tender Specification</th>
                                <th className="p-3">Offered Specification</th>
                                <th className="p-3 text-right">Compliance</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                              {GTP_SPECIFICATIONS.map((item, idx) => (
                                <tr
                                  key={idx}
                                  className={
                                    docTheme === 'paper'
                                      ? idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/70'
                                      : idx % 2 === 0 ? 'bg-transparent' : 'bg-slate-800/30'
                                  }
                                >
                                  <td className="p-3 font-semibold text-slate-900 dark:text-white">{item.parameter}</td>
                                  <td className="p-3 text-slate-700 dark:text-slate-300">{item.tenderReq}</td>
                                  <td className="p-3 font-medium text-slate-800 dark:text-slate-200">{item.offeredSpec}</td>
                                  <td className="p-3 text-right">
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-700">
                                      <CheckCircle2 size={11} /> {item.status}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {/* Pricing Table */}
                      {section.id === 'pricing' && (
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs sm:text-sm text-left border-collapse">
                            <thead>
                              <tr
                                className={`border-b font-bold text-xs uppercase tracking-wider ${
                                  docTheme === 'paper'
                                    ? 'bg-slate-100 text-slate-800 border-slate-200'
                                    : 'bg-slate-800 text-slate-300 border-slate-700'
                                }`}
                              >
                                <th className="p-3">#</th>
                                <th className="p-3">Item Description</th>
                                <th className="p-3 text-center">Unit</th>
                                <th className="p-3 text-right">Qty</th>
                                <th className="p-3 text-right">Rate (₹)</th>
                                <th className="p-3 text-right">Amount (₹)</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                              {PRICING_ITEMS.map((item, idx) => (
                                <tr
                                  key={idx}
                                  className={
                                    docTheme === 'paper'
                                      ? idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/70'
                                      : idx % 2 === 0 ? 'bg-transparent' : 'bg-slate-800/30'
                                  }
                                >
                                  <td className="p-3 text-slate-500">{idx + 1}</td>
                                  <td className="p-3 font-semibold text-slate-900 dark:text-white">{item.item}</td>
                                  <td className="p-3 text-center text-slate-600 dark:text-slate-400">{item.unit}</td>
                                  <td className="p-3 text-right font-mono font-medium text-slate-900 dark:text-white">
                                    {item.qty.toLocaleString('en-IN')}
                                  </td>
                                  <td className="p-3 text-right font-mono text-slate-900 dark:text-white">
                                    {item.rate.toLocaleString('en-IN')}
                                  </td>
                                  <td className="p-3 text-right font-mono font-bold text-slate-950 dark:text-white">
                                    {(item.qty * item.rate).toLocaleString('en-IN')}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>

                          {/* Commercial Summary Box */}
                          <div
                            className={`mt-4 pt-4 border-t space-y-1.5 text-xs sm:text-sm ${
                              docTheme === 'paper' ? 'border-slate-200 text-slate-700' : 'border-slate-700 text-slate-300'
                            }`}
                          >
                            <div className="flex justify-end gap-10">
                              <span className="font-medium text-slate-500 dark:text-slate-400">Net Basic Subtotal:</span>
                              <span className="font-mono font-bold w-36 text-right text-slate-900 dark:text-white">
                                {formatINR(subtotal)}
                              </span>
                            </div>
                            <div className="flex justify-end gap-10">
                              <span className="font-medium text-slate-500 dark:text-slate-400">GST @ 18%:</span>
                              <span className="font-mono font-bold w-36 text-right text-slate-900 dark:text-white">
                                {formatINR(gstTotal)}
                              </span>
                            </div>
                            <div
                              className={`flex justify-end gap-10 pt-2 border-t font-bold text-base ${
                                docTheme === 'paper'
                                  ? 'border-slate-300 text-blue-700'
                                  : 'border-slate-600 text-electric-cyan'
                              }`}
                            >
                              <span>Total Landed Bid Amount:</span>
                              <span className="font-mono text-right w-36">{formatINR(grandTotal)}</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Formatted Text Sections (Scope, Exec Summary, Terms, Compliance, Annexures) */}
                      {section.id !== 'cover' && section.id !== 'pricing' && section.id !== 'gtp' && (
                        <div
                          className={`text-xs sm:text-sm leading-relaxed space-y-2 ${
                            docTheme === 'paper' ? 'text-slate-800' : 'text-slate-200'
                          }`}
                        >
                          {section.content.split('\n').map((line, i) => {
                            const trimmed = line.trim();
                            if (!trimmed) return <div key={i} className="h-1" />;

                            if (trimmed.startsWith('✅')) {
                              return (
                                <div key={i} className="flex items-center gap-2 font-medium text-emerald-700 dark:text-emerald-400">
                                  <CheckCircle2 size={14} className="shrink-0" />
                                  <span>{trimmed.replace('✅', '').trim()}</span>
                                </div>
                              );
                            }

                            if (trimmed.startsWith('•')) {
                              return (
                                <div key={i} className="flex items-start gap-2 pl-2">
                                  <span className="text-blue-600 dark:text-cyan-400 font-bold shrink-0">•</span>
                                  <span className="font-normal">{trimmed.replace('•', '').trim()}</span>
                                </div>
                              );
                            }

                            if (/^\d+\./.test(trimmed)) {
                              return (
                                <div
                                  key={i}
                                  className={`p-2.5 rounded-lg border my-1 ${
                                    docTheme === 'paper'
                                      ? 'bg-slate-50 border-slate-200/90 text-slate-900 font-medium'
                                      : 'bg-slate-800/40 border-slate-700 text-slate-100 font-medium'
                                  }`}
                                >
                                  {trimmed}
                                </div>
                              );
                            }

                            return (
                              <p key={i} className="font-normal text-slate-700 dark:text-slate-300">
                                {trimmed}
                              </p>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
