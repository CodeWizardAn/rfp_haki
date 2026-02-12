import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  X,
  Plus,
  Trophy,
  CheckCircle2,
  AlertTriangle,
  Download,
  Star,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';

interface Product {
  sku: string;
  name: string;
  oem: string;
  oemColor: string;
  price: number;
  rating: number;
  specs: Record<string, string>;
}

const CATALOG: Product[] = [
  {
    sku: 'FNX-XLPE-3C240',
    name: '3C×240 sq mm XLPE Cable',
    oem: 'Finolex',
    oemColor: '#3B82F6',
    price: 4850,
    rating: 4.5,
    specs: {
      'Voltage Rating': '11 kV',
      'Conductor Material': 'Copper',
      'No. of Cores': '3',
      'Cross Section': '240 sq mm',
      'Insulation': 'XLPE',
      'Armour': 'Steel Wire',
      'Current Rating': '396 A',
      'Impedance': '0.098 Ω/km',
      'Outer Diameter': '72 mm',
      'Weight': '8,600 kg/km',
      'Bending Radius': '720 mm',
      'Temp Range': '-20°C to 90°C',
      'Standard': 'IS 7098 Part 2',
      'Fire Performance': 'FR / FRLS',
      'Availability': 'In Stock',
    },
  },
  {
    sku: 'HAV-XLPE-3C240',
    name: '3C×240 sq mm HT XLPE Cable',
    oem: 'Havells',
    oemColor: '#EF4444',
    price: 5120,
    rating: 4.7,
    specs: {
      'Voltage Rating': '11 kV',
      'Conductor Material': 'Copper',
      'No. of Cores': '3',
      'Cross Section': '240 sq mm',
      'Insulation': 'XLPE',
      'Armour': 'Aluminium Strip',
      'Current Rating': '405 A',
      'Impedance': '0.095 Ω/km',
      'Outer Diameter': '70 mm',
      'Weight': '7,900 kg/km',
      'Bending Radius': '700 mm',
      'Temp Range': '-20°C to 90°C',
      'Standard': 'IS 7098 Part 2',
      'Fire Performance': 'FRLS / LSZH',
      'Availability': 'In Stock',
    },
  },
  {
    sku: 'PLY-XLPE-3C240',
    name: '3C×240 sq mm XLPE Power Cable',
    oem: 'Polycab',
    oemColor: '#F97316',
    price: 4980,
    rating: 4.6,
    specs: {
      'Voltage Rating': '11 kV',
      'Conductor Material': 'Copper',
      'No. of Cores': '3',
      'Cross Section': '240 sq mm',
      'Insulation': 'XLPE',
      'Armour': 'Steel Wire',
      'Current Rating': '400 A',
      'Impedance': '0.097 Ω/km',
      'Outer Diameter': '71 mm',
      'Weight': '8,200 kg/km',
      'Bending Radius': '710 mm',
      'Temp Range': '-25°C to 90°C',
      'Standard': 'IS 7098 Part 2',
      'Fire Performance': 'FR / FRLS',
      'Availability': '2-3 Weeks',
    },
  },
  {
    sku: 'KEI-XLPE-3C240',
    name: '3C×240 sq mm HT XLPE Cable',
    oem: 'KEI',
    oemColor: '#22C55E',
    price: 4720,
    rating: 4.3,
    specs: {
      'Voltage Rating': '11 kV',
      'Conductor Material': 'Copper',
      'No. of Cores': '3',
      'Cross Section': '240 sq mm',
      'Insulation': 'XLPE',
      'Armour': 'Steel Tape',
      'Current Rating': '390 A',
      'Impedance': '0.100 Ω/km',
      'Outer Diameter': '73 mm',
      'Weight': '8,900 kg/km',
      'Bending Radius': '730 mm',
      'Temp Range': '-20°C to 90°C',
      'Standard': 'IS 7098 Part 2',
      'Fire Performance': 'FR',
      'Availability': 'In Stock',
    },
  },
  {
    sku: 'RRK-XLPE-3C240',
    name: '3C×240 sq mm XLPE Cable',
    oem: 'RR Kabel',
    oemColor: '#A855F7',
    price: 4650,
    rating: 4.0,
    specs: {
      'Voltage Rating': '11 kV',
      'Conductor Material': 'Copper',
      'No. of Cores': '3',
      'Cross Section': '240 sq mm',
      'Insulation': 'XLPE',
      'Armour': 'Steel Wire',
      'Current Rating': '388 A',
      'Impedance': '0.101 Ω/km',
      'Outer Diameter': '74 mm',
      'Weight': '9,100 kg/km',
      'Bending Radius': '740 mm',
      'Temp Range': '-15°C to 90°C',
      'Standard': 'IS 7098 Part 2',
      'Fire Performance': 'FR',
      'Availability': 'In Stock',
    },
  },
];

const specKeys = Object.keys(CATALOG[0]?.specs ?? {});

/* Determine best value per spec row */
function bestForSpec(key: string, products: Product[]): string | null {
  const numericKeys: Record<string, 'max' | 'min'> = {
    'Current Rating': 'max',
    'Impedance': 'min',
    'Outer Diameter': 'min',
    'Weight': 'min',
    'Bending Radius': 'min',
  };
  const dir = numericKeys[key];
  if (!dir) return null;
  const vals = products.map((p) => {
    const raw = (p.specs[key] ?? '').replace(/[^0-9.]/g, '');
    return { sku: p.sku, v: parseFloat(raw) || 0 };
  });
  if (vals.length === 0) return null;
  const best = vals.reduce((a, b) => (dir === 'max' ? (b.v > a.v ? b : a) : (b.v < a.v ? b : a)));
  return best.sku;
}

export default function ProductComparisonPage() {
  const [selected, setSelected] = useState<string[]>(['FNX-XLPE-3C240', 'HAV-XLPE-3C240', 'PLY-XLPE-3C240']);
  const [showPicker, setShowPicker] = useState(false);

  const products = CATALOG.filter((p) => selected.includes(p.sku));
  const available = CATALOG.filter((p) => !selected.includes(p.sku));

  const remove = (sku: string) => setSelected((s) => s.filter((x) => x !== sku));
  const add = (sku: string) => {
    if (selected.length < 5) {
      setSelected((s) => [...s, sku]);
      setShowPicker(false);
    }
  };

  /* Overall score per product (simple weighted heuristic) */
  const scores = products.map((p) => {
    let score = 60;
    score += p.rating * 4; // max 20
    const cr = parseFloat((p.specs['Current Rating'] ?? '').replace(/[^0-9.]/g, '')) || 0;
    score += Math.min(cr / 40, 10);
    const w = parseFloat((p.specs['Weight'] ?? '').replace(/[^0-9.,]/g, '').replace(',', '')) || 0;
    score += Math.max(10 - w / 1000, 0);
    return { sku: p.sku, score: Math.min(Math.round(score), 100) };
  });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/products" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Product Comparison</h1>
            <p className="text-body text-muted-silver">Compare up to 5 products side-by-side</p>
          </div>
        </div>
        <div className="flex gap-2">
          {selected.length < 5 && (
            <Button variant="secondary" leftIcon={<Plus size={14} />} onClick={() => setShowPicker(true)}>
              Add Product
            </Button>
          )}
          <Button variant="secondary" leftIcon={<Download size={14} />}>Export</Button>
        </div>
      </div>

      {/* Product headers */}
      <div className="overflow-x-auto">
        <div className="min-w-[700px]">
          {/* Header row */}
          <div className="grid gap-3" style={{ gridTemplateColumns: `180px repeat(${products.length}, 1fr)` }}>
            <div /> {/* spec label column */}
            {products.map((p, i) => (
              <motion.div
                key={p.sku}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="glass-card rounded-xl p-4 text-center relative group"
              >
                <button
                  onClick={() => remove(p.sku)}
                  className="absolute top-2 right-2 p-1 rounded-lg bg-steel-slate/20 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={12} className="text-muted-silver" />
                </button>
                <div className="w-10 h-1.5 rounded-full mx-auto mb-2" style={{ background: p.oemColor }} />
                <p className="text-xs font-bold text-muted-silver">{p.oem}</p>
                <p className="text-sm font-semibold text-ghost-white mt-1 leading-tight">{p.name}</p>
                <p className="text-[10px] text-muted-silver font-mono mt-1">{p.sku}</p>
                <div className="flex items-center justify-center gap-1 mt-2">
                  <Star size={11} className="text-amber-glow fill-amber-glow" />
                  <span className="text-xs text-ghost-white">{p.rating}</span>
                </div>
                <p className="text-lg font-bold text-electric-cyan mt-2">₹{p.price.toLocaleString('en-IN')}<span className="text-[10px] text-muted-silver font-normal">/m</span></p>
              </motion.div>
            ))}
          </div>

          {/* Overall Score Row */}
          <div className="grid gap-3 mt-3" style={{ gridTemplateColumns: `180px repeat(${products.length}, 1fr)` }}>
            <div className="flex items-center px-3">
              <span className="text-xs font-semibold text-muted-silver uppercase">Overall Score</span>
            </div>
            {scores.map((s) => {
              const best = scores.reduce((a, b) => (b.score > a.score ? b : a));
              const isBest = s.sku === best.sku;
              return (
                <div key={s.sku} className={`py-3 px-4 rounded-xl text-center ${isBest ? 'bg-neon-emerald/10 border border-neon-emerald/30' : 'bg-steel-slate/10'}`}>
                  <div className="flex items-center justify-center gap-2">
                    <span className={`text-xl font-bold ${isBest ? 'text-neon-emerald' : 'text-ghost-white'}`}>{s.score}</span>
                    {isBest && <Trophy size={14} className="text-neon-emerald" />}
                  </div>
                  <div className="w-full h-1.5 bg-steel-slate/20 rounded-full mt-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${s.score}%` }}
                      transition={{ duration: 0.8, delay: 0.3 }}
                      className={`h-full rounded-full ${isBest ? 'bg-neon-emerald' : 'bg-electric-cyan'}`}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Spec Comparison Table */}
          <Card variant="glass" className="mt-4 overflow-hidden">
            <CardHeader><CardTitle className="text-sm">Specification Comparison</CardTitle></CardHeader>
            <div className="divide-y divide-steel-slate/10">
              {specKeys.map((key, ri) => {
                const bestSku = bestForSpec(key, products);
                const values = products.map((p) => p.specs[key]);
                const allSame = values.every((v) => v === values[0]);
                return (
                  <div
                    key={key}
                    className={`grid gap-3 ${ri % 2 === 0 ? 'bg-steel-slate/5' : ''} ${!allSame ? 'bg-amber-glow/[0.03]' : ''}`}
                    style={{ gridTemplateColumns: `180px repeat(${products.length}, 1fr)` }}
                  >
                    <div className="py-2.5 px-4 flex items-center">
                      <span className="text-xs font-medium text-muted-silver">{key}</span>
                    </div>
                    {products.map((p) => {
                      const val = p.specs[key];
                      const isBestVal = bestSku === p.sku;
                      return (
                        <div key={p.sku} className="py-2.5 px-4 flex items-center gap-1.5">
                          {isBestVal && <CheckCircle2 size={11} className="text-neon-emerald flex-shrink-0" />}
                          {!allSame && !isBestVal && bestSku && <AlertTriangle size={11} className="text-amber-glow/50 flex-shrink-0" />}
                          <span className={`text-xs ${isBestVal ? 'text-neon-emerald font-semibold' : 'text-ghost-white'}`}>
                            {val}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Price Comparison Bar */}
          <Card variant="glass" className="mt-4">
            <CardHeader><CardTitle className="text-sm">Price Comparison</CardTitle></CardHeader>
            <div className="px-4 pb-4 space-y-2">
              {products.map((p) => {
                const maxP = Math.max(...products.map((x) => x.price));
                const pct = (p.price / maxP) * 100;
                const lowestPrice = Math.min(...products.map((x) => x.price));
                const isLowest = p.price === lowestPrice;
                return (
                  <div key={p.sku} className="flex items-center gap-3">
                    <span className="text-xs text-muted-silver w-16 text-right flex-shrink-0">{p.oem}</span>
                    <div className="flex-1 h-6 bg-steel-slate/15 rounded-lg overflow-hidden relative">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className={`h-full rounded-lg ${isLowest ? 'bg-neon-emerald/60' : 'bg-electric-cyan/40'}`}
                      />
                      <span className="absolute inset-y-0 right-2 flex items-center text-xs font-semibold text-ghost-white">
                        ₹{p.price.toLocaleString('en-IN')}
                      </span>
                    </div>
                    {isLowest && <Badge variant="solid" color="teal" size="sm">Lowest</Badge>}
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      {/* Add Product Picker Modal */}
      <AnimatePresence>
        {showPicker && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-deep-navy/70 backdrop-blur-sm z-40"
              onClick={() => setShowPicker(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md bg-midnight-blue border border-steel-slate/30 rounded-2xl shadow-2xl p-5"
            >
              <h3 className="text-lg font-semibold text-ghost-white mb-4">Add Product to Compare</h3>
              {available.length === 0 ? (
                <p className="text-sm text-muted-silver">No more products available.</p>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {available.map((p) => (
                    <button
                      key={p.sku}
                      onClick={() => add(p.sku)}
                      className="w-full flex items-center gap-3 p-3 rounded-xl bg-steel-slate/10 hover:bg-steel-slate/20 transition-colors text-left"
                    >
                      <div className="w-3 h-8 rounded-full" style={{ background: p.oemColor }} />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-ghost-white">{p.name}</p>
                        <p className="text-[10px] text-muted-silver">{p.oem} · {p.sku}</p>
                      </div>
                      <span className="text-sm font-semibold text-electric-cyan">₹{p.price.toLocaleString('en-IN')}</span>
                    </button>
                  ))}
                </div>
              )}
              <div className="mt-4 flex justify-end">
                <Button variant="secondary" onClick={() => setShowPicker(false)}>Close</Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
