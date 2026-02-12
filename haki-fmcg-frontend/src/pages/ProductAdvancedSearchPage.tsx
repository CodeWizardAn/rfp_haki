import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Search, SlidersHorizontal, X, ChevronDown, Package } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface Filter { category: string; voltage: string; material: string; standard: string; priceRange: [number, number]; }
const categories = ['All', 'Power Cables', 'Control Cables', 'Instrumentation', 'Fire Resistant', 'Armoured'];
const voltages = ['All', 'LT (≤1.1kV)', 'HT (3.3-33kV)', 'EHV (66-220kV)'];
const materials = ['All', 'Copper', 'Aluminium', 'Copper-Clad'];
const standards = ['All', 'IS 7098', 'IS 1554', 'IEC 60502', 'BS 6346'];

const mockProducts = [
  { sku: 'HAK-XLPE-240', name: 'XLPE Insulated Power Cable 240mm²', category: 'Power Cables', voltage: 'HT (3.3-33kV)', material: 'Copper', standard: 'IS 7098', price: 2450, matchScore: 94 },
  { sku: 'HAK-XLPE-400', name: 'XLPE Insulated Power Cable 400mm²', category: 'Power Cables', voltage: 'HT (3.3-33kV)', material: 'Copper', standard: 'IS 7098', price: 3120, matchScore: 88 },
  { sku: 'HAK-PVC-16', name: 'PVC Control Cable 16-core', category: 'Control Cables', voltage: 'LT (≤1.1kV)', material: 'Copper', standard: 'IS 1554', price: 890, matchScore: 76 },
  { sku: 'HAK-FR-25', name: 'Fire Resistant Cable 25mm²', category: 'Fire Resistant', voltage: 'LT (≤1.1kV)', material: 'Copper', standard: 'IEC 60502', price: 1680, matchScore: 91 },
  { sku: 'HAK-ARM-120', name: 'Armoured Cable 120mm²', category: 'Armoured', voltage: 'HT (3.3-33kV)', material: 'Aluminium', standard: 'BS 6346', price: 1450, matchScore: 82 },
  { sku: 'HAK-INST-4P', name: 'Instrumentation Cable 4-pair', category: 'Instrumentation', voltage: 'LT (≤1.1kV)', material: 'Copper-Clad', standard: 'IS 1554', price: 320, matchScore: 69 },
];

export default function ProductAdvancedSearchPage() {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(true);
  const [filters, setFilters] = useState<Filter>({ category: 'All', voltage: 'All', material: 'All', standard: 'All', priceRange: [0, 5000] });

  const results = mockProducts.filter((p) => {
    if (query && !p.name.toLowerCase().includes(query.toLowerCase()) && !p.sku.toLowerCase().includes(query.toLowerCase())) return false;
    if (filters.category !== 'All' && p.category !== filters.category) return false;
    if (filters.voltage !== 'All' && p.voltage !== filters.voltage) return false;
    if (filters.material !== 'All' && p.material !== filters.material) return false;
    if (filters.standard !== 'All' && p.standard !== filters.standard) return false;
    if (p.price < filters.priceRange[0] || p.price > filters.priceRange[1]) return false;
    return true;
  });

  const SelectFilter = ({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) => (
    <div>
      <label className="text-[10px] text-muted-silver block mb-1">{label}</label>
      <div className="relative">
        <select value={value} onChange={(e) => onChange(e.target.value)} className="w-full bg-deep-navy/50 border border-steel-slate/20 rounded-lg px-3 py-2 text-xs text-ghost-white appearance-none focus:outline-none focus:ring-1 focus:ring-electric-cyan/40">
          {options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-silver pointer-events-none" />
      </div>
    </div>
  );

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/products" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Advanced Product Search</h1><p className="text-body text-muted-silver">Multi-criteria search with specification filters</p></div>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by SKU, name, or specification..." className="w-full bg-deep-navy/50 border border-steel-slate/20 rounded-lg pl-10 pr-4 py-2.5 text-sm text-ghost-white placeholder:text-muted-silver/50 focus:outline-none focus:ring-1 focus:ring-electric-cyan/40" />
          {query && <button onClick={() => setQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2"><X size={14} className="text-muted-silver" /></button>}
        </div>
        <button onClick={() => setShowFilters(!showFilters)} className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm ${showFilters ? 'border-electric-cyan/40 text-electric-cyan bg-electric-cyan/5' : 'border-steel-slate/20 text-muted-silver'}`}><SlidersHorizontal size={14} />Filters</button>
      </div>

      {showFilters && (
        <Card variant="glass" className="p-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <SelectFilter label="Category" value={filters.category} options={categories} onChange={(v) => setFilters({ ...filters, category: v })} />
            <SelectFilter label="Voltage Class" value={filters.voltage} options={voltages} onChange={(v) => setFilters({ ...filters, voltage: v })} />
            <SelectFilter label="Conductor Material" value={filters.material} options={materials} onChange={(v) => setFilters({ ...filters, material: v })} />
            <SelectFilter label="Standard" value={filters.standard} options={standards} onChange={(v) => setFilters({ ...filters, standard: v })} />
          </div>
          <div className="mt-3 flex justify-end">
            <button onClick={() => setFilters({ category: 'All', voltage: 'All', material: 'All', standard: 'All', priceRange: [0, 5000] })} className="text-xs text-muted-silver hover:text-ghost-white">Reset Filters</button>
          </div>
        </Card>
      )}

      <div className="text-xs text-muted-silver">{results.length} products found</div>

      <div className="space-y-2">
        {results.map((p, i) => (
          <motion.div key={p.sku} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
            <Link to={`/products/${p.sku}`}>
              <Card variant="glass" className="p-4 flex items-center gap-4 hover:bg-steel-slate/5 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-electric-cyan/10 flex items-center justify-center"><Package size={18} className="text-electric-cyan" /></div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-ghost-white truncate">{p.name}</h3>
                  <div className="flex gap-2 mt-1">
                    <Badge variant="soft" color="cyan" size="sm">{p.sku}</Badge>
                    <Badge variant="soft" color="teal" size="sm">{p.category}</Badge>
                    <Badge variant="soft" color="amber" size="sm">{p.standard}</Badge>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-ghost-white">₹{p.price.toLocaleString('en-IN')}/m</span>
                  <div className="mt-1"><Badge variant="soft" color={p.matchScore >= 85 ? 'emerald' : p.matchScore >= 70 ? 'amber' : 'coral'} size="sm">{p.matchScore}% match</Badge></div>
                </div>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
