import { useState } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Download,
  Printer,
  Mail,
  Eye,
  GripVertical,
  Layers,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface Section {
  id: string;
  title: string;
  visible: boolean;
  content: string;
}

/* ─── data ─── */
const templates = [
  { id: 'standard', name: 'Standard Template', desc: 'Default bid document layout' },
  { id: 'detailed', name: 'Detailed Technical', desc: 'Extended specs & compliance' },
  { id: 'executive', name: 'Executive Summary', desc: 'High-level overview for management' },
];

const initialSections: Section[] = [
  {
    id: 'cover',
    title: 'Cover Page',
    visible: true,
    content: 'HAKI FMCG Procurement Intelligence\nBid Response Document\n\nBID-2026-001\nDate: February 7, 2026\n\nPrepared for: Municipal Corporation of Greater Mumbai\nRFP Reference: RFP-2024-089\nSubject: Supply of LT Power Cables — 240 sq mm, 3.5 Core',
  },
  {
    id: 'scope',
    title: 'Scope of Supply',
    visible: true,
    content: '1. LT Power Cable, 240 sq mm, 3.5 Core XLPE — 15,000 meters\n2. LT Control Cable, 2.5 sq mm, 12 Core — 5,000 meters\n3. Jointing Kits (Heat Shrink) — 120 nos\n4. Cable Glands (Double Compression, Brass) — 240 nos\n\nDelivery Schedule:\n  • Phase 1 (60%): Within 6 weeks of PO\n  • Phase 2 (40%): Within 10 weeks of PO\n\nManufacturer: Finolex Cables Ltd\nCompliance: IS 1554 Part 1, IS 694, IEC 60502-1',
  },
  {
    id: 'pricing',
    title: 'Pricing Table',
    visible: true,
    content: '',
  },
  {
    id: 'terms',
    title: 'Terms & Conditions',
    visible: true,
    content: '1. Payment Terms: 30 days from delivery\n2. Warranty: 12 months from commissioning / 18 months from delivery\n3. Liquidated Damages: 0.5% per week, max 5%\n4. Force Majeure: As per Indian Contract Act\n5. Dispute Resolution: Arbitration in Mumbai\n6. Price Validity: 90 days from bid submission\n7. Loading/Unloading: At seller\'s cost up to delivery point\n8. Insurance: Transit insurance included\n9. Testing: As per IS specifications, third-party testing at buyer\'s request\n10. Packing: Drum lengths as specified, proper weatherproofing',
  },
  {
    id: 'compliance',
    title: 'Compliance & Certifications',
    visible: true,
    content: 'Standards Compliance:\n  ✅ IS 1554 Part 1 — PVC Insulated Cables\n  ✅ IS 694 — PVC for Electrical Insulation\n  ✅ IEC 60502-1 — Power Cables\n  ✅ IS 8130 — Conductors for Insulated Cables\n\nManufacturer Certifications:\n  • ISO 9001:2015 (Valid till Dec 2027)\n  • ISO 14001:2015 (Valid till Dec 2027)\n  • BIS License: CM/L-1234567\n  • NABL Accredited Lab',
  },
  {
    id: 'annexures',
    title: 'Annexures',
    visible: false,
    content: 'Annexure A — Test Certificates\nAnnexure B — Factory Inspection Report\nAnnexure C — Delivery Schedule Gantt Chart\nAnnexure D — Company Profile & Past Performance',
  },
];

const pricingItems = [
  { item: 'LT Power Cable 240 sq mm 3.5C XLPE', unit: 'meter', qty: 15000, rate: 1850, gst: 18 },
  { item: 'LT Control Cable 2.5 sq mm 12C', unit: 'meter', qty: 5000, rate: 320, gst: 18 },
  { item: 'Jointing Kit (Heat Shrink)', unit: 'nos', qty: 120, rate: 4500, gst: 18 },
  { item: 'Cable Gland (DC, Brass)', unit: 'nos', qty: 240, rate: 850, gst: 18 },
];

function formatINR(n: number) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
}

export default function BidDocumentPreviewPage() {
  const { id } = useParams();
  const [sections, setSections] = useState(initialSections);
  const [template, setTemplate] = useState('standard');
  const [previewMode, setPreviewMode] = useState(true);

  const toggleSection = (sectionId: string) => {
    setSections((p) => p.map((s) => (s.id === sectionId ? { ...s, visible: !s.visible } : s)));
  };

  const subtotal = pricingItems.reduce((s, i) => s + i.qty * i.rate, 0);
  const gstTotal = pricingItems.reduce((s, i) => s + i.qty * i.rate * (i.gst / 100), 0);
  const grandTotal = subtotal + gstTotal;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to={id ? `/bids/${id}` : '/bids'} className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Bid Document Preview</h1>
            <p className="text-body text-muted-silver">BID-2026-001 — LT Power Cables Supply</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" leftIcon={<Printer size={14} />}>Print</Button>
          <Button variant="secondary" leftIcon={<Mail size={14} />}>Email</Button>
          <Button leftIcon={<Download size={14} />}>Export PDF</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
        {/* Left Panel — Controls */}
        <div className="space-y-4">
          {/* Template Selector */}
          <Card variant="glass" className="p-3 space-y-2">
            <h3 className="text-xs font-semibold text-ghost-white flex items-center gap-1.5"><Layers size={13} /> Template</h3>
            {templates.map((t) => (
              <button
                key={t.id}
                onClick={() => setTemplate(t.id)}
                className={`w-full text-left p-2 rounded-lg transition-colors text-xs ${template === t.id ? 'bg-electric-cyan/10 border border-electric-cyan/30' : 'bg-steel-slate/8 border border-transparent hover:border-steel-slate/20'}`}
              >
                <span className="font-medium text-ghost-white block">{t.name}</span>
                <span className="text-[10px] text-muted-silver">{t.desc}</span>
              </button>
            ))}
          </Card>

          {/* Section Order */}
          <Card variant="glass" className="p-3 space-y-2">
            <h3 className="text-xs font-semibold text-ghost-white flex items-center gap-1.5"><GripVertical size={13} /> Sections</h3>
            <Reorder.Group values={sections} onReorder={setSections} className="space-y-1">
              {sections.map((s) => (
                <Reorder.Item key={s.id} value={s} className="flex items-center gap-2 p-1.5 rounded-lg bg-steel-slate/8 cursor-grab active:cursor-grabbing">
                  <GripVertical size={12} className="text-muted-silver/50 flex-shrink-0" />
                  <span className={`text-xs flex-1 ${s.visible ? 'text-ghost-white' : 'text-muted-silver/50 line-through'}`}>{s.title}</span>
                  <button onClick={() => toggleSection(s.id)} className="flex-shrink-0">
                    {s.visible ? (
                      <Eye size={12} className="text-neon-emerald" />
                    ) : (
                      <Eye size={12} className="text-muted-silver/30" />
                    )}
                  </button>
                </Reorder.Item>
              ))}
            </Reorder.Group>
          </Card>

          {/* Preview Toggle */}
          <Card variant="glass" className="p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-ghost-white">Live Preview</span>
              <button
                onClick={() => setPreviewMode(!previewMode)}
                className={`w-9 h-5 rounded-full transition-colors ${previewMode ? 'bg-neon-emerald' : 'bg-steel-slate/30'} relative`}
              >
                <div className={`w-3.5 h-3.5 rounded-full bg-white absolute top-[3px] transition-all ${previewMode ? 'left-[18px]' : 'left-[3px]'}`} />
              </button>
            </div>
          </Card>
        </div>

        {/* Right Panel — Document Preview */}
        <Card variant="glass" className="p-0 overflow-hidden">
          <div className="p-3 border-b border-steel-slate/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText size={14} className="text-electric-cyan" />
              <span className="text-xs font-semibold text-ghost-white">Document Preview</span>
              <Badge variant="soft" color="cyan" size="sm">{template}</Badge>
            </div>
            <span className="text-[10px] text-muted-silver">{sections.filter((s) => s.visible).length} sections visible</span>
          </div>

          {/* A4-ish preview area */}
          <div className="p-6 bg-[#0D1229] min-h-[600px] space-y-6">
            <AnimatePresence mode="popLayout">
              {sections.filter((s) => s.visible).map((section) => (
                <motion.div
                  key={section.id}
                  layout
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="border border-steel-slate/15 rounded-lg overflow-hidden"
                >
                  {/* Section Header */}
                  <div className="px-4 py-2.5 bg-steel-slate/10 border-b border-steel-slate/10">
                    <h3 className="text-sm font-semibold text-electric-cyan">{section.title}</h3>
                  </div>

                  {/* Section Content */}
                  <div className="p-4">
                    {section.id === 'cover' && (
                      <div className="text-center space-y-3 py-6">
                        <div className="w-16 h-16 rounded-xl bg-electric-cyan/10 mx-auto flex items-center justify-center">
                          <FileText size={28} className="text-electric-cyan" />
                        </div>
                        {section.content.split('\n').map((line, i) => (
                          <p key={i} className={`${i === 0 ? 'text-lg font-bold text-ghost-white' : i === 1 ? 'text-sm text-electric-cyan font-medium' : i === 2 ? 'text-xs font-mono text-muted-silver mt-4' : 'text-xs text-muted-silver'}`}>
                            {line}
                          </p>
                        ))}
                      </div>
                    )}

                    {section.id === 'pricing' && (
                      <div>
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-steel-slate/20 text-muted-silver">
                              <th className="text-left py-2">#</th>
                              <th className="text-left py-2">Item Description</th>
                              <th className="text-center py-2">Unit</th>
                              <th className="text-right py-2">Qty</th>
                              <th className="text-right py-2">Rate (₹)</th>
                              <th className="text-right py-2">Amount (₹)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {pricingItems.map((item, idx) => (
                              <tr key={idx} className="border-b border-steel-slate/8">
                                <td className="py-2 text-muted-silver">{idx + 1}</td>
                                <td className="py-2 text-ghost-white">{item.item}</td>
                                <td className="py-2 text-center text-muted-silver">{item.unit}</td>
                                <td className="py-2 text-right text-ghost-white font-mono">{item.qty.toLocaleString('en-IN')}</td>
                                <td className="py-2 text-right text-ghost-white font-mono">{item.rate.toLocaleString('en-IN')}</td>
                                <td className="py-2 text-right text-ghost-white font-mono">{(item.qty * item.rate).toLocaleString('en-IN')}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <div className="mt-3 pt-3 border-t border-steel-slate/15 space-y-1 text-right text-xs">
                          <div className="flex justify-end gap-8">
                            <span className="text-muted-silver">Subtotal</span>
                            <span className="text-ghost-white font-mono w-28">{formatINR(subtotal)}</span>
                          </div>
                          <div className="flex justify-end gap-8">
                            <span className="text-muted-silver">GST (18%)</span>
                            <span className="text-ghost-white font-mono w-28">{formatINR(gstTotal)}</span>
                          </div>
                          <div className="flex justify-end gap-8 pt-1 border-t border-steel-slate/15">
                            <span className="text-electric-cyan font-semibold">Grand Total</span>
                            <span className="text-electric-cyan font-bold font-mono w-28">{formatINR(grandTotal)}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {section.id !== 'cover' && section.id !== 'pricing' && (
                      <pre className="text-xs text-muted-silver whitespace-pre-wrap leading-relaxed font-sans">
                        {section.content.split('\n').map((line, i) => {
                          if (line.includes('✅')) return <span key={i} className="text-neon-emerald block">{line}</span>;
                          if (line.includes('⚠️') || line.includes('⚠')) return <span key={i} className="text-amber-glow block">{line}</span>;
                          if (line.includes('❌')) return <span key={i} className="text-coral-flame block">{line}</span>;
                          if (/^\d+\./.test(line.trim())) return <span key={i} className="text-ghost-white block">{line}</span>;
                          if (line.includes('•')) return <span key={i} className="text-ghost-white/80 block">{line}</span>;
                          return <span key={i} className="block">{line}</span>;
                        })}
                      </pre>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
