import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, IndianRupee, Plus, Trash2, Save, Calculator, Percent, Package } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface LineItem { id: number; sku: string; name: string; qty: number; unit: string; unitPrice: number; margin: number; discount: number; }

const initialItems: LineItem[] = [
  { id: 1, sku: 'HAK-XLPE-240', name: 'XLPE Power Cable 240mm²', qty: 5000, unit: 'm', unitPrice: 2450, margin: 12, discount: 3 },
  { id: 2, sku: 'HAK-FR-25', name: 'Fire Resistant Cable 25mm²', qty: 2000, unit: 'm', unitPrice: 1680, margin: 10, discount: 0 },
  { id: 3, sku: 'HAK-ARM-120', name: 'Armoured Cable 120mm²', qty: 3000, unit: 'm', unitPrice: 1450, margin: 15, discount: 5 },
  { id: 4, sku: 'HAK-TERM-240', name: 'Termination Kit 240mm²', qty: 20, unit: 'set', unitPrice: 4500, margin: 20, discount: 0 },
];

export default function BidPricingEditorPage() {
  const [items, setItems] = useState<LineItem[]>(initialItems);

  const updateItem = (id: number, field: keyof LineItem, value: number | string) => {
    setItems((prev) => prev.map((it) => it.id === id ? { ...it, [field]: value } : it));
  };

  const calcLine = (it: LineItem) => {
    const base = it.qty * it.unitPrice;
    const withMargin = base * (1 + it.margin / 100);
    const withDiscount = withMargin * (1 - it.discount / 100);
    return { base, withMargin, final: Math.round(withDiscount) };
  };

  const grandTotal = items.reduce((a, it) => a + calcLine(it).final, 0);
  const totalBase = items.reduce((a, it) => a + calcLine(it).base, 0);
  const avgMargin = items.length > 0 ? items.reduce((a, it) => a + it.margin, 0) / items.length : 0;

  const addItem = () => setItems((prev) => [...prev, { id: Date.now(), sku: '', name: 'New Item', qty: 1, unit: 'm', unitPrice: 0, margin: 10, discount: 0 }]);
  const removeItem = (id: number) => setItems((prev) => prev.filter((it) => it.id !== id));

  const fmt = (n: number) => `₹${n.toLocaleString('en-IN')}`;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/bids" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Bid Pricing Editor</h1><p className="text-body text-muted-silver">BID-2026-0044 — Adjust margins, discounts & line items</p></div>
        </div>
        <div className="flex gap-2">
          <button onClick={addItem} className="flex items-center gap-1 text-sm text-electric-cyan bg-electric-cyan/10 px-3 py-2 rounded-lg hover:bg-electric-cyan/20"><Plus size={14} />Add Item</button>
          <button className="flex items-center gap-1 text-sm text-neon-emerald bg-neon-emerald/10 px-3 py-2 rounded-lg hover:bg-neon-emerald/20"><Save size={14} />Save</button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { l: 'Base Total', v: fmt(totalBase), icon: Package, c: 'text-muted-silver' },
          { l: 'Avg Margin', v: `${avgMargin.toFixed(1)}%`, icon: Percent, c: 'text-amber-glow' },
          { l: 'Grand Total', v: fmt(grandTotal), icon: IndianRupee, c: 'text-electric-cyan' },
          { l: 'Profit', v: fmt(grandTotal - totalBase), icon: Calculator, c: 'text-neon-emerald' },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-4">
            <s.icon size={16} className={`${s.c} mb-1`} />
            <span className="text-lg font-bold text-ghost-white">{s.v}</span>
            <span className="text-xs text-muted-silver block">{s.l}</span>
          </Card>
        ))}
      </div>

      <Card variant="glass" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-steel-slate/20">
                {['SKU', 'Product', 'Qty', 'Unit', 'Unit Price', 'Margin %', 'Discount %', 'Line Total', ''].map((h) => (
                  <th key={h} className="px-3 py-3 text-left text-muted-silver font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((it) => {
                const line = calcLine(it);
                return (
                  <tr key={it.id} className="border-b border-steel-slate/10 hover:bg-steel-slate/5">
                    <td className="px-3 py-2"><Badge variant="soft" color="cyan" size="sm">{it.sku || '—'}</Badge></td>
                    <td className="px-3 py-2 text-ghost-white">{it.name}</td>
                    <td className="px-3 py-2"><input type="number" value={it.qty} onChange={(e) => updateItem(it.id, 'qty', +e.target.value)} className="w-16 bg-deep-navy/50 border border-steel-slate/20 rounded px-2 py-1 text-ghost-white text-center" /></td>
                    <td className="px-3 py-2 text-muted-silver">{it.unit}</td>
                    <td className="px-3 py-2"><input type="number" value={it.unitPrice} onChange={(e) => updateItem(it.id, 'unitPrice', +e.target.value)} className="w-20 bg-deep-navy/50 border border-steel-slate/20 rounded px-2 py-1 text-ghost-white text-center" /></td>
                    <td className="px-3 py-2"><input type="number" value={it.margin} onChange={(e) => updateItem(it.id, 'margin', +e.target.value)} className="w-14 bg-deep-navy/50 border border-steel-slate/20 rounded px-2 py-1 text-amber-glow text-center" /></td>
                    <td className="px-3 py-2"><input type="number" value={it.discount} onChange={(e) => updateItem(it.id, 'discount', +e.target.value)} className="w-14 bg-deep-navy/50 border border-steel-slate/20 rounded px-2 py-1 text-neon-emerald text-center" /></td>
                    <td className="px-3 py-2 text-ghost-white font-semibold">{fmt(line.final)}</td>
                    <td className="px-3 py-2"><button onClick={() => removeItem(it.id)} className="text-coral-flame/50 hover:text-coral-flame"><Trash2 size={12} /></button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
