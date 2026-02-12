import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  CartesianGrid,
  Area,
  AreaChart,
} from 'recharts';
import {
  ArrowLeft,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Shield,
  Package,
  Factory,
  Users,
  IndianRupee,
  ChevronDown,
  ChevronUp,
  Zap,
  Target,
  FileText,
  Search,
  Download,
  RefreshCw,
  BarChart3,
  History,
  Layers,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, CardContent } from '@/components/ui';
import { tenderPricingService } from '@/services/tender-pricing.service';
import type {
  CatalogProduct,
  TenderPricingAnalytics,
} from '@/types';

/* ─── helpers ─── */

const fmt = (n: number) =>
  n >= 10000000 ? `₹${(n / 10000000).toFixed(2)} Cr` :
  n >= 100000 ? `₹${(n / 100000).toFixed(2)} L` :
  `₹${n.toLocaleString('en-IN')}`;

const fmtUnit = (n: number) => `₹${n.toLocaleString('en-IN')}`;

const riskColors: Record<string, string> = {
  low: '#00E68A',
  medium: '#FFB224',
  high: '#FF6B6B',
  critical: '#FF3366',
};

const riskBg: Record<string, string> = {
  low: 'rgba(0,230,138,0.1)',
  medium: 'rgba(255,178,36,0.1)',
  high: 'rgba(255,107,107,0.1)',
  critical: 'rgba(255,51,102,0.1)',
};

const outcomeColors: Record<string, string> = {
  won: '#00E68A',
  lost: '#FF6B6B',
  pending: '#FFB224',
  no_bid: '#8892B0',
};

const confidenceBadge: Record<string, { color: string; bg: string }> = {
  high: { color: '#00E68A', bg: 'rgba(0,230,138,0.12)' },
  medium: { color: '#FFB224', bg: 'rgba(255,178,36,0.12)' },
  low: { color: '#FF6B6B', bg: 'rgba(255,107,107,0.12)' },
};

const glassTooltip = {
  contentStyle: {
    background: 'rgba(18,24,51,0.92)',
    border: '1px solid rgba(0,212,255,0.15)',
    borderRadius: 10,
    color: '#E8ECF4',
    fontSize: 12,
  },
  cursor: { stroke: 'rgba(0,212,255,0.25)' },
};

type Tab = 'catalog' | 'autofill' | 'analytics';

/* ═══════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════ */

export default function TenderPricingIntelPage() {
  const [tab, setTab] = useState<Tab>('autofill');
  const [catalog, setCatalog] = useState<CatalogProduct[]>([]);
  const [analytics, setAnalytics] = useState<TenderPricingAnalytics | null>(null);
  const [, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [catalogSearch, setCatalogSearch] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      const [cat, anal] = await Promise.all([
        tenderPricingService.getCatalog(),
        tenderPricingService.getTenderAnalytics(),
      ]);
      setCatalog(cat);
      setAnalytics(anal);
      setLoading(false);
    })();
  }, []);

  const filteredCatalog = useMemo(() => {
    if (!catalogSearch.trim()) return catalog;
    const q = catalogSearch.toLowerCase();
    return catalog.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.oem.toLowerCase().includes(q) ||
        p.sku.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q)
    );
  }, [catalog, catalogSearch]);

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'catalog', label: 'Product Catalog', icon: <Package size={14} /> },
    { key: 'autofill', label: 'RFP Auto-Fill', icon: <Zap size={14} /> },
    { key: 'analytics', label: 'Pricing Intelligence', icon: <BarChart3 size={14} /> },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* ─── Header ─── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/analytics/trends" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Tender Pricing Intelligence</h1>
            <p className="text-body text-muted-silver">
              OEM Catalog → Auto-Fill RFP → Historical Pricing & Win Probability
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" leftIcon={<RefreshCw size={14} />} onClick={() => window.location.reload()}>
            Refresh
          </Button>
          <Button variant="secondary" leftIcon={<Download size={14} />}>Export</Button>
        </div>
      </div>

      {/* ─── KPI Summary ─── */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <KPICard label="Total Tender Value" value={fmt(analytics.total_value)} sub={`vs hist avg ${fmt(analytics.historical_avg_value)}`} delta={analytics.price_delta_pct} />
          <KPICard label="Win Probability" value={`${analytics.overall_win_probability}%`} sub="Based on historical data" delta={analytics.overall_win_probability > 60 ? 12 : -8} />
          <KPICard label="Line Items" value={String(analytics.line_items.length)} sub="Auto-matched from catalog" icon={<Layers size={14} className="text-electric-cyan" />} />
          <KPICard label="Vendors in Pool" value={String(new Set(catalog.flatMap((p) => p.vendors.map((v) => v.vendor_id))).size)} sub="OEM & distributors" icon={<Users size={14} className="text-violet-pulse" />} />
          <RiskPill risk={analytics.risk_summary} />
        </div>
      )}

      {/* ─── Tab Bar ─── */}
      <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1 w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-colors ${
              tab === t.key
                ? 'bg-electric-cyan/15 text-electric-cyan'
                : 'text-muted-silver hover:text-ghost-white'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* ─── Tab Content ─── */}
      <AnimatePresence mode="wait">
        {tab === 'catalog' && (
          <motion.div key="catalog" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="space-y-4">
            <CatalogPanel catalog={filteredCatalog} search={catalogSearch} onSearch={setCatalogSearch} />
          </motion.div>
        )}

        {tab === 'autofill' && analytics && (
          <motion.div key="autofill" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="space-y-4">
            <AutoFillPanel analytics={analytics} expandedRow={expandedRow} onToggleRow={setExpandedRow} />
          </motion.div>
        )}

        {tab === 'analytics' && analytics && (
          <motion.div key="analytics" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="space-y-4">
            <PricingAnalyticsPanel analytics={analytics} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════════
   KPI CARD
   ═══════════════════════════════════════════════════════════ */

function KPICard({ label, value, sub, delta, icon }: {
  label: string;
  value: string;
  sub: string;
  delta?: number;
  icon?: React.ReactNode;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-xl p-3.5">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-muted-silver uppercase tracking-wide">{label}</span>
        {icon}
      </div>
      <p className="text-lg font-bold text-ghost-white">{value}</p>
      <div className="flex items-center gap-1 mt-0.5">
        {delta !== undefined && (
          <span className={`text-[10px] font-medium flex items-center gap-0.5 ${delta >= 0 ? 'text-neon-emerald' : 'text-coral-flame'}`}>
            {delta >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
            {delta >= 0 ? '+' : ''}{delta.toFixed(1)}%
          </span>
        )}
        <span className="text-[10px] text-muted-silver">{sub}</span>
      </div>
    </motion.div>
  );
}

function RiskPill({ risk }: { risk: { low: number; medium: number; high: number; critical: number } }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-xl p-3.5">
      <span className="text-[10px] text-muted-silver uppercase tracking-wide block mb-1">Risk Breakdown</span>
      <div className="flex gap-2 mt-1.5">
        {(['low', 'medium', 'high', 'critical'] as const).map((r) => (
          <div key={r} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ background: riskColors[r] }} />
            <span className="text-xs font-semibold text-ghost-white">{risk[r]}</span>
            <span className="text-[9px] text-muted-silver capitalize">{r}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════════
   1. PRODUCT CATALOG PANEL (OEM + Vendor Pool)
   ═══════════════════════════════════════════════════════════ */

function CatalogPanel({ catalog, search, onSearch }: {
  catalog: CatalogProduct[];
  search: string;
  onSearch: (s: string) => void;
}) {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <>
      {/* Search */}
      <div className="relative max-w-md">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
        <input
          type="text"
          placeholder="Search by name, OEM, SKU, category…"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2 rounded-lg bg-steel-slate/10 border border-steel-slate/20 text-sm text-ghost-white placeholder:text-muted-silver focus:border-electric-cyan/40 focus:outline-none transition-colors"
        />
      </div>

      {/* Catalog cards */}
      <div className="space-y-3">
        {catalog.map((product) => (
          <Card key={product.id} variant="glass">
            <button
              className="w-full text-left p-4"
              onClick={() => setExpanded(expanded === product.id ? null : product.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-electric-cyan/10">
                    <Package size={16} className="text-electric-cyan" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-ghost-white">{product.name}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-steel-slate/15 text-muted-silver font-mono">{product.sku}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-silver">
                      <span className="flex items-center gap-1"><Factory size={10} /> OEM: <span className="text-ghost-white font-medium">{product.oem}</span></span>
                      <span>|</span>
                      <span>{product.category}</span>
                      <span>|</span>
                      <span>{fmtUnit(product.unit_price)}/{product.unit_of_measure}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-xs text-muted-silver block">Vendors</span>
                    <span className="text-sm font-bold text-electric-cyan">{product.vendors.length}</span>
                  </div>
                  {expanded === product.id ? <ChevronUp size={14} className="text-muted-silver" /> : <ChevronDown size={14} className="text-muted-silver" />}
                </div>
              </div>

              {/* Tags + Certs */}
              <div className="flex flex-wrap gap-1.5 mt-2">
                {product.certifications.map((c) => (
                  <span key={c} className="text-[9px] px-1.5 py-0.5 rounded-full bg-neon-emerald/10 text-neon-emerald font-medium flex items-center gap-0.5">
                    <Shield size={8} /> {c}
                  </span>
                ))}
              </div>
            </button>

            {/* Expanded: Vendor Pool */}
            <AnimatePresence>
              {expanded === product.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-4 border-t border-steel-slate/10 pt-3">
                    <span className="text-xs font-semibold text-ghost-white mb-2 block flex items-center gap-1">
                      <Users size={12} /> Vendor Pool
                    </span>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-muted-silver">
                            <th className="text-left py-1.5 pr-4">Vendor</th>
                            <th className="text-left py-1.5 pr-4">Tier</th>
                            <th className="text-right py-1.5 pr-4">Unit Price</th>
                            <th className="text-right py-1.5 pr-4">MOQ</th>
                            <th className="text-right py-1.5 pr-4">Lead Time</th>
                            <th className="text-right py-1.5 pr-4">Rating</th>
                            <th className="text-right py-1.5">Quality</th>
                          </tr>
                        </thead>
                        <tbody>
                          {product.vendors.map((v) => (
                            <tr key={v.vendor_id} className="border-t border-steel-slate/5">
                              <td className="py-1.5 pr-4 text-ghost-white font-medium">{v.name}</td>
                              <td className="py-1.5 pr-4">
                                <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${
                                  v.tier === 'platinum' ? 'bg-violet-pulse/15 text-violet-pulse' :
                                  v.tier === 'gold' ? 'bg-amber-glow/15 text-amber-glow' :
                                  'bg-steel-slate/15 text-muted-silver'
                                }`}>
                                  {v.tier}
                                </span>
                              </td>
                              <td className="py-1.5 pr-4 text-right text-ghost-white font-mono">{fmtUnit(v.unit_price)}</td>
                              <td className="py-1.5 pr-4 text-right text-muted-silver">{v.moq.toLocaleString()}</td>
                              <td className="py-1.5 pr-4 text-right text-muted-silver">{v.lead_time_days}d</td>
                              <td className="py-1.5 pr-4 text-right text-amber-glow">⭐ {v.rating}</td>
                              <td className="py-1.5 text-right">
                                <span className={`font-medium ${v.quality_score >= 90 ? 'text-neon-emerald' : 'text-amber-glow'}`}>
                                  {v.quality_score}%
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Mini price history chart */}
                    <div className="mt-3">
                      <span className="text-xs font-semibold text-ghost-white mb-1 block flex items-center gap-1">
                        <History size={12} /> Price History
                      </span>
                      <div className="h-32">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={product.price_history}>
                            <defs>
                              <linearGradient id={`catGrad-${product.id}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#00D4FF" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <XAxis dataKey="date" tick={{ fill: '#8892B0', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={(d) => d.slice(5)} />
                            <YAxis tick={{ fill: '#8892B0', fontSize: 9 }} axisLine={false} tickLine={false} />
                            <Tooltip {...glassTooltip} formatter={(val: any) => [fmtUnit(Number(val)), 'Price']} />
                            <Area type="monotone" dataKey="price" stroke="#00D4FF" fill={`url(#catGrad-${product.id})`} strokeWidth={2} dot={(props: any) => {
                              const { cx, cy, payload } = props;
                              const c = outcomeColors[payload.outcome] || '#8892B0';
                              return <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r={4} fill={c} stroke={c} strokeWidth={2} fillOpacity={0.6} />;
                            }} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="flex gap-3 mt-1">
                        {['won', 'lost', 'pending'].map((o) => (
                          <span key={o} className="flex items-center gap-1 text-[9px] text-muted-silver">
                            <span className="w-2 h-2 rounded-full" style={{ background: outcomeColors[o] }} />
                            {o}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        ))}
      </div>
    </>
  );
}

/* ═══════════════════════════════════════════════════════════
   2. AUTO-FILL PANEL (LHS Tender Req = RHS Prefilled)
   ═══════════════════════════════════════════════════════════ */

function AutoFillPanel({ analytics, expandedRow, onToggleRow }: {
  analytics: TenderPricingAnalytics;
  expandedRow: number | null;
  onToggleRow: (id: number | null) => void;
}) {
  return (
    <>
      {/* Tender Header */}
      <Card variant="glass">
        <div className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-violet-pulse/10">
              <FileText size={18} className="text-violet-pulse" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-ghost-white">{analytics.tender_title}</h2>
              <p className="text-xs text-muted-silver">Tender ID: {analytics.tender_id} • {analytics.line_items.length} line items</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-[10px] text-muted-silver block">Total Value</span>
              <span className="text-lg font-bold text-ghost-white">{fmt(analytics.total_value)}</span>
            </div>
            <WinProbabilityGauge probability={analytics.overall_win_probability} />
          </div>
        </div>
      </Card>

      {/* LHS = RHS Mapping */}
      <div className="space-y-2">
        <div className="grid grid-cols-12 gap-2 px-3 text-[10px] text-muted-silver uppercase tracking-wider">
          <div className="col-span-1">#</div>
          <div className="col-span-3">Tender Requirement (LHS)</div>
          <div className="col-span-1 text-center">→</div>
          <div className="col-span-3">Matched Product (RHS)</div>
          <div className="col-span-1 text-right">Price</div>
          <div className="col-span-1 text-right">Win %</div>
          <div className="col-span-1 text-right">Risk</div>
          <div className="col-span-1 text-center">Detail</div>
        </div>

        {analytics.line_items.map((item) => (
          <Card key={item.requirement_id} variant="glass">
            {/* Summary Row */}
            <button
              className="w-full text-left p-3"
              onClick={() => onToggleRow(expandedRow === item.requirement_id ? null : item.requirement_id)}
            >
              <div className="grid grid-cols-12 gap-2 items-center">
                {/* Line No */}
                <div className="col-span-1">
                  <span className="text-xs font-mono text-muted-silver">{item.requirement.line_no}</span>
                </div>

                {/* LHS: Tender Requirement */}
                <div className="col-span-3">
                  <span className="text-xs text-ghost-white font-medium block leading-tight">{item.requirement.item_description}</span>
                  <span className="text-[10px] text-muted-silver">{item.requirement.quantity.toLocaleString()} {item.requirement.unit}</span>
                </div>

                {/* Arrow */}
                <div className="col-span-1 flex justify-center">
                  <div className="flex items-center gap-1">
                    <div className="w-6 h-[1px] bg-electric-cyan/50" />
                    <ArrowRight size={10} className="text-electric-cyan" />
                  </div>
                </div>

                {/* RHS: Matched Product */}
                <div className="col-span-3">
                  <span className="text-xs text-ghost-white font-medium block leading-tight">{item.matched_product.name}</span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-[9px] font-mono text-muted-silver">{item.matched_product.sku}</span>
                    <span style={{ background: confidenceBadge[item.confidence]?.bg, color: confidenceBadge[item.confidence]?.color }} className="text-[8px] px-1 py-0.5 rounded font-semibold">
                      {item.match_score}% match
                    </span>
                  </div>
                </div>

                {/* Price */}
                <div className="col-span-1 text-right">
                  <span className="text-xs font-mono text-ghost-white block">{fmtUnit(item.prefilled_price)}</span>
                  <span className={`text-[9px] flex items-center gap-0.5 justify-end ${item.price_change_pct >= 0 ? 'text-coral-flame' : 'text-neon-emerald'}`}>
                    {item.price_trend === 'rising' ? <TrendingUp size={8} /> : item.price_trend === 'falling' ? <TrendingDown size={8} /> : <Minus size={8} />}
                    {item.price_change_pct >= 0 ? '+' : ''}{item.price_change_pct}%
                  </span>
                </div>

                {/* Win Probability */}
                <div className="col-span-1 text-right">
                  <span className={`text-xs font-bold ${item.win_probability >= 65 ? 'text-neon-emerald' : item.win_probability >= 40 ? 'text-amber-glow' : 'text-coral-flame'}`}>
                    {item.win_probability}%
                  </span>
                </div>

                {/* Risk */}
                <div className="col-span-1 text-right">
                  <span
                    className="text-[9px] px-1.5 py-0.5 rounded-full font-semibold capitalize"
                    style={{ background: riskBg[item.risk_level], color: riskColors[item.risk_level] }}
                  >
                    {item.risk_level}
                  </span>
                </div>

                {/* Expand */}
                <div className="col-span-1 flex justify-center">
                  {expandedRow === item.requirement_id ? <ChevronUp size={12} className="text-muted-silver" /> : <ChevronDown size={12} className="text-muted-silver" />}
                </div>
              </div>
            </button>

            {/* ─── Expanded Detail ─── */}
            <AnimatePresence>
              {expandedRow === item.requirement_id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-4 border-t border-steel-slate/10 pt-3 grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Col 1: Requirement & Product detail */}
                    <div className="space-y-3">
                      <div>
                        <span className="text-[10px] text-muted-silver uppercase tracking-wide block mb-1">Tender Specification</span>
                        <p className="text-xs text-ghost-white leading-relaxed">{item.requirement.specifications}</p>
                        {item.requirement.mandatory_certs && (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {item.requirement.mandatory_certs.map((c) => (
                              <span key={c} className="text-[8px] px-1 py-0.5 rounded bg-electric-cyan/10 text-electric-cyan">{c}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div>
                        <span className="text-[10px] text-muted-silver uppercase tracking-wide block mb-1">OEM & Product</span>
                        <p className="text-xs text-ghost-white"><Factory size={10} className="inline mr-1" />{item.matched_product.oem}</p>
                        <p className="text-[10px] text-muted-silver mt-0.5">{item.matched_product.description}</p>
                      </div>
                    </div>

                    {/* Col 2: Price Intelligence */}
                    <div className="space-y-3">
                      <div>
                        <span className="text-[10px] text-muted-silver uppercase tracking-wide block mb-1">Price Intelligence</span>
                        <div className="grid grid-cols-2 gap-2">
                          <PriceStat label="Current Price" value={fmtUnit(item.prefilled_price)} />
                          <PriceStat label="Recommended" value={fmtUnit(item.recommended_price)} highlight={item.recommended_price < item.prefilled_price} />
                          <PriceStat label="Historical Avg" value={fmtUnit(item.historical_avg_price)} />
                          <PriceStat label="Line Total" value={fmt(item.prefilled_price * item.requirement.quantity)} />
                        </div>
                      </div>

                      {/* Mini price trend */}
                      <div className="h-20">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={item.matched_product.price_history}>
                            <Line type="monotone" dataKey="price" stroke="#00D4FF" strokeWidth={1.5} dot={{ r: 2, fill: '#00D4FF' }} />
                            <ReferenceLine y={item.historical_avg_price} stroke="#FFB224" strokeDasharray="3 3" strokeWidth={1} />
                            <Tooltip {...glassTooltip} formatter={(val: any) => [fmtUnit(Number(val)), 'Price']} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Col 3: Risk & Vendors */}
                    <div className="space-y-3">
                      <div>
                        <span className="text-[10px] text-muted-silver uppercase tracking-wide block mb-1">Risk Factors</span>
                        <div className="space-y-1">
                          {item.risk_factors.map((rf, i) => (
                            <div key={i} className="flex items-start gap-1.5">
                              <AlertTriangle size={10} className="mt-0.5 flex-shrink-0" style={{ color: riskColors[item.risk_level] }} />
                              <span className="text-[10px] text-muted-silver leading-tight">{rf}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] text-muted-silver uppercase tracking-wide block mb-1">Available Vendors</span>
                        {item.vendor_options.slice(0, 3).map((v) => (
                          <div key={v.vendor_id} className="flex items-center justify-between py-1 border-b border-steel-slate/5 last:border-0">
                            <span className="text-[10px] text-ghost-white">{v.name}</span>
                            <span className="text-[10px] font-mono text-muted-silver">{fmtUnit(v.unit_price)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        ))}
      </div>

      {/* Historical comparison callout */}
      <Card variant="glass">
        <div className="p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-amber-glow/10">
              <AlertTriangle size={16} className="text-amber-glow" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-ghost-white mb-1">Historical Price Comparison</h3>
              <p className="text-xs text-muted-silver leading-relaxed">
                Current tender total is <span className="text-ghost-white font-semibold">{fmt(analytics.total_value)}</span> vs. historical average of <span className="text-ghost-white font-semibold">{fmt(analytics.historical_avg_value)}</span> —
                a <span className={`font-semibold ${analytics.price_delta_pct >= 0 ? 'text-coral-flame' : 'text-neon-emerald'}`}>
                  {analytics.price_delta_pct >= 0 ? '+' : ''}{analytics.price_delta_pct}%
                </span> change.
                {analytics.price_delta_pct > 10 && ' Historically, tenders priced significantly above average have a higher loss rate. Consider reviewing vendor pricing or negotiating better rates.'}
                {analytics.price_delta_pct < -5 && ' This is below historical average — strong competitive positioning.'}
              </p>
              <p className="text-xs text-muted-silver mt-2">
                <span className="text-ghost-white font-medium">Example:</span> If a tender historically cost ₹25L and now costs ₹21L, there's a chance you don't get the tender
                because such a large price drop (<span className="text-coral-flame font-medium">-16%</span>) may signal quality concerns to the buyer or trigger L1 suspicion. The system flags this as a risk automatically.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </>
  );
}

function PriceStat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="p-2 rounded-lg bg-steel-slate/8">
      <span className="text-[9px] text-muted-silver block">{label}</span>
      <span className={`text-xs font-semibold ${highlight ? 'text-neon-emerald' : 'text-ghost-white'}`}>{value}</span>
    </div>
  );
}

function WinProbabilityGauge({ probability }: { probability: number }) {
  const color = probability >= 65 ? '#00E68A' : probability >= 40 ? '#FFB224' : '#FF6B6B';
  const circumference = 2 * Math.PI * 18;
  const offset = circumference - (probability / 100) * circumference;

  return (
    <div className="relative w-14 h-14">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="18" fill="none" stroke="rgba(136,146,176,0.15)" strokeWidth="3" />
        <circle cx="20" cy="20" r="18" fill="none" stroke={color} strokeWidth="3" strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xs font-bold" style={{ color }}>{probability}%</span>
        <span className="text-[7px] text-muted-silver">WIN</span>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   3. PRICING ANALYTICS PANEL (Historical + Trends)
   ═══════════════════════════════════════════════════════════ */

function PricingAnalyticsPanel({ analytics }: { analytics: TenderPricingAnalytics }) {
  // Build historical tender timeline chart data
  const tenderTimeline = analytics.historical_tenders.map((t) => ({
    name: t.title.slice(0, 20) + '…',
    date: t.date,
    value: t.total_value / 100000, // in Lakhs
    outcome: t.outcome,
    ourBid: t.our_bid_value / 100000,
    winBid: t.winning_bid_value ? t.winning_bid_value / 100000 : undefined,
  }));

  // Price trend per product
  const lineItemPrices = analytics.line_items.map((li) => ({
    name: li.matched_product.sku,
    current: li.prefilled_price,
    historical: li.historical_avg_price,
    recommended: li.recommended_price,
    winProb: li.win_probability,
  }));

  return (
    <div className="space-y-4">
      {/* Historical Tenders Timeline */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <History size={14} className="text-electric-cyan" />
            Historical Tender Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tenderTimeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(136,146,176,0.1)" />
                <XAxis dataKey="name" tick={{ fill: '#8892B0', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 9 }} axisLine={false} tickLine={false} label={{ value: '₹ Lakhs', angle: -90, position: 'insideLeft', fill: '#8892B0', fontSize: 10 }} />
                <Tooltip
                  {...glassTooltip}
                  formatter={(val: any, name: any) => [`₹${Number(val).toFixed(1)}L`, name === 'ourBid' ? 'Our Bid' : name === 'winBid' ? 'Winning Bid' : 'Value']}
                />
                <Bar dataKey="ourBid" name="Our Bid" radius={[4, 4, 0, 0]}>
                  {tenderTimeline.map((entry, idx) => (
                    <Cell key={idx} fill={outcomeColors[entry.outcome]} fillOpacity={0.7} />
                  ))}
                </Bar>
                <Bar dataKey="winBid" name="Winning Bid" fill="rgba(0,212,255,0.3)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-2 justify-center">
            {['won', 'lost', 'pending'].map((o) => (
              <span key={o} className="flex items-center gap-1.5 text-[10px] text-muted-silver">
                <span className="w-2.5 h-2.5 rounded" style={{ background: outcomeColors[o] }} />
                {o.charAt(0).toUpperCase() + o.slice(1)}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Current vs Historical Price Comparison */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <IndianRupee size={14} className="text-amber-glow" />
            Price Comparison: Current vs Historical vs Recommended
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={lineItemPrices} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(136,146,176,0.1)" />
                <XAxis type="number" tick={{ fill: '#8892B0', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#8892B0', fontSize: 9 }} axisLine={false} tickLine={false} width={100} />
                <Tooltip
                  {...glassTooltip}
                  formatter={(val: any) => [fmtUnit(Number(val)), '']}
                />
                <Bar dataKey="historical" name="Historical Avg" fill="rgba(136,146,176,0.4)" radius={[0, 4, 4, 0]} />
                <Bar dataKey="current" name="Current Price" fill="rgba(0,212,255,0.6)" radius={[0, 4, 4, 0]} />
                <Bar dataKey="recommended" name="Recommended" fill="rgba(0,230,138,0.6)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Win Probability Matrix */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Target size={14} className="text-neon-emerald" />
            Win Probability by Line Item
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {analytics.line_items.map((item) => {
              const color = item.win_probability >= 65 ? '#00E68A' : item.win_probability >= 40 ? '#FFB224' : '#FF6B6B';
              return (
                <div key={item.requirement_id} className="flex items-center gap-3">
                  <span className="text-[10px] text-muted-silver w-28 truncate">{item.matched_product.sku}</span>
                  <div className="flex-1 h-4 bg-steel-slate/15 rounded-full overflow-hidden relative">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${item.win_probability}%` }}
                      transition={{ duration: 0.6, delay: 0.1 }}
                      className="h-full rounded-full"
                      style={{ background: color }}
                    />
                    {/* Historical avg marker */}
                    <div
                      className="absolute top-0 h-full w-0.5 bg-white/40"
                      style={{ left: `${Math.min(item.win_probability + 10, 95)}%` }}
                      title="Historical win rate"
                    />
                  </div>
                  <span className="text-xs font-bold w-10 text-right" style={{ color }}>{item.win_probability}%</span>
                  <span
                    className="text-[8px] px-1.5 py-0.5 rounded-full font-semibold capitalize w-14 text-center"
                    style={{ background: riskBg[item.risk_level], color: riskColors[item.risk_level] }}
                  >
                    {item.risk_level}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Historical Tender Table */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <FileText size={14} className="text-violet-pulse" />
            Past Tender History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted-silver border-b border-steel-slate/10">
                  <th className="text-left py-2 pr-3">Tender ID</th>
                  <th className="text-left py-2 pr-3">Title</th>
                  <th className="text-left py-2 pr-3">Date</th>
                  <th className="text-right py-2 pr-3">Our Bid</th>
                  <th className="text-right py-2 pr-3">Winning Bid</th>
                  <th className="text-right py-2 pr-3">Gap</th>
                  <th className="text-center py-2">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {analytics.historical_tenders.map((t) => {
                  const gap = t.winning_bid_value ? ((t.our_bid_value - t.winning_bid_value) / t.winning_bid_value * 100) : 0;
                  return (
                    <tr key={t.tender_id} className="border-b border-steel-slate/5">
                      <td className="py-2 pr-3 font-mono text-muted-silver">{t.tender_id}</td>
                      <td className="py-2 pr-3 text-ghost-white">{t.title}</td>
                      <td className="py-2 pr-3 text-muted-silver">{t.date}</td>
                      <td className="py-2 pr-3 text-right font-mono text-ghost-white">{fmt(t.our_bid_value)}</td>
                      <td className="py-2 pr-3 text-right font-mono text-muted-silver">{t.winning_bid_value ? fmt(t.winning_bid_value) : '—'}</td>
                      <td className="py-2 pr-3 text-right">
                        {t.winning_bid_value ? (
                          <span className={`font-medium ${gap > 0 ? 'text-coral-flame' : 'text-neon-emerald'}`}>
                            {gap > 0 ? '+' : ''}{gap.toFixed(1)}%
                          </span>
                        ) : '—'}
                      </td>
                      <td className="py-2 text-center">
                        <span
                          className="text-[9px] px-2 py-0.5 rounded-full font-semibold capitalize"
                          style={{ background: `${outcomeColors[t.outcome]}20`, color: outcomeColors[t.outcome] }}
                        >
                          {t.outcome === 'won' && <CheckCircle size={8} className="inline mr-0.5" />}
                          {t.outcome === 'lost' && <XCircle size={8} className="inline mr-0.5" />}
                          {t.outcome}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
