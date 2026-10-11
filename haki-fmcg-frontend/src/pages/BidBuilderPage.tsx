import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  FileText,
  Package,
  DollarSign,
  ScrollText,
  Eye,
  Save,
  Play,
  Plus,
  Trash2,
  Loader2,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── Wizard step config ─── */
const STEPS = [
  { id: 1, label: 'Select RFP', icon: FileText },
  { id: 2, label: 'Products', icon: Package },
  { id: 3, label: 'Pricing', icon: DollarSign },
  { id: 4, label: 'Terms', icon: ScrollText },
  { id: 5, label: 'Review', icon: Eye },
] as const;

/* ─── Mock data ─── */
const rfps = [
  { id: 'RFP-2026-0001', title: 'Power Cable Supply — BSES Delhi', value: '₹2.5 Cr', deadline: 'Feb 15, 2026', items: 24 },
  { id: 'RFP-2026-0002', title: 'Industrial Wiring — Tata Projects', value: '₹1.8 Cr', deadline: 'Feb 22, 2026', items: 18 },
  { id: 'RFP-2026-0003', title: 'HT Cable Procurement — L&T', value: '₹4.1 Cr', deadline: 'Mar 01, 2026', items: 31 },
];

interface LineItem {
  id: number;
  product: string;
  sku: string;
  unitPrice: number;
  qty: number;
  discount: number;
}

const defaultLineItems: LineItem[] = [
  { id: 1, product: '3C×240 sq mm XLPE Cable', sku: 'FNX-XLPE-3C240', unitPrice: 4850, qty: 2000, discount: 5 },
  { id: 2, product: '3C×120 sq mm XLPE Cable', sku: 'HAV-XLPE-3C120', unitPrice: 2680, qty: 3000, discount: 3 },
  { id: 3, product: '4C×16 sq mm PVC Cable', sku: 'PLY-PVC-4C16', unitPrice: 320, qty: 5000, discount: 7 },
];

const matchedProducts = [
  { name: '3C×240 sq mm XLPE Cable', sku: 'FNX-XLPE-3C240', oem: 'Finolex', match: 96, price: 4850 },
  { name: '3C×240 sq mm HT XLPE Cable', sku: 'HAV-XLPE-3C240', oem: 'Havells', match: 94, price: 5120 },
  { name: '3C×120 sq mm XLPE Cable', sku: 'HAV-XLPE-3C120', oem: 'Havells', match: 91, price: 2680 },
  { name: '3C×120 sq mm XLPE Power Cable', sku: 'PLY-XLPE-3C120', oem: 'Polycab', match: 89, price: 2740 },
  { name: '4C×16 sq mm PVC Cable', sku: 'PLY-PVC-4C16', oem: 'Polycab', match: 87, price: 320 },
  { name: '4C×16 sq mm PVC Cable', sku: 'KEI-PVC-4C16', oem: 'KEI', match: 85, price: 305 },
];

const termsTemplates = [
  { id: 'standard', label: 'Standard T&C', desc: 'Default payment and delivery terms' },
  { id: 'premium', label: 'Premium T&C', desc: 'Extended warranty, priority delivery' },
  { id: 'govt', label: 'Government T&C', desc: 'Government procurement compliance terms' },
];

const fmt = (n: number) => '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 0 });

export default function BidBuilderPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedRfp, setSelectedRfp] = useState<string | null>(null);
  const [selectedProducts, setSelectedProducts] = useState<string[]>(['FNX-XLPE-3C240', 'HAV-XLPE-3C120', 'PLY-PVC-4C16']);
  const [lineItems, setLineItems] = useState<LineItem[]>(defaultLineItems);
  const [selectedTerms, setSelectedTerms] = useState('standard');
  const [notes, setNotes] = useState('');

  const canNext = () => {
    if (step === 1) return !!selectedRfp;
    if (step === 2) return selectedProducts.length > 0;
    return true;
  };

  const subtotal = lineItems.reduce((a, li) => a + li.unitPrice * li.qty * (1 - li.discount / 100), 0);
  const gst = subtotal * 0.18;
  const grandTotal = subtotal + gst;

  const handleSaveDraft = () => {
    const draftId = `B-${Math.floor(1000 + Math.random() * 9000)}`;
    const targetRfp = rfps.find((r) => r.id === selectedRfp);
    const draftBid = {
      id: draftId,
      rfpId: selectedRfp || 'RFP-2026-0001',
      vendor: 'Haki FMCG Procurement',
      amount: grandTotal,
      status: 'draft',
      deadline: targetRfp?.deadline || '2026-02-28',
      items: lineItems.length,
      createdAt: new Date().toISOString().split('T')[0],
      approvalLevel: 0,
      maxApproval: 4,
      probability: 45,
    };
    try {
      const saved = localStorage.getItem('haki_custom_bids');
      const existing = saved ? JSON.parse(saved) : [];
      localStorage.setItem('haki_custom_bids', JSON.stringify([draftBid, ...existing]));
    } catch {
      // ignore
    }
    toast.success(`Bid draft ${draftId} saved successfully!`);
    navigate('/bids');
  };

  const handleGenerateBid = () => {
    setIsGenerating(true);
    const bidId = `B-${Math.floor(1000 + Math.random() * 9000)}`;
    const targetRfp = rfps.find((r) => r.id === selectedRfp);

    const newBid = {
      id: bidId,
      rfpId: selectedRfp || 'RFP-2026-0001',
      vendor: 'Haki FMCG Procurement',
      amount: grandTotal,
      status: 'submitted',
      deadline: targetRfp?.deadline || '2026-02-28',
      items: lineItems.length,
      createdAt: new Date().toISOString().split('T')[0],
      approvalLevel: 1,
      maxApproval: 4,
      probability: 88,
    };

    try {
      const saved = localStorage.getItem('haki_custom_bids');
      const existing = saved ? JSON.parse(saved) : [];
      localStorage.setItem('haki_custom_bids', JSON.stringify([newBid, ...existing]));
    } catch {
      // ignore
    }

    setTimeout(() => {
      setIsGenerating(false);
      toast.success(`Bid ${bidId} generated successfully! Opening commercial dossier...`);
      navigate(`/bids/${bidId}/preview`);
    }, 700);
  };

  const toggleProduct = (sku: string) => {
    setSelectedProducts((p) =>
      p.includes(sku) ? p.filter((x) => x !== sku) : [...p, sku]
    );
  };

  const updateItem = (id: number, field: keyof LineItem, value: number) => {
    setLineItems((items) => items.map((i) => (i.id === id ? { ...i, [field]: value } : i)));
  };

  const addItem = () => {
    setLineItems((items) => [
      ...items,
      { id: Date.now(), product: 'New Item', sku: '-', unitPrice: 0, qty: 1, discount: 0 },
    ]);
  };

  const removeItem = (id: number) => {
    setLineItems((items) => items.filter((i) => i.id !== id));
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/bids" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
          <ArrowLeft size={18} className="text-muted-silver" />
        </Link>
        <div>
          <h1 className="text-h1 text-ghost-white">Bid Builder</h1>
          <p className="text-body text-muted-silver">Create a new bid in 5 steps</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="flex items-center gap-1">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          const active = step === s.id;
          const done = step > s.id;
          return (
            <div key={s.id} className="flex items-center flex-1">
              <button
                onClick={() => done && setStep(s.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl transition-all text-left w-full ${
                  active ? 'bg-electric-cyan/10 border border-electric-cyan/30' :
                  done ? 'bg-neon-emerald/10 cursor-pointer' : 'bg-steel-slate/10'
                }`}
              >
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  done ? 'bg-neon-emerald/20' : active ? 'bg-electric-cyan/20' : 'bg-steel-slate/20'
                }`}>
                  {done ? <Check size={13} className="text-neon-emerald" /> : <Icon size={13} className={active ? 'text-electric-cyan' : 'text-muted-silver'} />}
                </div>
                <div className="hidden md:block">
                  <p className={`text-[10px] ${done ? 'text-neon-emerald' : active ? 'text-electric-cyan' : 'text-muted-silver'}`}>
                    Step {s.id}
                  </p>
                  <p className={`text-xs font-medium ${active ? 'text-ghost-white' : 'text-muted-silver'}`}>{s.label}</p>
                </div>
              </button>
              {i < STEPS.length - 1 && (
                <div className={`w-4 h-0.5 mx-1 flex-shrink-0 ${done ? 'bg-neon-emerald' : 'bg-steel-slate/30'}`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Step Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
        >
          {/* Step 1: Select RFP */}
          {step === 1 && (
            <div className="space-y-3">
              <p className="text-sm text-muted-silver">Select the RFP to create a bid for</p>
              {rfps.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedRfp(r.id)}
                  className={`w-full glass-card rounded-xl p-4 text-left transition-all border ${
                    selectedRfp === r.id ? 'border-electric-cyan/40 bg-electric-cyan/5' : 'border-transparent hover:border-steel-slate/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-mono text-electric-cyan">{r.id}</span>
                      <p className="text-sm font-semibold text-ghost-white mt-0.5">{r.title}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-ghost-white">{r.value}</p>
                      <p className="text-[10px] text-muted-silver">Due: {r.deadline}</p>
                    </div>
                  </div>
                  <div className="flex gap-3 mt-2">
                    <Badge variant="soft" color="cyan" size="sm">{r.items} items</Badge>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Step 2: Select Products */}
          {step === 2 && (
            <div className="space-y-3">
              <p className="text-sm text-muted-silver">Select matched products for the bid ({selectedProducts.length} selected)</p>
              <div className="grid gap-2">
                {matchedProducts.map((p) => {
                  const sel = selectedProducts.includes(p.sku);
                  return (
                    <button
                      key={p.sku}
                      onClick={() => toggleProduct(p.sku)}
                      className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all border ${
                        sel ? 'bg-electric-cyan/5 border-electric-cyan/30' : 'bg-steel-slate/10 border-transparent hover:border-steel-slate/30'
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center ${
                        sel ? 'border-electric-cyan bg-electric-cyan/20' : 'border-steel-slate/40'
                      }`}>
                        {sel && <Check size={12} className="text-electric-cyan" />}
                      </div>
                      <div className="flex-1 text-left">
                        <p className="text-sm font-medium text-ghost-white">{p.name}</p>
                        <p className="text-[10px] text-muted-silver">{p.oem} · {p.sku}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant="soft" color={p.match >= 90 ? 'teal' : 'amber'} size="sm">{p.match}% match</Badge>
                        <span className="text-sm font-semibold text-ghost-white">{fmt(p.price)}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 3: Pricing */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-silver">Configure pricing for bid line items</p>
                <Button size="sm" variant="secondary" leftIcon={<Plus size={12} />} onClick={addItem}>Add Item</Button>
              </div>
              <Card variant="glass" className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-steel-slate/20">
                      <th className="py-2 px-3 text-left text-[10px] text-muted-silver uppercase">Product</th>
                      <th className="py-2 px-3 text-right text-[10px] text-muted-silver uppercase w-28">Unit Price (₹)</th>
                      <th className="py-2 px-3 text-right text-[10px] text-muted-silver uppercase w-24">Qty</th>
                      <th className="py-2 px-3 text-right text-[10px] text-muted-silver uppercase w-20">Disc %</th>
                      <th className="py-2 px-3 text-right text-[10px] text-muted-silver uppercase w-32">Total</th>
                      <th className="w-10" />
                    </tr>
                  </thead>
                  <tbody>
                    {lineItems.map((li) => {
                      const total = li.unitPrice * li.qty * (1 - li.discount / 100);
                      return (
                        <tr key={li.id} className="border-b border-steel-slate/10 hover:bg-steel-slate/5">
                          <td className="py-2 px-3">
                            <p className="text-xs text-ghost-white">{li.product}</p>
                            <p className="text-[10px] text-muted-silver font-mono">{li.sku}</p>
                          </td>
                          <td className="py-2 px-3">
                            <input
                              type="number"
                              value={li.unitPrice}
                              onChange={(e) => updateItem(li.id, 'unitPrice', +e.target.value)}
                              className="w-full bg-steel-slate/15 rounded-lg px-2 py-1 text-xs text-ghost-white text-right border border-steel-slate/20 focus:border-electric-cyan/40 outline-none"
                            />
                          </td>
                          <td className="py-2 px-3">
                            <input
                              type="number"
                              value={li.qty}
                              onChange={(e) => updateItem(li.id, 'qty', +e.target.value)}
                              className="w-full bg-steel-slate/15 rounded-lg px-2 py-1 text-xs text-ghost-white text-right border border-steel-slate/20 focus:border-electric-cyan/40 outline-none"
                            />
                          </td>
                          <td className="py-2 px-3">
                            <input
                              type="number"
                              value={li.discount}
                              onChange={(e) => updateItem(li.id, 'discount', +e.target.value)}
                              className="w-full bg-steel-slate/15 rounded-lg px-2 py-1 text-xs text-ghost-white text-right border border-steel-slate/20 focus:border-electric-cyan/40 outline-none"
                            />
                          </td>
                          <td className="py-2 px-3 text-right text-xs font-semibold text-ghost-white">{fmt(total)}</td>
                          <td className="py-2 px-3">
                            <button onClick={() => removeItem(li.id)} className="text-coral-flame/60 hover:text-coral-flame">
                              <Trash2 size={12} />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </Card>
              {/* Totals */}
              <div className="flex justify-end">
                <div className="text-right space-y-1">
                  <p className="text-xs text-muted-silver">Subtotal: <span className="text-ghost-white font-semibold">{fmt(subtotal)}</span></p>
                  <p className="text-xs text-muted-silver">GST (18%): <span className="text-ghost-white font-semibold">{fmt(gst)}</span></p>
                  <p className="text-sm font-bold text-electric-cyan">Grand Total: {fmt(grandTotal)}</p>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Terms & Conditions */}
          {step === 4 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-silver">Select terms template and add notes</p>
              <div className="grid gap-2">
                {termsTemplates.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setSelectedTerms(t.id)}
                    className={`w-full flex items-center gap-3 p-4 rounded-xl border transition-all text-left ${
                      selectedTerms === t.id ? 'bg-electric-cyan/5 border-electric-cyan/30' : 'bg-steel-slate/10 border-transparent hover:border-steel-slate/30'
                    }`}
                  >
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      selectedTerms === t.id ? 'border-electric-cyan' : 'border-steel-slate/40'
                    }`}>
                      {selectedTerms === t.id && <div className="w-2.5 h-2.5 rounded-full bg-electric-cyan" />}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-ghost-white">{t.label}</p>
                      <p className="text-xs text-muted-silver">{t.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
              <div>
                <label className="text-xs text-muted-silver uppercase tracking-wider block mb-1.5">Additional Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={4}
                  placeholder="Add any additional notes or special requirements..."
                  className="w-full bg-steel-slate/15 rounded-xl px-4 py-3 text-sm text-ghost-white border border-steel-slate/20 focus:border-electric-cyan/40 outline-none resize-none placeholder:text-muted-silver/50"
                />
              </div>
            </div>
          )}

          {/* Step 5: Review */}
          {step === 5 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-silver">Review bid details before generating</p>
              {/* RFP */}
              <Card variant="glass" className="p-4">
                <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-1">RFP</p>
                <p className="text-sm font-semibold text-ghost-white">{selectedRfp}</p>
                <p className="text-xs text-muted-silver">{rfps.find((r) => r.id === selectedRfp)?.title}</p>
              </Card>
              {/* Products */}
              <Card variant="glass" className="p-4">
                <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-2">Line Items ({lineItems.length})</p>
                {lineItems.map((li) => (
                  <div key={li.id} className="flex items-center justify-between py-1.5 border-b border-steel-slate/10 last:border-0">
                    <div>
                      <p className="text-xs text-ghost-white">{li.product}</p>
                      <p className="text-[10px] text-muted-silver">{li.qty} × {fmt(li.unitPrice)} @ {li.discount}% disc</p>
                    </div>
                    <p className="text-xs font-semibold text-ghost-white">{fmt(li.unitPrice * li.qty * (1 - li.discount / 100))}</p>
                  </div>
                ))}
                <div className="mt-2 pt-2 border-t border-steel-slate/20 text-right">
                  <p className="text-sm font-bold text-electric-cyan">Grand Total (incl GST): {fmt(grandTotal)}</p>
                </div>
              </Card>
              {/* Terms */}
              <Card variant="glass" className="p-4">
                <p className="text-[10px] text-muted-silver uppercase tracking-wider mb-1">Terms</p>
                <p className="text-sm text-ghost-white">{termsTemplates.find((t) => t.id === selectedTerms)?.label}</p>
                {notes && <p className="text-xs text-muted-silver mt-1">{notes}</p>}
              </Card>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex items-center justify-between pt-2">
        <div>
          {step > 1 && (
            <Button variant="secondary" leftIcon={<ArrowLeft size={14} />} onClick={() => setStep((s) => s - 1)}>
              Back
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" leftIcon={<Save size={14} />} onClick={handleSaveDraft}>
            Save Draft
          </Button>
          {step < 5 ? (
            <Button variant="primary" rightIcon={<ArrowRight size={14} />} onClick={() => setStep((s) => s + 1)} disabled={!canNext()}>
              Next
            </Button>
          ) : (
            <Button
              variant="primary"
              leftIcon={isGenerating ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              disabled={isGenerating}
              onClick={handleGenerateBid}
            >
              {isGenerating ? 'Generating Bid...' : 'Generate Bid'}
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
