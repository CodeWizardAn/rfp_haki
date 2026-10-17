import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Package,
  Star,
  Shield,
  Zap,
  Ruler,
  Layers,
  FileText,
  Download,
  ShoppingCart,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  TrendingUp,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { formatCompactCurrency } from '@/utils/formatters';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

const mockProduct = {
  sku: 'HAV-XLPE-3C-240-11KV',
  name: 'XLPE Insulated 3-Core 240 sq.mm 11kV Power Cable',
  oem: 'Havells',
  oemColor: '#00D4FF',
  category: 'HT Cables',
  status: 'in_stock',
  rating: 4.6,
  reviewCount: 128,
  price: 4850,
  unit: '/100m',
  listPrice: 5200,
  moq: 500,
  leadTime: '10-14 days',
  lastUpdated: '2026-02-05',
  description: 'High-quality XLPE insulated power cable designed for 11kV distribution networks. Features stranded copper conductors, XLPE insulation, and galvanized steel wire armour. Compliant with IS 7098 Part 1 and suitable for direct burial or duct installation.',
  specs: {
    'Voltage Rating': '11kV (Ur = 12kV)',
    'Conductor Material': 'Electrolytic Copper, Stranded',
    'Conductor Size': '240 sq.mm',
    'Number of Cores': '3',
    'Insulation': 'XLPE (Cross-Linked Polyethylene)',
    'Inner Sheath': 'PVC (Polyvinyl Chloride)',
    'Armour': 'Galvanized Steel Wire (GSW)',
    'Outer Sheath': 'PVC, Black',
    'Current Rating': '398A (in air), 312A (in ground)',
    'Impedance': '0.0754 Ω/km at 90°C',
    'Short Circuit': '31.8 kA for 1s',
    'Overall Diameter': '78.2 mm (approx)',
    'Weight': '9,420 kg/km (approx)',
    'Min Bending Radius': '15 × OD = 1,173 mm',
    'Temperature Range': '-10°C to 90°C (conductor)',
    'Standard': 'IS 7098 Part 1',
    'Fire Performance': 'FR, FRLS available',
  },
  certifications: [
    { name: 'BIS IS 7098', status: 'valid' },
    { name: 'CPRI Type Tested', status: 'valid' },
    { name: 'ISO 9001:2015', status: 'valid' },
    { name: 'IEC 60502-2', status: 'valid' },
  ],
  testCosts: {
    routine: 15000,
    type: 85000,
    acceptance: 25000,
  },
  compatibility: [
    { rfpId: 'RFP-2026-0001', title: 'Power Cable Supply Phase 1', matchScore: 92 },
    { rfpId: 'RFP-2026-0005', title: 'Power Cable Supply Phase 2', matchScore: 78 },
    { rfpId: 'RFP-2026-0003', title: 'HV Cable Tender — Metro Expansion', matchScore: 65 },
  ],
};

const priceHistory = [
  { date: 'Sep', price: 4600 },
  { date: 'Oct', price: 4650 },
  { date: 'Nov', price: 4700 },
  { date: 'Dec', price: 4750 },
  { date: 'Jan', price: 4800 },
  { date: 'Feb', price: 4850 },
];

const tooltipStyle = {
  contentStyle: { background: '#0F172A', border: '1px solid #334155', borderRadius: 8, fontSize: 12, color: '#F8FAFC' },
  labelStyle: { color: '#94A3B8', fontWeight: 600, fontSize: 11 },
  itemStyle: { color: '#FFFFFF', fontWeight: 600, fontSize: 12 },
};

type TabId = 'specs' | 'pricing' | 'certifications' | 'compatibility';

export default function ProductDetailPage() {
  const { sku } = useParams();
  const [activeTab, setActiveTab] = useState<TabId>('specs');
  const p = mockProduct;
  const discount = Math.round(((p.listPrice - p.price) / p.listPrice) * 100);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div className="flex items-start gap-3">
          <Link to="/products" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors mt-1">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-electric-cyan">{sku || p.sku}</span>
              <Badge variant="soft" color={p.status === 'in_stock' ? 'emerald' : 'amber'} size="sm">
                {p.status === 'in_stock' ? 'In Stock' : 'Limited'}
              </Badge>
            </div>
            <h1 className="text-h1 text-ghost-white">{p.name}</h1>
            <div className="flex items-center gap-3 mt-1">
              <Badge variant="outline" color="cyan" size="sm" style={{ borderColor: p.oemColor, color: p.oemColor } as React.CSSProperties}>
                {p.oem}
              </Badge>
              <span className="text-xs text-muted-silver">{p.category}</span>
              <div className="flex items-center gap-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star key={i} size={11} className={i < Math.floor(p.rating) ? 'text-amber-glow fill-amber-glow' : 'text-steel-slate/30'} />
                ))}
                <span className="text-xs text-muted-silver ml-1">{p.rating} ({p.reviewCount})</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" leftIcon={<Download size={14} />}>Datasheet</Button>
          <Button variant="primary" leftIcon={<ShoppingCart size={14} />}>Add to Bid</Button>
        </div>
      </div>

      {/* Top Row: Price + Quick Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pricing Card */}
        <Card variant="glass">
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-3xl font-bold text-ghost-white">₹{p.price.toLocaleString('en-IN')}</span>
            <span className="text-sm text-muted-silver">{p.unit}</span>
          </div>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm text-muted-silver line-through">₹{p.listPrice.toLocaleString('en-IN')}</span>
            <Badge variant="soft" color="emerald" size="sm">-{discount}%</Badge>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-silver">MOQ</span>
              <span className="text-ghost-white font-medium">{p.moq} meters</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-silver">Lead Time</span>
              <span className="text-ghost-white font-medium">{p.leadTime}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-silver">Last Updated</span>
              <span className="text-ghost-white font-medium">{p.lastUpdated}</span>
            </div>
          </div>
        </Card>

        {/* Description */}
        <Card variant="glass" className="lg:col-span-2">
          <CardHeader><CardTitle>Description</CardTitle></CardHeader>
          <p className="text-sm text-muted-silver leading-relaxed">{p.description}</p>
          <div className="flex gap-4 mt-4">
            {([
              { icon: <Zap size={14} />, label: '11kV Rated', color: 'text-amber-glow' },
              { icon: <Layers size={14} />, label: '3-Core', color: 'text-electric-cyan' },
              { icon: <Ruler size={14} />, label: '240 sq.mm', color: 'text-neon-emerald' },
              { icon: <Shield size={14} />, label: 'IS 7098', color: 'text-violet-pulse' },
            ]).map((tag) => (
              <div key={tag.label} className="flex items-center gap-1.5">
                <span className={tag.color}>{tag.icon}</span>
                <span className="text-xs text-ghost-white font-medium">{tag.label}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-steel-slate/20 overflow-x-auto">
        {([
          { id: 'specs' as TabId, label: 'Specifications', icon: <FileText size={14} /> },
          { id: 'pricing' as TabId, label: 'Price History', icon: <BarChart3 size={14} /> },
          { id: 'certifications' as TabId, label: 'Certifications', icon: <Shield size={14} /> },
          { id: 'compatibility' as TabId, label: 'RFP Compatibility', icon: <Package size={14} /> },
        ]).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative flex items-center gap-1.5 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id ? 'text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'
            }`}
          >
            {tab.icon}
            {tab.label}
            {activeTab === tab.id && (
              <motion.div layoutId="product-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-electric-cyan rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
          {/* Specifications */}
          {activeTab === 'specs' && (
            <Card variant="glass">
              <CardHeader><CardTitle>Technical Specifications</CardTitle></CardHeader>
              <div className="divide-y divide-steel-slate/10">
                {Object.entries(p.specs).map(([key, value], i) => (
                  <div key={key} className={`flex justify-between py-3 ${i % 2 === 0 ? 'bg-transparent' : 'bg-steel-slate/5'} px-2 rounded`}>
                    <span className="text-sm text-muted-silver">{key}</span>
                    <span className="text-sm text-ghost-white font-medium text-right">{value}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Price History */}
          {activeTab === 'pricing' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card variant="glass" className="lg:col-span-2">
                <CardHeader><CardTitle>Price Trend (6 Months)</CardTitle></CardHeader>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={priceHistory}>
                    <defs>
                      <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E2642" />
                    <XAxis dataKey="date" tick={{ fill: '#8892B0', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#8892B0', fontSize: 11 }} domain={['auto', 'auto']} />
                    <Tooltip {...tooltipStyle} formatter={(value: unknown) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Price']} />
                    <Area type="monotone" dataKey="price" stroke="#00D4FF" fill="url(#priceGrad)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>

              <Card variant="glass">
                <CardHeader><CardTitle>Test Costs</CardTitle></CardHeader>
                <div className="space-y-4">
                  {([
                    { label: 'Routine Testing', cost: p.testCosts.routine, desc: 'Per lot / batch' },
                    { label: 'Type Testing', cost: p.testCosts.type, desc: 'One-time / per project' },
                    { label: 'Acceptance Testing', cost: p.testCosts.acceptance, desc: 'Per delivery' },
                  ]).map((test) => (
                    <div key={test.label} className="flex justify-between items-start">
                      <div>
                        <p className="text-sm font-medium text-ghost-white">{test.label}</p>
                        <p className="text-[10px] text-muted-silver">{test.desc}</p>
                      </div>
                      <span className="text-sm font-bold text-ghost-white">{formatCompactCurrency(test.cost)}</span>
                    </div>
                  ))}
                  <div className="pt-3 border-t border-steel-slate/20 flex justify-between">
                    <span className="text-sm font-semibold text-ghost-white">Total Testing</span>
                    <span className="text-sm font-bold text-electric-cyan">
                      {formatCompactCurrency(p.testCosts.routine + p.testCosts.type + p.testCosts.acceptance)}
                    </span>
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <TrendingUp size={12} className="text-neon-emerald" />
                  <span className="text-[10px] text-muted-silver">Price increased +5.4% over 6 months</span>
                </div>
              </Card>
            </div>
          )}

          {/* Certifications */}
          {activeTab === 'certifications' && (
            <Card variant="glass">
              <CardHeader><CardTitle>Certifications & Standards Compliance</CardTitle></CardHeader>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {p.certifications.map((cert) => (
                  <div key={cert.name} className="flex items-center gap-3 p-3 rounded-xl bg-steel-slate/10">
                    <div className={`p-2 rounded-lg ${cert.status === 'valid' ? 'bg-neon-emerald/10' : 'bg-amber-glow/10'}`}>
                      {cert.status === 'valid'
                        ? <CheckCircle2 size={16} className="text-neon-emerald" />
                        : <AlertTriangle size={16} className="text-amber-glow" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-ghost-white">{cert.name}</p>
                      <p className="text-[10px] text-muted-silver">Status: {cert.status}</p>
                    </div>
                    <Badge variant="soft" color={cert.status === 'valid' ? 'emerald' : 'amber'} size="sm">
                      {cert.status === 'valid' ? 'Valid' : 'Expiring'}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* RFP Compatibility */}
          {activeTab === 'compatibility' && (
            <Card variant="glass">
              <CardHeader><CardTitle>Matched RFPs ({p.compatibility.length})</CardTitle></CardHeader>
              <div className="space-y-3">
                {p.compatibility.map((rfp) => (
                  <Link
                    key={rfp.rfpId}
                    to={`/rfps/${rfp.rfpId}`}
                    className="flex items-center justify-between p-3 rounded-xl bg-steel-slate/10 hover:bg-steel-slate/20 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono text-electric-cyan">{rfp.rfpId}</span>
                      <span className="text-sm text-ghost-white">{rfp.title}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-steel-slate/20 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${rfp.matchScore >= 80 ? 'bg-neon-emerald' : rfp.matchScore >= 60 ? 'bg-amber-glow' : 'bg-coral-flame'}`}
                            style={{ width: `${rfp.matchScore}%` }}
                          />
                        </div>
                        <span className="text-xs font-bold text-ghost-white">{rfp.matchScore}%</span>
                      </div>
                      <ExternalLink size={12} className="text-muted-silver opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </Link>
                ))}
              </div>
            </Card>
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}
