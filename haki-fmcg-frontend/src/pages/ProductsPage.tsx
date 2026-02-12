import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Package,
  Search,
  SlidersHorizontal,
  LayoutGrid,
  List,
  Download,
  Plus,
  Star,

  CheckSquare,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';
import { useProducts, useProductCategories } from '@/hooks/useApi';


const oemTabs = [
  { id: 'all', label: 'All', count: 22028 },
  { id: 'finolex', label: 'Finolex', count: 164, color: '#3B82F6' },
  { id: 'havells', label: 'Havells', count: 33, color: '#EF4444' },
  { id: 'kei', label: 'KEI', count: 45, color: '#22C55E' },
  { id: 'polycab', label: 'Polycab', count: 285, color: '#F97316' },
  { id: 'rrkabel', label: 'RR Kabel', count: 166, color: '#A855F7' },
];

const mockProducts = [
  { sku: 'HAV-XLPE-11-240', name: 'XLPE 11kV 3Cx240 Power Cable', oem: 'Havells', size: '240 sq mm', cores: 3, voltage: '11kV', type: 'HT Power', price: 1850, unit: 'm', available: true, rating: 4.8 },
  { sku: 'POL-PVC-1.1-16', name: 'PVC 1.1kV 4Cx16 Control Cable', oem: 'Polycab', size: '16 sq mm', cores: 4, voltage: '1.1kV', type: 'LT Control', price: 320, unit: 'm', available: true, rating: 4.6 },
  { sku: 'KEI-XLPE-11-240', name: 'XLPE 11kV 3Cx240 HT Cable', oem: 'KEI', size: '240 sq mm', cores: 3, voltage: '11kV', type: 'HT Power', price: 1780, unit: 'm', available: true, rating: 4.5 },
  { sku: 'FIN-FR-1.1-2.5', name: 'FR PVC Wire 1.1kV 1Cx2.5', oem: 'Finolex', size: '2.5 sq mm', cores: 1, voltage: '1.1kV', type: 'House Wire', price: 28, unit: 'm', available: true, rating: 4.7 },
  { sku: 'RR-ARM-415-400', name: 'Armoured XLPE 415V 3.5Cx400', oem: 'RR Kabel', size: '400 sq mm', cores: 3.5, voltage: '415V', type: 'LT Power', price: 2400, unit: 'm', available: false, rating: 4.4 },
  { sku: 'POL-FR-1.1-4', name: 'FR PVC Wire 1.1kV 1Cx4', oem: 'Polycab', size: '4 sq mm', cores: 1, voltage: '1.1kV', type: 'House Wire', price: 42, unit: 'm', available: true, rating: 4.6 },
  { sku: 'HAV-ARM-415-240', name: 'Armoured XLPE 415V 3.5Cx240', oem: 'Havells', size: '240 sq mm', cores: 3.5, voltage: '415V', type: 'LT Power', price: 1650, unit: 'm', available: true, rating: 4.7 },
  { sku: 'KEI-CTRL-1.1-2.5', name: 'Control Cable 1.1kV 12Cx2.5', oem: 'KEI', size: '2.5 sq mm', cores: 12, voltage: '1.1kV', type: 'Control', price: 680, unit: 'm', available: true, rating: 4.3 },
];

const oemColors: Record<string, string> = {
  Havells: '#EF4444', Polycab: '#F97316', KEI: '#22C55E', Finolex: '#3B82F6', 'RR Kabel': '#A855F7',
};

export default function ProductsPage() {
  const [activeOem, setActiveOem] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [compareList, setCompareList] = useState<string[]>([]);
  const [page, setPage] = useState(1);

  /* ── Backend hooks ── */
  const { data: apiProducts } = useProducts({ page, search: searchQuery || undefined });
  const { data: _apiCategories } = useProductCategories();

  /* Build product list: backend → mock fallback */
  const allProducts = useMemo(() => {
    const items = (apiProducts as unknown as { data?: typeof mockProducts })?.data;
    if (items?.length) {
      return items.map((p: Record<string, unknown>) => ({
        sku: (p.sku as string) || '',
        name: (p.name as string) || '',
        oem: (p.oem as string) || (p.manufacturer as string) || '',
        size: (p.size as string) || '',
        cores: Number(p.cores) || 1,
        voltage: (p.voltage as string) || '',
        type: (p.type as string) || (p.category as string) || '',
        price: Number(p.price) || 0,
        unit: (p.unit as string) || 'm',
        available: p.available !== false,
        rating: Number(p.rating) || 4.0,
      }));
    }
    return mockProducts;
  }, [apiProducts]);

  const totalProducts = (apiProducts as unknown as { total?: number })?.total || 22028;
  const totalPages = (apiProducts as unknown as { total_pages?: number })?.total_pages || 2203;

  const filteredProducts = allProducts.filter((p) => {
    if (activeOem !== 'all' && p.oem.toLowerCase().replace(' ', '') !== activeOem) return false;
    if (searchQuery && !p.name.toLowerCase().includes(searchQuery.toLowerCase()) && !p.sku.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const toggleCompare = (sku: string) =>
    setCompareList((prev) =>
      prev.includes(sku) ? prev.filter((s) => s !== sku) : prev.length < 5 ? [...prev, sku] : prev,
    );

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-neon-emerald/10">
            <Package size={24} className="text-neon-emerald" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Product Catalog</h1>
            <p className="text-body text-muted-silver">22,028 products from 6 OEMs</p>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button variant="secondary" leftIcon={<Download size={14} />}>Export</Button>
          <Button variant="primary" leftIcon={<Plus size={14} />}>Add Product</Button>
        </div>
      </div>

      {/* Search + View Toggle */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search products by name, SKU, specs…"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50"
          />
        </div>
        <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${viewMode === 'grid' ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'}`}
          >
            <LayoutGrid size={16} />
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${viewMode === 'table' ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'}`}
          >
            <List size={16} />
          </button>
        </div>
        <Button variant="secondary" leftIcon={<SlidersHorizontal size={14} />}>Filters</Button>
      </div>

      {/* OEM Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-none">
        {oemTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveOem(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
              activeOem === tab.id
                ? 'bg-electric-cyan/15 text-electric-cyan'
                : 'bg-steel-slate/10 text-muted-silver hover:bg-steel-slate/20'
            }`}
          >
            {tab.color && <span className="w-2 h-2 rounded-full" style={{ backgroundColor: tab.color }} />}
            {tab.label}
            <span className="text-xs opacity-60">({tab.count.toLocaleString()})</span>
          </button>
        ))}
      </div>

      {/* Compare bar */}
      {compareList.length > 0 && (
        <div className="flex items-center gap-3 p-3 rounded-xl bg-violet-pulse/10 border border-violet-pulse/20">
          <CheckSquare size={16} className="text-violet-pulse" />
          <span className="text-sm text-ghost-white">{compareList.length} products selected for comparison</span>
          <Button variant="primary" size="sm" className="ml-auto">Compare Now</Button>
          <button onClick={() => setCompareList([])} className="text-xs text-muted-silver hover:text-ghost-white">Clear</button>
        </div>
      )}

      {/* Grid View */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredProducts.map((p) => (
            <motion.div key={p.sku} whileHover={{ y: -3 }}>
              <Card variant="glass" className="relative overflow-hidden">
                {/* OEM stripe */}
                <div className="absolute top-0 left-0 right-0 h-1" style={{ backgroundColor: oemColors[p.oem] || '#00D4FF' }} />

                <div className="flex items-start justify-between mb-2 pt-1">
                  <Badge variant="soft" color="cyan" size="sm">{p.oem}</Badge>
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleCompare(p.sku); }}
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                      compareList.includes(p.sku) ? 'border-violet-pulse bg-violet-pulse' : 'border-steel-slate/40'
                    }`}
                  >
                    {compareList.includes(p.sku) && <CheckSquare size={10} className="text-white" />}
                  </button>
                </div>

                <p className="text-sm font-semibold text-ghost-white leading-tight">{p.name}</p>
                <p className="text-xs text-muted-silver font-mono mt-1">{p.sku}</p>

                <div className="grid grid-cols-2 gap-1.5 mt-3 text-xs">
                  <div className="px-2 py-1 rounded bg-steel-slate/10 text-muted-silver">
                    <span className="text-ghost-white">{p.size}</span> · {p.cores}C
                  </div>
                  <div className="px-2 py-1 rounded bg-steel-slate/10 text-muted-silver">
                    {p.voltage} · {p.type}
                  </div>
                </div>

                <div className="flex items-center justify-between mt-3 pt-3 border-t border-steel-slate/15">
                  <div>
                    <span className="text-base font-bold text-ghost-white">₹{p.price.toLocaleString('en-IN')}</span>
                    <span className="text-xs text-muted-silver">/{p.unit}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={p.available ? 'soft' : 'outline'} color={p.available ? 'emerald' : 'coral'} size="sm">
                      {p.available ? 'In Stock' : 'Out'}
                    </Badge>
                  </div>
                </div>

                <div className="flex items-center gap-1 mt-2 text-xs text-amber-glow">
                  <Star size={10} fill="currentColor" /> {p.rating}
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        /* Table View */
        <Card variant="glass">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted-silver uppercase tracking-wider border-b border-steel-slate/30">
                  <th className="px-4 py-3">SKU</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">OEM</th>
                  <th className="px-4 py-3">Size</th>
                  <th className="px-4 py-3">Voltage</th>
                  <th className="px-4 py-3 text-right">Price</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((p) => (
                  <tr key={p.sku} className="border-b border-steel-slate/15 hover:bg-steel-slate/10 cursor-pointer transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-electric-cyan">{p.sku}</td>
                    <td className="px-4 py-3 text-ghost-white">{p.name}</td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: oemColors[p.oem] }} />
                        {p.oem}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-silver">{p.size} · {p.cores}C</td>
                    <td className="px-4 py-3 text-muted-silver">{p.voltage}</td>
                    <td className="px-4 py-3 text-ghost-white text-right font-medium">₹{p.price.toLocaleString('en-IN')}/{p.unit}</td>
                    <td className="px-4 py-3">
                      <Badge variant="soft" color={p.available ? 'emerald' : 'coral'} size="sm">
                        {p.available ? 'In Stock' : 'Out'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-silver">Showing {filteredProducts.length} of {totalProducts.toLocaleString()} products</p>
        <div className="flex gap-1">
          {[1, 2, 3, '...', totalPages].map((pg, i) => (
            <button
              key={i}
              onClick={() => typeof pg === 'number' && setPage(pg)}
              className={`w-8 h-8 rounded-lg text-sm transition-colors ${
                pg === page ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver hover:bg-steel-slate/15'
              }`}
            >
              {pg}
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
