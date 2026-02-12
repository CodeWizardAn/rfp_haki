import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  Play,
  MoreVertical,
  Clock,
  Calendar,
  FileText,
  Package,
  Banknote,
  Tag,
  Bot,
  ClipboardList,
  Shield,
  RefreshCw,
  Download,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Wifi,
  Search,
  BarChart3,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { formatCompactCurrency } from '@/utils/formatters';

/* ───── tab definition ───── */
const tabs = [
  { id: 'requirements', label: 'Extracted Terms', icon: <Search size={14} /> },
  { id: 'products', label: 'Matched Products', icon: <Package size={14} /> },
  { id: 'pricing', label: 'Pricing', icon: <Banknote size={14} /> },
  { id: 'bids', label: 'Bids', icon: <Tag size={14} /> },
  { id: 'analysis', label: 'Analysis Report', icon: <BarChart3 size={14} /> },
  { id: 'agents', label: 'Agent Logs', icon: <Bot size={14} /> },
  { id: 'audit', label: 'Audit', icon: <ClipboardList size={14} /> },
];

/* ───── Portal info for mock ───── */
const PORTAL_MAP: Record<string, { name: string; icon: string; port: number; color: string }> = {
  portal_1: { name: 'GovProcure India', icon: '🏛️', port: 5001, color: 'cyan' },
  portal_2: { name: 'TenderConnect', icon: '🔗', port: 5002, color: 'emerald' },
  portal_3: { name: 'eProcure Hub', icon: '📦', port: 5003, color: 'amber' },
  portal_4: { name: 'BidMarket Pro', icon: '📊', port: 5004, color: 'violet' },
  portal_5: { name: 'PublicBids Online', icon: '🌐', port: 5005, color: 'coral' },
};

/* ───── mock data ───── */
const mockPortalSource = {
  portalId: 'portal_1',
  scrapedAt: '2026-02-04 09:12:34',
  downloadedAt: '2026-02-04 09:12:38',
  fileSize: '2.4 MB',
  pages: 12,
  extractedTerms: 847,
  analysisScore: 94,
};

const mockRequirements = [
  { id: 1, desc: 'XLPE Power Cable 11kV 3C x 240 sqmm', specs: '11kV, 3-core, 240mm² Aluminium', qty: 1200, unit: 'm', matchStatus: 'matched' as const,
    matches: [
      { product: 'HAV-XLPE-11-240', oem: 'Havells', score: 96 },
      { product: 'POL-XLPE-11-240', oem: 'Polycab', score: 94 },
    ],
  },
  { id: 2, desc: 'PVC Insulated Cable 1.1kV 4C x 16 sqmm', specs: '1.1kV, 4-core, 16mm² Copper', qty: 3500, unit: 'm', matchStatus: 'matched' as const,
    matches: [{ product: 'POL-PVC-1.1-16', oem: 'Polycab', score: 91 }],
  },
  { id: 3, desc: 'Cable Gland Brass 3/4"', specs: 'Indoor, IP68, Nickel Plated', qty: 200, unit: 'pcs', matchStatus: 'partial' as const,
    matches: [{ product: 'BRS-CG-34', oem: 'Comet', score: 72 }],
  },
  { id: 4, desc: 'Heat Shrink Termination Kit 11kV', specs: '3-core, 185-300mm², outdoor', qty: 24, unit: 'set', matchStatus: 'unmatched' as const,
    matches: [],
  },
  { id: 5, desc: 'Armoured Cable 415V 3.5C x 400 sqmm', specs: '415V, LT, 400mm², XLPE', qty: 800, unit: 'm', matchStatus: 'matched' as const,
    matches: [{ product: 'HAV-ARM-415-400', oem: 'Havells', score: 89 }],
  },
];

const mockMatchedProducts = [
  { rank: 1, name: 'XLPE 11kV 3Cx240 Havells Make', oem: 'Havells', sku: 'HAV-XLPE-11-240', score: 96,
    breakdown: { size: 100, voltage: 100, material: 88, cert: 96 } },
  { rank: 2, name: 'XLPE 11kV 3Cx240 Polycab', oem: 'Polycab', sku: 'POL-XLPE-11-240', score: 94,
    breakdown: { size: 100, voltage: 100, material: 82, cert: 94 } },
  { rank: 3, name: 'XLPE 11kV 3Cx240 KEI', oem: 'KEI Industries', sku: 'KEI-XLPE-11-240', score: 89,
    breakdown: { size: 95, voltage: 100, material: 80, cert: 82 } },
  { rank: 4, name: 'PVC 1.1kV 4Cx16 Polycab', oem: 'Polycab', sku: 'POL-PVC-1.1-16', score: 91,
    breakdown: { size: 100, voltage: 100, material: 78, cert: 85 } },
];

const mockPricing = [
  { item: 'XLPE Power Cable 11kV', product: 'HAV-XLPE-11-240', unitPrice: 1850, qty: 1200, total: 2220000, testCost: 45000, trend: 'up' as const },
  { item: 'PVC Cable 1.1kV', product: 'POL-PVC-1.1-16', unitPrice: 320, qty: 3500, total: 1120000, testCost: 15000, trend: 'down' as const },
  { item: 'Cable Gland', product: 'BRS-CG-34', unitPrice: 480, qty: 200, total: 96000, testCost: 0, trend: 'stable' as const },
  { item: 'Heat Shrink Kit', product: 'RPG-HSK-11', unitPrice: 8500, qty: 24, total: 204000, testCost: 12000, trend: 'up' as const },
  { item: 'Armoured Cable 415V', product: 'HAV-ARM-415-400', unitPrice: 2400, qty: 800, total: 1920000, testCost: 35000, trend: 'stable' as const },
];

const mockBids = [
  { id: 'B-0087', vendor: 'Havells India Ltd', status: 'approved', amount: 5860000, date: '2026-02-05', items: 5 },
  { id: 'B-0088', vendor: 'Polycab India Ltd', status: 'submitted', amount: 5640000, date: '2026-02-05', items: 4 },
  { id: 'B-0089', vendor: 'KEI Industries Ltd', status: 'draft', amount: 5920000, date: '2026-02-06', items: 3 },
];

const mockAnalysisReport = {
  summary: 'RFP analysis completed successfully. 847 terms extracted from 12 pages. 5 key requirements identified with 4/5 matched to products in the database.',
  termCategories: [
    { category: 'Technical Specs', count: 312, confidence: 96 },
    { category: 'Material Requirements', count: 198, confidence: 91 },
    { category: 'Compliance Standards', count: 145, confidence: 88 },
    { category: 'Delivery Terms', count: 102, confidence: 94 },
    { category: 'Quality Parameters', count: 90, confidence: 85 },
  ],
  keyFindings: [
    'High demand for XLPE cables with IS 7098 compliance',
    'Budget allows for premium vendor selection',
    'Tight deadline requires parallel vendor engagement',
    'Type-test reports mandatory for all HV cables',
    'EMD of ₹5L required with bid submission',
  ],
};

const mockAgentLogs = [
  { id: 1, agent: 'Portal Scraper', type: 'scraper', action: 'Scraped RFP from GovProcure India portal (port 5001)', duration: '1.2s', status: 'completed', color: '#00D4FF',
    data: '{"portal":"GovProcure India","port":5001,"api_endpoint":"/api/rfps"}' },
  { id: 2, agent: 'PDF Downloader', type: 'downloader', action: 'Downloaded RFP PDF — 2.4 MB, 12 pages', duration: '2.1s', status: 'completed', color: '#14B8A6',
    data: '{"file_size":"2.4MB","pages":12,"format":"PDF 1.7"}' },
  { id: 3, agent: 'Text Extractor', type: 'extractor', action: 'Extracted text using pdfplumber — 847 terms identified', duration: '4.5s', status: 'completed', color: '#FFB224',
    data: '{"extractor":"pdfplumber","terms_found":847,"pages_processed":12}' },
  { id: 4, agent: 'Terms Matcher', type: 'matcher', action: 'Matched against 7.7M+ term database — 312 technical spec matches', duration: '8.3s', status: 'completed', color: '#7C3AED',
    data: '{"database_size":"7.7M+","matches":312,"fuzzy_threshold":80}' },
  { id: 5, agent: 'RFP Analyzer', type: 'analyzer', action: 'Generated analysis report — 5 requirements, 4 product matches, score 94%', duration: '3.2s', status: 'completed', color: '#10B981',
    data: '{"requirements":5,"products_matched":4,"analysis_score":94}' },
  { id: 6, agent: 'Master Agent', type: 'master', action: 'Pipeline complete — ready for bid generation', duration: '0.1s', status: 'completed', color: '#7C3AED',
    data: '{"pipeline_id":"pipe-8a3f","total_duration":"19.4s","status":"complete"}' },
];

const mockAuditTrail = [
  { id: 1, action: 'scraped', user: 'portal_scraper', timestamp: '2026-02-04 09:12:34', detail: 'RFP scraped from GovProcure India portal (port 5001)' },
  { id: 2, action: 'downloaded', user: 'pdf_downloader', timestamp: '2026-02-04 09:12:38', detail: 'PDF downloaded — 2.4 MB, stored in scraped_rfps/' },
  { id: 3, action: 'extracted', user: 'text_extractor', timestamp: '2026-02-04 09:12:42', detail: '12 pages processed, 847 terms extracted via pdfplumber' },
  { id: 4, action: 'matched', user: 'terms_matcher', timestamp: '2026-02-04 09:12:50', detail: '312 terms matched against 7.7M+ database, 5 requirements identified' },
  { id: 5, action: 'analyzed', user: 'rfp_analyzer', timestamp: '2026-02-04 09:12:54', detail: 'Analysis complete — 4/5 products matched, score 94%' },
  { id: 6, action: 'status_changed', user: 'system', timestamp: '2026-02-04 09:12:54', detail: 'Status: scraped → analyzed' },
  { id: 7, action: 'bid_generated', user: 'system', timestamp: '2026-02-05 10:30:02', detail: 'Bid B-0087 generated for Havells India Ltd' },
];

/* ───── helpers ───── */
const matchBadgeColor = (s: string) =>
  s === 'matched' ? 'emerald' : s === 'partial' ? 'amber' : 'coral';

const trendIcon = (t: string) =>
  t === 'up' ? '↑' : t === 'down' ? '↓' : '→';
const trendColor = (t: string) =>
  t === 'up' ? 'text-coral-flame' : t === 'down' ? 'text-neon-emerald' : 'text-muted-silver';

const bidStatusColor = (s: string) =>
  s === 'approved' ? 'emerald' : s === 'submitted' ? 'cyan' : 'amber';

const stages = ['scrape', 'download', 'extract-text', 'term-matching', 'analysis', 'product-matching', 'pricing', 'bid-generation'];

/* ═══════════════════════════════════════════════════════════════ */

export default function RFPDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState('requirements');
  const [expandedReq, setExpandedReq] = useState<number | null>(null);
  const [expandedLog, setExpandedLog] = useState<number | null>(null);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const currentStageIdx = 6; // pricing in progress

  const portalInfo = PORTAL_MAP[mockPortalSource.portalId];

  const subtotal = mockPricing.reduce((s, r) => s + r.total, 0);
  const testCosts = mockPricing.reduce((s, r) => s + r.testCost, 0);
  const grandTotal = subtotal + testCosts;
  const gst = grandTotal * 0.18;

  const toggleProduct = (sku: string) =>
    setSelectedProducts((prev) =>
      prev.includes(sku) ? prev.filter((s) => s !== sku) : [...prev, sku],
    );

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/rfps" className="p-2 rounded-lg hover:bg-steel-slate/30 text-muted-silver transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-h1 text-ghost-white">{id || 'RFP2'}</h1>
              <Badge variant="soft" color="cyan">analyzed</Badge>
              <Badge variant="soft" color="amber">high</Badge>
              <Badge variant="outline" color={portalInfo?.color as any || 'silver'} size="sm">
                <span className="mr-1">{portalInfo?.icon}</span> {portalInfo?.name}
              </Badge>
            </div>
            <p className="text-body text-muted-silver mt-0.5">Power Cable Supply — Zone East · Scraped from portal</p>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button variant="secondary" leftIcon={<Download size={14} />}>Export</Button>
          <Button variant="secondary" leftIcon={<RefreshCw size={14} />}>Re-analyze</Button>
          <Button variant="primary" leftIcon={<Play size={14} />}>Generate Bid</Button>
          <Button variant="ghost" iconOnly leftIcon={<MoreVertical size={16} />} />
        </div>
      </div>

      {/* ── Info + Pipeline Status ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* RFP Information — updated with portal source */}
        <Card variant="glass">
          <CardHeader><CardTitle>RFP Information</CardTitle></CardHeader>
          <div className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
            <div>
              <p className="text-xs text-muted-silver uppercase tracking-wider mb-1">Source Portal</p>
              <div className="flex items-center gap-2">
                <span className="text-lg">{portalInfo?.icon}</span>
                <div>
                  <p className="text-ghost-white font-medium">{portalInfo?.name}</p>
                  <p className="text-xs text-muted-silver">Port {portalInfo?.port}</p>
                </div>
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-silver uppercase tracking-wider mb-1">Scraped At</p>
              <div className="flex items-center gap-1.5 text-electric-cyan font-medium">
                <Wifi size={14} /> {mockPortalSource.scrapedAt}
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-silver uppercase tracking-wider mb-1">Deadline</p>
              <div className="flex items-center gap-1.5 text-amber-glow font-medium">
                <Calendar size={14} /> Feb 15, 2026
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-silver uppercase tracking-wider mb-1">Budget</p>
              <p className="text-ghost-white font-medium">{formatCompactCurrency(25000000)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-silver uppercase tracking-wider mb-1">Document</p>
              <p className="text-ghost-white font-medium">{mockPortalSource.pages} pages · {mockPortalSource.fileSize}</p>
            </div>
            <div>
              <p className="text-xs text-muted-silver uppercase tracking-wider mb-1">Terms Extracted</p>
              <p className="text-ghost-white font-medium">{mockPortalSource.extractedTerms} terms</p>
            </div>
            <div>
              <p className="text-xs text-muted-silver uppercase tracking-wider mb-1">Requirements</p>
              <p className="text-ghost-white font-medium">{mockRequirements.length} items</p>
            </div>
            <div>
              <p className="text-xs text-muted-silver uppercase tracking-wider mb-1">Analysis Score</p>
              <div className="flex items-center gap-2">
                <span className="text-neon-emerald font-bold text-lg">{mockPortalSource.analysisScore}%</span>
                <div className="w-16 h-1.5 rounded-full bg-steel-slate/30">
                  <div className="h-full rounded-full bg-neon-emerald" style={{ width: `${mockPortalSource.analysisScore}%` }} />
                </div>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 mt-5 pt-4 border-t border-steel-slate/20">
            {['scraped', 'portal-1', 'xlpe', 'power-cable', 'zone-east'].map((tag) => (
              <Badge key={tag} variant="outline" color="cyan" size="sm">{tag}</Badge>
            ))}
          </div>
        </Card>

        {/* Processing Status — updated pipeline */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Processing Pipeline</CardTitle>
            <span className="text-xs text-muted-silver">Scrape → Analyze → Bid</span>
          </CardHeader>
          <div className="space-y-2">
            {stages.map((stage, i) => {
              const completed = i < currentStageIdx;
              const current = i === currentStageIdx;
              return (
                <div key={stage} className="flex items-center gap-3">
                  <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                    completed
                      ? 'bg-neon-emerald/20 text-neon-emerald'
                      : current
                        ? 'bg-electric-cyan/20 text-electric-cyan ring-2 ring-electric-cyan/40 animate-pulse'
                        : 'bg-steel-slate/20 text-muted-silver/60'
                  }`}>
                    {completed ? <CheckCircle2 size={14} /> : i + 1}
                  </span>
                  <span className={`text-sm capitalize flex-1 ${
                    completed ? 'text-neon-emerald' : current ? 'text-electric-cyan font-medium' : 'text-muted-silver/60'
                  }`}>
                    {stage.replace(/-/g, ' ')}
                  </span>
                  {completed && <span className="text-xs text-neon-emerald/70">✓</span>}
                  {current && <span className="text-xs text-electric-cyan animate-pulse">Running...</span>}
                </div>
              );
            })}
          </div>
          <div className="mt-4 pt-3 border-t border-steel-slate/20 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-muted-silver">
              <Clock size={12} /> Duration: 19.4s · Stage {currentStageIdx + 1}/{stages.length}
            </div>
            <div className="w-24 h-1.5 rounded-full bg-steel-slate/30">
              <div className="h-full rounded-full bg-electric-cyan transition-all" style={{ width: `${(currentStageIdx / stages.length) * 100}%` }} />
            </div>
          </div>
        </Card>
      </div>

      {/* ── Tab Bar ── */}
      <div className="flex gap-1 overflow-x-auto border-b border-steel-slate/30 pb-px scrollbar-none">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors rounded-t-lg ${
              activeTab === tab.id
                ? 'text-electric-cyan bg-electric-cyan/8'
                : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/15'
            }`}
          >
            {tab.icon} {tab.label}
            {activeTab === tab.id && (
              <motion.span
                layoutId="rfp-tab-indicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-electric-cyan rounded-full"
              />
            )}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.15 }}
        >
          {/* ── Requirements Tab ── */}
          {activeTab === 'requirements' && (
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Extracted Terms &amp; Requirements ({mockRequirements.length})</CardTitle>
                <div className="flex gap-2">
                  <Badge variant="soft" color="cyan" size="sm">{mockPortalSource.extractedTerms} terms from {mockPortalSource.pages} pages</Badge>
                  <Button variant="secondary" size="sm" leftIcon={<RefreshCw size={12} />}>Re-match All</Button>
                </div>
              </CardHeader>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-muted-silver uppercase tracking-wider border-b border-steel-slate/30">
                      <th className="px-4 py-3 w-8"></th>
                      <th className="px-4 py-3">#</th>
                      <th className="px-4 py-3">Description</th>
                      <th className="px-4 py-3">Specifications</th>
                      <th className="px-4 py-3 text-right">Qty</th>
                      <th className="px-4 py-3">Unit</th>
                      <th className="px-4 py-3">Match</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockRequirements.map((r) => (
                      <>
                        <tr
                          key={r.id}
                          className="border-b border-steel-slate/15 hover:bg-steel-slate/10 transition-colors cursor-pointer"
                          onClick={() => setExpandedReq(expandedReq === r.id ? null : r.id)}
                        >
                          <td className="px-4 py-3">
                            {r.matches.length > 0 && (
                              expandedReq === r.id ? <ChevronUp size={14} className="text-muted-silver" /> : <ChevronDown size={14} className="text-muted-silver" />
                            )}
                          </td>
                          <td className="px-4 py-3 text-muted-silver font-mono">{r.id}</td>
                          <td className="px-4 py-3 text-ghost-white font-medium">{r.desc}</td>
                          <td className="px-4 py-3 text-muted-silver font-mono text-xs">{r.specs}</td>
                          <td className="px-4 py-3 text-ghost-white text-right">{r.qty.toLocaleString()}</td>
                          <td className="px-4 py-3 text-muted-silver">{r.unit}</td>
                          <td className="px-4 py-3">
                            <Badge variant="soft" color={matchBadgeColor(r.matchStatus)}>{r.matchStatus}</Badge>
                          </td>
                          <td className="px-4 py-3">
                            <Button variant="ghost" size="xs" leftIcon={<RefreshCw size={10} />}>Re-match</Button>
                          </td>
                        </tr>
                        {expandedReq === r.id && r.matches.length > 0 && (
                          <tr key={`${r.id}-expanded`}>
                            <td colSpan={8} className="px-8 py-3 bg-steel-slate/5">
                              <div className="space-y-2">
                                <p className="text-xs text-muted-silver uppercase tracking-wider mb-2">Matched Products</p>
                                {r.matches.map((m) => (
                                  <div key={m.product} className="flex items-center justify-between py-2 px-3 rounded-lg bg-steel-slate/10">
                                    <div className="flex items-center gap-3">
                                      <span className="font-mono text-xs text-electric-cyan">{m.product}</span>
                                      <span className="text-sm text-muted-silver">{m.oem}</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                      <span className="text-sm font-bold text-neon-emerald">{m.score}%</span>
                                      <div className="w-20 h-1.5 rounded-full bg-steel-slate/30">
                                        <div className="h-full rounded-full bg-neon-emerald" style={{ width: `${m.score}%` }} />
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* ── Matched Products Tab ── */}
          {activeTab === 'products' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-silver">{selectedProducts.length} of {mockMatchedProducts.length} selected for bid</p>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm">Sort by Score</Button>
                  <Button variant="primary" size="sm" disabled={selectedProducts.length === 0}>
                    Create Bid ({selectedProducts.length})
                  </Button>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockMatchedProducts.map((p) => {
                  const isSelected = selectedProducts.includes(p.sku);
                  return (
                    <Card
                      key={p.sku}
                      variant="glass"
                      className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-electric-cyan/50' : ''}`}
                      onClick={() => toggleProduct(p.sku)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                            p.rank <= 1 ? 'bg-amber-glow/20 text-amber-glow' : 'bg-steel-slate/30 text-muted-silver'
                          }`}>
                            #{p.rank}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-ghost-white">{p.name}</p>
                            <p className="text-xs text-muted-silver">OEM: {p.oem} · {p.sku}</p>
                          </div>
                        </div>
                        <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                          isSelected ? 'border-electric-cyan bg-electric-cyan' : 'border-steel-slate/40'
                        }`}>
                          {isSelected && <CheckCircle2 size={12} className="text-deep-navy" />}
                        </div>
                      </div>
                      {/* Overall Score */}
                      <div className="flex items-center gap-3 mb-4">
                        <div className="flex-1 h-2.5 rounded-full bg-steel-slate/30">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-electric-cyan to-neon-emerald transition-all"
                            style={{ width: `${p.score}%` }}
                          />
                        </div>
                        <span className="text-lg font-bold text-neon-emerald">{p.score}%</span>
                      </div>
                      {/* Score Breakdown */}
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(p.breakdown).map(([key, val]) => (
                          <div key={key} className="flex items-center justify-between py-1.5 px-2 rounded bg-steel-slate/10">
                            <span className="text-muted-silver capitalize">{key}</span>
                            <span className={val >= 90 ? 'text-neon-emerald font-medium' : val >= 75 ? 'text-amber-glow font-medium' : 'text-coral-flame font-medium'}>{val}%</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Pricing Tab ── */}
          {activeTab === 'pricing' && (
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Pricing Summary</CardTitle>
                <Button variant="primary" size="sm" leftIcon={<RefreshCw size={12} />}>Recalculate</Button>
              </CardHeader>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-muted-silver uppercase tracking-wider border-b border-steel-slate/30">
                      <th className="px-4 py-3">Item</th>
                      <th className="px-4 py-3">Product</th>
                      <th className="px-4 py-3 text-right">Unit Price</th>
                      <th className="px-4 py-3 text-right">Qty</th>
                      <th className="px-4 py-3 text-right">Total</th>
                      <th className="px-4 py-3 text-right">Test Costs</th>
                      <th className="px-4 py-3 text-center">Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockPricing.map((r, i) => (
                      <tr key={i} className="border-b border-steel-slate/15 hover:bg-steel-slate/10 transition-colors">
                        <td className="px-4 py-3 text-ghost-white">{r.item}</td>
                        <td className="px-4 py-3 text-muted-silver font-mono text-xs">{r.product}</td>
                        <td className="px-4 py-3 text-ghost-white text-right">₹{r.unitPrice.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 text-ghost-white text-right">{r.qty.toLocaleString()}</td>
                        <td className="px-4 py-3 text-ghost-white text-right font-medium">{formatCompactCurrency(r.total)}</td>
                        <td className="px-4 py-3 text-muted-silver text-right">{r.testCost ? formatCompactCurrency(r.testCost) : '—'}</td>
                        <td className={`px-4 py-3 text-center font-bold ${trendColor(r.trend)}`}>{trendIcon(r.trend)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t border-steel-slate/30">
                      <td colSpan={4} className="px-4 py-2 text-right text-sm text-muted-silver">Subtotal</td>
                      <td className="px-4 py-2 text-right text-ghost-white font-medium">{formatCompactCurrency(subtotal)}</td>
                      <td className="px-4 py-2 text-right text-muted-silver">{formatCompactCurrency(testCosts)}</td>
                      <td />
                    </tr>
                    <tr>
                      <td colSpan={4} className="px-4 py-2 text-right text-sm text-muted-silver">Total (incl. test costs)</td>
                      <td className="px-4 py-2 text-right text-ghost-white font-medium">{formatCompactCurrency(grandTotal)}</td>
                      <td /><td />
                    </tr>
                    <tr>
                      <td colSpan={4} className="px-4 py-2 text-right text-sm text-muted-silver">GST (18%)</td>
                      <td className="px-4 py-2 text-right text-muted-silver">{formatCompactCurrency(gst)}</td>
                      <td /><td />
                    </tr>
                    <tr className="border-t border-steel-slate/30">
                      <td colSpan={4} className="px-4 py-3 text-right text-base font-bold text-neon-emerald">Grand Total</td>
                      <td className="px-4 py-3 text-right text-base font-bold text-neon-emerald">{formatCompactCurrency(grandTotal + gst)}</td>
                      <td /><td />
                    </tr>
                  </tfoot>
                </table>
              </div>
              {/* Discount Section */}
              <div className="mt-4 pt-4 border-t border-steel-slate/20 grid grid-cols-3 gap-4 text-sm">
                <div className="p-3 rounded-lg bg-neon-emerald/5 border border-neon-emerald/20">
                  <p className="text-xs text-muted-silver mb-1">Volume Discount</p>
                  <p className="text-neon-emerald font-bold">-3.5%</p>
                </div>
                <div className="p-3 rounded-lg bg-electric-cyan/5 border border-electric-cyan/20">
                  <p className="text-xs text-muted-silver mb-1">Early Payment</p>
                  <p className="text-electric-cyan font-bold">-2.0%</p>
                </div>
                <div className="p-3 rounded-lg bg-violet-pulse/5 border border-violet-pulse/20">
                  <p className="text-xs text-muted-silver mb-1">Loyalty Credit</p>
                  <p className="text-violet-pulse font-bold">-1.0%</p>
                </div>
              </div>
            </Card>
          )}

          {/* ── Bids Tab ── */}
          {activeTab === 'bids' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-silver">{mockBids.length} bids for this RFP</p>
                <Button variant="primary" size="sm" leftIcon={<Tag size={12} />}>Generate New Bid</Button>
              </div>
              {mockBids.map((bid) => (
                <Card key={bid.id} variant="glass" className="hover:border-steel-slate/40 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-4">
                      <Badge variant="soft" color={bidStatusColor(bid.status)}>{bid.status}</Badge>
                      <div>
                        <p className="text-sm font-medium text-ghost-white">{bid.id} · {bid.vendor}</p>
                        <p className="text-xs text-muted-silver">Created: {bid.date} · {bid.items} items</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-ghost-white font-bold">{formatCompactCurrency(bid.amount)}</p>
                      </div>
                      <div className="flex gap-1">
                        <Button variant="secondary" size="xs">View</Button>
                        <Button variant="ghost" size="xs">Edit</Button>
                        <Button variant="ghost" size="xs" leftIcon={<Download size={10} />}>PDF</Button>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* ── Analysis Report Tab ── */}
          {activeTab === 'analysis' && (
            <div className="space-y-4">
              {/* Summary */}
              <Card variant="glass">
                <CardHeader>
                  <CardTitle>Analysis Summary</CardTitle>
                  <Badge variant="soft" color="emerald" size="sm">Score: {mockPortalSource.analysisScore}%</Badge>
                </CardHeader>
                <p className="text-sm text-muted-silver leading-relaxed">{mockAnalysisReport.summary}</p>
              </Card>

              {/* Term Categories */}
              <Card variant="glass">
                <CardHeader>
                  <CardTitle>Extracted Term Categories</CardTitle>
                  <span className="text-xs text-muted-silver">{mockPortalSource.extractedTerms} total terms</span>
                </CardHeader>
                <div className="space-y-3">
                  {mockAnalysisReport.termCategories.map((cat) => (
                    <div key={cat.category} className="flex items-center gap-4">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-ghost-white">{cat.category}</span>
                          <span className="text-xs text-muted-silver">{cat.count} terms · {cat.confidence}% confidence</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-steel-slate/30">
                          <div
                            className={`h-full rounded-full transition-all ${
                              cat.confidence >= 90 ? 'bg-neon-emerald' : cat.confidence >= 80 ? 'bg-amber-glow' : 'bg-coral-flame'
                            }`}
                            style={{ width: `${cat.confidence}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Key Findings */}
              <Card variant="glass">
                <CardHeader>
                  <CardTitle>Key Findings</CardTitle>
                </CardHeader>
                <div className="space-y-2">
                  {mockAnalysisReport.keyFindings.map((finding, i) => (
                    <div key={i} className="flex items-start gap-3 py-2 px-3 rounded-lg bg-steel-slate/10">
                      <CheckCircle2 size={14} className="text-electric-cyan flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-ghost-white">{finding}</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Download Reports */}
              <div className="flex gap-3">
                <Button variant="secondary" size="sm" leftIcon={<Download size={14} />}>
                  Download JSON Report
                </Button>
                <Button variant="secondary" size="sm" leftIcon={<Download size={14} />}>
                  Download Text Report
                </Button>
                <Button variant="primary" size="sm" leftIcon={<FileText size={14} />}>
                  View Full Report
                </Button>
              </div>
            </div>
          )}

          {/* ── Agent Logs Tab ── */}
          {activeTab === 'agents' && (
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Agent Activity Timeline</CardTitle>
                <div className="flex gap-1.5">
                  {['All', 'Master', 'Sales', 'Technical', 'Pricing'].map((f) => (
                    <Badge key={f} variant="outline" color="cyan" size="sm" className="cursor-pointer hover:bg-electric-cyan/10">{f}</Badge>
                  ))}
                </div>
              </CardHeader>
              <div className="space-y-0">
                {mockAgentLogs.map((log, i) => (
                  <div key={log.id} className="relative flex items-start gap-4 pb-6 last:pb-0">
                    {/* Timeline line */}
                    {i < mockAgentLogs.length - 1 && (
                      <div className="absolute left-[15px] top-9 bottom-0 w-px bg-steel-slate/25" />
                    )}
                    {/* Agent icon */}
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ring-2 ring-deep-navy"
                      style={{ backgroundColor: `${log.color}20` }}
                    >
                      <Bot size={14} style={{ color: log.color }} />
                    </div>
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-ghost-white">{log.agent}</span>
                        <Badge variant="soft" color="emerald" size="sm">{log.status}</Badge>
                        <span className="text-xs text-muted-silver ml-auto flex-shrink-0">{log.duration}</span>
                      </div>
                      <p className="text-sm text-muted-silver mt-1">{log.action}</p>
                      {/* Expandable JSON */}
                      <button
                        className="text-xs text-electric-cyan/70 hover:text-electric-cyan mt-1.5 transition-colors"
                        onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                      >
                        {expandedLog === log.id ? 'Hide data ▲' : 'Show data ▼'}
                      </button>
                      <AnimatePresence>
                        {expandedLog === log.id && (
                          <motion.pre
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="mt-2 p-3 rounded-lg bg-deep-navy/60 text-xs text-electric-cyan/80 font-mono overflow-x-auto"
                          >
                            {JSON.stringify(JSON.parse(log.data), null, 2)}
                          </motion.pre>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* ── Audit Tab ── */}
          {activeTab === 'audit' && (
            <Card variant="glass">
              <CardHeader>
                <CardTitle>Audit Trail</CardTitle>
                <div className="flex gap-1.5">
                  {['All', 'Status', 'Pipeline', 'Bids'].map((f) => (
                    <Badge key={f} variant="outline" color="violet" size="sm" className="cursor-pointer hover:bg-violet-pulse/10">{f}</Badge>
                  ))}
                </div>
              </CardHeader>
              <div className="space-y-0">
                {mockAuditTrail.map((entry, i) => (
                  <div key={entry.id} className="relative flex items-start gap-4 pb-5 last:pb-0">
                    {i < mockAuditTrail.length - 1 && (
                      <div className="absolute left-[15px] top-8 bottom-0 w-px bg-steel-slate/20" />
                    )}
                    <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-violet-pulse/10">
                      <Shield size={14} className="text-violet-pulse" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="soft" color="violet" size="sm">{entry.action}</Badge>
                        <span className="text-xs text-muted-silver">{entry.user}</span>
                        <span className="text-xs text-muted-silver/60 ml-auto flex-shrink-0">{entry.timestamp}</span>
                      </div>
                      <p className="text-sm text-muted-silver mt-1">{entry.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}
