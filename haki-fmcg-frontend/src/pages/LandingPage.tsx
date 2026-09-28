import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  CheckCircle2,
  ExternalLink,
  ChevronDown,
  Menu,
  X,
  FileCheck,
  TrendingUp,
  Database,
  UploadCloud,
  FileSpreadsheet,
  Building2,
} from 'lucide-react';
import { useAuthStore } from '@/stores';

interface SpecSample {
  query: string;
  matchedSku: string;
  brand: string;
  category: string;
  conductor: string;
  cores: string;
  size: string;
  insulation: string;
  voltage: string;
  score: number;
  price: string;
  margin: string;
  standards: string;
}

const SAMPLE_SPECS: SpecSample[] = [
  {
    query: '3 Core 2.5 sq mm XLPE Armoured Copper Cable 1100V',
    matchedSku: 'POL-XLPE-3C-2.5-ARM-CU',
    brand: 'Polycab',
    category: 'LT Power Cables',
    conductor: 'Electrolytic Copper (Class 2)',
    cores: '3 Core',
    size: '2.5 sq mm',
    insulation: 'Cross-Linked Polyethylene (XLPE)',
    voltage: '1100V (IS 7098 Part 1)',
    score: 99.4,
    price: '₹ 148.50 / m',
    margin: '+18.2% margin',
    standards: 'IS 7098 (Pt 1), IEC 60502',
  },
  {
    query: '4 Core 16 sq mm Aluminium Armoured Underground Cable',
    matchedSku: 'HAV-AL-4C-16-AR-PVC',
    brand: 'Havells',
    category: 'LT Power Cables',
    conductor: 'Solid / Stranded Aluminium',
    cores: '4 Core',
    size: '16.0 sq mm',
    insulation: 'Heavy Duty PVC (Type A)',
    voltage: '650/1100V',
    score: 98.7,
    price: '₹ 94.20 / m',
    margin: '+15.5% margin',
    standards: 'IS 1554 (Pt 1)',
  },
  {
    query: '1.5 sq mm Multicore Flexible Copper Industrial Wire',
    matchedSku: 'FIN-FLX-3C-1.5-CU-FR',
    brand: 'Finolex',
    category: 'Flexible Multicore',
    conductor: 'Annealed Bare Copper Flexible',
    cores: '3 Core',
    size: '1.5 sq mm',
    insulation: 'Flame Retardant (FR) PVC',
    voltage: '1100V',
    score: 97.9,
    price: '₹ 42.80 / m',
    margin: '+22.0% margin',
    standards: 'IS 694, BS EN 50525',
  },
  {
    query: '10 sq mm Single Core Solar DC Cable 1500V UV Resistant',
    matchedSku: 'RRK-SOL-1C-10-XLPO',
    brand: 'RR Kabel',
    category: 'Solar PV Cables',
    conductor: 'Tinned Copper Flexible Class 5',
    cores: 'Single Core',
    size: '10.0 sq mm',
    insulation: 'Crosslinked Polyolefin (XLPO)',
    voltage: '1500V DC (EN 50618)',
    score: 99.1,
    price: '₹ 112.00 / m',
    margin: '+19.4% margin',
    standards: 'TÜV 2 Pfg 1169/08.2007',
  },
];

export default function LandingPage() {
  const { isAuthenticated, user } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSpecIndex, setActiveSpecIndex] = useState(0);
  const [customSearch, setCustomSearch] = useState('');

  const currentSpec = SAMPLE_SPECS[activeSpecIndex] ?? SAMPLE_SPECS[0]!;

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900">
      {/* ── Fixed Top Navbar (HAKI | FMCG 2.0) ── */}
      <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-[#FAF8F5]/90 backdrop-blur-md border-b border-black/[0.06]">
        <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5">
              <span className="font-extrabold text-2xl tracking-tight text-slate-900 font-sans">
                HAKI
              </span>
              <span className="text-slate-300 font-light text-xl">|</span>
              <span className="text-[12px] font-bold text-[#2563EB] tracking-[0.16em] uppercase">
                FMCG 2.0
              </span>
            </Link>
          </div>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#pipeline" className="hover:text-slate-900 transition-colors">
              RFP Pipeline
            </a>
            <a href="#catalog" className="hover:text-slate-900 transition-colors">
              22K+ Catalog
            </a>
            <a href="#matcher" className="hover:text-slate-900 transition-colors">
              Spec Matcher
            </a>
            <a href="#solutions" className="hover:text-slate-900 transition-colors">
              AI Agents
            </a>
            <Link to="/vendors" className="hover:text-slate-900 transition-colors">
              Vendors
            </Link>
            <a
              href="http://localhost:8000/api/v1/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-900 transition-colors flex items-center gap-1"
            >
              API Docs
              <ExternalLink size={12} className="text-slate-400" />
            </a>
          </nav>

          {/* Right Action Buttons */}
          <div className="hidden sm:flex items-center gap-4">
            <Link
              to="/user"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 flex items-center gap-1.5 transition-colors"
            >
              <Building2 size={15} className="text-slate-500" />
              Vendor Portal
            </Link>

            {isAuthenticated ? (
              <Link
                to={user?.role === 'admin' || user?.role === 'manager' ? '/dashboard' : '/user'}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-sm font-semibold transition-all shadow-sm"
              >
                Go to Platform
                <ArrowRight size={14} />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors px-2 py-1"
                >
                  Sign In
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-sm font-semibold transition-all shadow-sm"
                >
                  <UploadCloud size={14} />
                  Upload RFP
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-slate-600 hover:text-slate-900"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#FAF8F5] border-b border-black/[0.08] px-6 py-4 space-y-3">
            <a
              href="#pipeline"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-700"
            >
              RFP Pipeline
            </a>
            <a
              href="#catalog"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-700"
            >
              22K+ Catalog
            </a>
            <a
              href="#matcher"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-700"
            >
              Spec Matcher
            </a>
            <a
              href="#solutions"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-700"
            >
              AI Agents
            </a>
            <div className="pt-2 border-t border-slate-200 flex flex-col gap-2">
              <Link
                to="/login"
                className="w-full text-center py-2 text-sm font-semibold text-white bg-[#2563EB] rounded-md flex items-center justify-center gap-1.5"
              >
                <UploadCloud size={14} />
                Upload RFP
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ── Hero Section (Matches Editorial Craft Layout) ── */}
      <section className="pt-32 pb-20 px-6 max-w-7xl mx-auto">
        {/* Category kicker / tag */}
        <div className="mb-6">
          <span className="text-[#2563EB] text-[11px] font-bold tracking-[0.2em] uppercase font-mono">
            THE AI PROCUREMENT & TENDER ENGINE FOR FMCG & ELECTRICALS
          </span>
        </div>

        {/* Two-column headline + description */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
          <div className="lg:col-span-7">
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black text-slate-900 tracking-[-0.035em] leading-[1.04]">
              Smart RFPs.
              <br />
              <span className="text-[#2563EB]">Lasting precision.</span>
            </h1>
          </div>

          <div className="lg:col-span-5 flex flex-col justify-end space-y-5">
            <p className="text-slate-600 text-base md:text-lg leading-relaxed font-normal">
              HAKI FMCG transforms complex industrial procurement across 22,000+ catalog products, automated multi-page OCR parsing, LangChain agent reasoning, and real-time margin benchmarking.
            </p>
            <div className="flex flex-wrap items-center gap-6 pt-1">
              <a
                href="#catalog"
                className="text-[#2563EB] font-semibold text-sm hover:underline flex items-center gap-1.5 group"
              >
                Explore 22K+ catalog
                <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
              </a>
              <a
                href="#matcher"
                className="text-[#2563EB] font-semibold text-sm hover:underline flex items-center gap-1.5 group"
              >
                Interactive spec matcher
                <ChevronDown size={14} className="group-hover:translate-y-0.5 transition-transform" />
              </a>
            </div>
          </div>
        </div>

        {/* Tinted Banner Card (Matches Soft Blue Accent Container) */}
        <div className="mt-14 p-8 md:p-10 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE]/80 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-[0_2px_12px_rgba(37,99,235,0.06)]">
          <div className="space-y-2 max-w-2xl">
            <h3 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              Procure with teams who demand exact specs.
            </h3>
            <p className="text-slate-600 text-sm md:text-base leading-relaxed">
              Upload technical tender PDFs or query 22,028 wire and cable SKUs. Instant compliance scores, margin calculations, and automated vendor proposal generation.
            </p>
          </div>
          <div className="flex-shrink-0">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#1D4ED8] hover:bg-[#1E40AF] text-white font-semibold text-sm transition-all shadow-sm hover:shadow-md"
            >
              Start RFP Processing
              <span className="text-base font-bold">↗</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Key Metrics Bar ── */}
      <section className="border-y border-black/[0.06] bg-white/60 py-10 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <div className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight">22,028</div>
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mt-1">
              Catalog SKUs Pre-Indexed
            </div>
          </div>
          <div>
            <div className="text-3xl md:text-4xl font-black text-[#2563EB] tracking-tight">&lt; 1.2s</div>
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mt-1">
              Semantic Search Latency
            </div>
          </div>
          <div>
            <div className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight">99.4%</div>
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mt-1">
              Spec Extraction Precision
            </div>
          </div>
          <div>
            <div className="text-3xl md:text-4xl font-black text-emerald-600 tracking-tight">526 / 526</div>
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mt-1">
              CI Test Cases Passing
            </div>
          </div>
        </div>
      </section>

      {/* ── Interactive Live Spec Matcher Sandbox ── */}
      <section id="matcher" className="py-20 px-6 max-w-7xl mx-auto">
        <div className="mb-10 text-center max-w-2xl mx-auto">
          <span className="text-[#2563EB] text-xs font-bold tracking-[0.2em] uppercase font-mono">
            LIVE INTERACTIVE SPEC ENGINE
          </span>
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight mt-2">
            Test Instant Wire & Cable Matching
          </h2>
          <p className="text-slate-600 text-sm md:text-base mt-2">
            Click a real-world tender requirement or enter specifications to test vector similarity and compliance scoring in real time.
          </p>
        </div>

        {/* Query Selector Tabs */}
        <div className="flex flex-wrap gap-2 justify-center mb-8">
          {SAMPLE_SPECS.map((sample, idx) => (
            <button
              key={idx}
              onClick={() => {
                setActiveSpecIndex(idx);
                setCustomSearch('');
              }}
              className={`px-4 py-2 rounded-lg text-xs md:text-sm font-medium transition-all ${
                activeSpecIndex === idx && !customSearch
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-white text-slate-700 border border-slate-200 hover:border-slate-300'
              }`}
            >
              {sample.brand}: {sample.size} {sample.cores}
            </button>
          ))}
        </div>

        {/* Interactive Query Box */}
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-[0_8px_30px_rgba(0,0,0,0.04)] p-6 md:p-8">
          <div className="relative mb-6">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              value={customSearch || currentSpec.query}
              onChange={(e) => setCustomSearch(e.target.value)}
              placeholder="e.g. 3 Core 2.5 sq mm XLPE Armoured Copper Cable..."
              className="w-full pl-12 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 font-medium text-sm md:text-base focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            />
          </div>

          {/* Result Card */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 bg-slate-50/80 rounded-xl p-6 border border-slate-200/70">
            {/* Left Result Details */}
            <div className="lg:col-span-8 space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <span className="px-2.5 py-1 rounded bg-blue-100 text-blue-800 text-xs font-bold font-mono">
                  {currentSpec.matchedSku}
                </span>
                <span className="px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 text-xs font-semibold flex items-center gap-1">
                  <CheckCircle2 size={13} />
                  {currentSpec.score}% Match Confidence
                </span>
                <span className="px-2.5 py-1 rounded bg-slate-200 text-slate-800 text-xs font-semibold">
                  {currentSpec.brand} Catalog
                </span>
              </div>

              <h4 className="text-xl md:text-2xl font-bold text-slate-900">
                {currentSpec.brand} {currentSpec.size} {currentSpec.cores} {currentSpec.category}
              </h4>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs md:text-sm pt-2">
                <div className="bg-white p-3 rounded-lg border border-slate-200/70">
                  <span className="text-slate-500 block text-[11px] uppercase font-semibold">Conductor</span>
                  <span className="font-semibold text-slate-900">{currentSpec.conductor}</span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200/70">
                  <span className="text-slate-500 block text-[11px] uppercase font-semibold">Insulation</span>
                  <span className="font-semibold text-slate-900">{currentSpec.insulation}</span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200/70">
                  <span className="text-slate-500 block text-[11px] uppercase font-semibold">Voltage Rating</span>
                  <span className="font-semibold text-slate-900">{currentSpec.voltage}</span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200/70">
                  <span className="text-slate-500 block text-[11px] uppercase font-semibold">Standard Code</span>
                  <span className="font-semibold text-slate-900">{currentSpec.standards}</span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200/70">
                  <span className="text-slate-500 block text-[11px] uppercase font-semibold">Cores & Size</span>
                  <span className="font-semibold text-slate-900">{currentSpec.cores} • {currentSpec.size}</span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200/70">
                  <span className="text-slate-500 block text-[11px] uppercase font-semibold">Vector Index</span>
                  <span className="font-semibold text-blue-700">384-Dim Normalized</span>
                </div>
              </div>
            </div>

            {/* Right Pricing & Quick CTA */}
            <div className="lg:col-span-4 bg-white rounded-xl p-5 border border-slate-200 flex flex-col justify-between">
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
                  Benchmarked Unit Rate
                </span>
                <div className="text-3xl font-black text-slate-900 mt-1">
                  {currentSpec.price}
                </div>
                <div className="inline-block mt-2 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
                  {currentSpec.margin}
                </div>

                <p className="text-xs text-slate-500 mt-4 leading-relaxed">
                  Calculated against daily MCX Copper / Aluminium base indices with manufacturing cost matrix.
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100">
                <Link
                  to="/login"
                  className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-semibold text-xs transition-colors shadow-sm"
                >
                  Generate Tender Proposal
                  <ArrowRight size={14} />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 6 Core Platform Pillars Grid ── */}
      <section id="solutions" className="py-20 px-6 max-w-7xl mx-auto border-t border-black/[0.06]">
        <div className="mb-14">
          <span className="text-[#2563EB] text-xs font-bold tracking-[0.2em] uppercase font-mono">
            BUILT FOR SCALE & RIGOR
          </span>
          <h2 className="text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight mt-2">
            Engineered for high-stakes electrical RFPs.
          </h2>
          <p className="text-slate-600 text-base md:text-lg max-w-2xl mt-3">
            Every layer—from optical character recognition to multi-agent pricing logic—is constructed to eliminate proposal errors and capture higher gross margins.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="bg-white p-8 rounded-xl border border-slate-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all group">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-[#2563EB] flex items-center justify-center font-bold mb-6">
              <Database size={20} />
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight group-hover:text-[#2563EB] transition-colors">
              22,028 Verified SKUs
            </h3>
            <p className="text-slate-600 text-sm mt-2 leading-relaxed">
              Curated catalog covering Polycab, Havells, KEI, RR Kabel, and Finolex with voltage tiers, conductor metallurgy, armor configurations, and standard ratings.
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-white p-8 rounded-xl border border-slate-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all group">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold mb-6">
              <FileCheck size={20} />
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight group-hover:text-emerald-700 transition-colors">
              Tesseract OCR & Document AI
            </h3>
            <p className="text-slate-600 text-sm mt-2 leading-relaxed">
              Automatic discovery of local OCR binaries. Extracts tabular technical annexures, scanned NIT notices, and multilingual Hindi/English specifications with 99.4% accuracy.
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-white p-8 rounded-xl border border-slate-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all group">
            <div className="w-10 h-10 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center font-bold mb-6">
              <Cpu size={20} />
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight group-hover:text-violet-700 transition-colors">
              Multi-Agent LangChain System
            </h3>
            <p className="text-slate-600 text-sm mt-2 leading-relaxed">
              Autonomous coordination: Intake Agent extracts parameters, Matcher calculates cross-standard fits, and Pricing Agent computes competitive margins with fallback synthesis.
            </p>
          </div>

          {/* Card 4 */}
          <div className="bg-white p-8 rounded-xl border border-slate-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all group">
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold mb-6">
              <TrendingUp size={20} />
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight group-hover:text-amber-700 transition-colors">
              Margin & Pricing Intelligence
            </h3>
            <p className="text-slate-600 text-sm mt-2 leading-relaxed">
              Commodity-linked cost tracking. Recommends aggressive winning bid prices while protecting floor margins based on historical tender victory analytics.
            </p>
          </div>

          {/* Card 5 */}
          <div className="bg-white p-8 rounded-xl border border-slate-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all group">
            <div className="w-10 h-10 rounded-lg bg-cyan-50 text-[#2563EB] flex items-center justify-center font-bold mb-6">
              <Layers size={20} />
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight group-hover:text-[#2563EB] transition-colors">
              384-Dim Vector Embedder
            </h3>
            <p className="text-slate-600 text-sm mt-2 leading-relaxed">
              Ultra-lightweight embedded semantic representation specialized for electrical terminology, wire gauge conversion (AWG to mm²), and cross-manufacturer equivalence.
            </p>
          </div>

          {/* Card 6 */}
          <div className="bg-white p-8 rounded-xl border border-slate-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] hover:border-slate-300 transition-all group">
            <div className="w-10 h-10 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center font-bold mb-6">
              <ShieldCheck size={20} />
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight group-hover:text-rose-700 transition-colors">
              Compliance & Audit Trail
            </h3>
            <p className="text-slate-600 text-sm mt-2 leading-relaxed">
              Cryptographic trace IDs for every agent action, immutable bid revision histories, and webhook events for automated ERP integration.
            </p>
          </div>
        </div>
      </section>

      {/* ── Architecture Pipeline ── */}
      <section id="pipeline" className="py-20 px-6 bg-white/70 border-t border-black/[0.06]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-[#2563EB] text-xs font-bold tracking-[0.2em] uppercase font-mono">
              END-TO-END TENDER FLOW
            </span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight mt-2">
              From raw tender PDF to winning bid in 60 seconds.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
            <div className="bg-[#FAF8F5] p-6 rounded-xl border border-slate-200 relative">
              <span className="text-xs font-bold text-[#2563EB] font-mono">01</span>
              <h4 className="text-base font-bold text-slate-900 mt-2">Intake & OCR</h4>
              <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                PyPDF + Tesseract parses complex PDF, scanned images, and Excel BOQs.
              </p>
            </div>

            <div className="bg-[#FAF8F5] p-6 rounded-xl border border-slate-200 relative">
              <span className="text-xs font-bold text-[#2563EB] font-mono">02</span>
              <h4 className="text-base font-bold text-slate-900 mt-2">Normalization</h4>
              <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                Standardizes voltage (1.1kV vs 1100V), core counts, and AWG to mm².
              </p>
            </div>

            <div className="bg-[#FAF8F5] p-6 rounded-xl border border-slate-200 relative">
              <span className="text-xs font-bold text-[#2563EB] font-mono">03</span>
              <h4 className="text-base font-bold text-slate-900 mt-2">Vector Search</h4>
              <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                Dense 384-dim semantic matching queries 22,028 products in under 50ms.
              </p>
            </div>

            <div className="bg-[#FAF8F5] p-6 rounded-xl border border-slate-200 relative">
              <span className="text-xs font-bold text-[#2563EB] font-mono">04</span>
              <h4 className="text-base font-bold text-slate-900 mt-2">Pricing Engine</h4>
              <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                Commodity index lookup and automated margin optimizations.
              </p>
            </div>

            <div className="bg-[#EFF6FF] p-6 rounded-xl border border-blue-200 relative">
              <span className="text-xs font-bold text-[#2563EB] font-mono">05</span>
              <h4 className="text-base font-bold text-slate-900 mt-2">Commercial Bid</h4>
              <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
                Full compliance matrix and exportable tender response.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Catalog Showcase ── */}
      <section id="catalog" className="py-20 px-6 max-w-7xl mx-auto border-t border-black/[0.06]">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div>
            <span className="text-[#2563EB] text-xs font-bold tracking-[0.2em] uppercase font-mono">
              PRE-INDEXED MANUFACTURER CATALOG
            </span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight mt-2">
              Wires, Cables, & FMCG Standards
            </h2>
          </div>
          <Link
            to="/products"
            className="text-[#2563EB] font-semibold text-sm hover:underline flex items-center gap-1.5"
          >
            Explore all 22,028 products →
          </Link>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-5 bg-white rounded-xl border border-slate-200">
            <h5 className="font-bold text-slate-900 text-sm">LT Power Cables</h5>
            <p className="text-xs text-slate-500 mt-1">1.1 kV XLPE & PVC Armoured</p>
            <span className="text-xs font-semibold text-[#2563EB] mt-3 inline-block">7,420 SKUs</span>
          </div>

          <div className="p-5 bg-white rounded-xl border border-slate-200">
            <h5 className="font-bold text-slate-900 text-sm">HT Power Cables</h5>
            <p className="text-xs text-slate-500 mt-1">3.3 kV to 33 kV Heavy Duty</p>
            <span className="text-xs font-semibold text-[#2563EB] mt-3 inline-block">4,810 SKUs</span>
          </div>

          <div className="p-5 bg-white rounded-xl border border-slate-200">
            <h5 className="font-bold text-slate-900 text-sm">Flexible Multicore</h5>
            <p className="text-xs text-slate-500 mt-1">Industrial Grade Copper</p>
            <span className="text-xs font-semibold text-[#2563EB] mt-3 inline-block">5,140 SKUs</span>
          </div>

          <div className="p-5 bg-white rounded-xl border border-slate-200">
            <h5 className="font-bold text-slate-900 text-sm">Specialty & Solar</h5>
            <p className="text-xs text-slate-500 mt-1">FR-LSH, Fire Survival, PV</p>
            <span className="text-xs font-semibold text-[#2563EB] mt-3 inline-block">4,658 SKUs</span>
          </div>
        </div>
      </section>

      {/* ── Call To Action Banner ── */}
      <section className="py-20 px-6 max-w-7xl mx-auto">
        <div className="p-10 md:p-14 rounded-2xl bg-slate-900 text-white flex flex-col lg:flex-row lg:items-center justify-between gap-8 shadow-xl">
          <div className="space-y-3 max-w-2xl">
            <h3 className="text-3xl md:text-4xl font-extrabold tracking-tight">
              Ready to automate your technical procurement?
            </h3>
            <p className="text-slate-400 text-base leading-relaxed">
              Upload your tender specifications now or browse our comprehensive 22,000+ electrical inventory with instant margin optimization.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              to="/login"
              className="px-6 py-3.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-semibold text-sm transition-all shadow-md flex items-center gap-2"
            >
              <UploadCloud size={16} />
              Upload RFP Document
            </Link>
            <Link
              to="/products"
              className="px-6 py-3.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm transition-all border border-slate-700 flex items-center gap-2"
            >
              <FileSpreadsheet size={16} />
              Browse Product Catalog
            </Link>
          </div>
        </div>
      </section>

      {/* ── Clean Craft Footer ── */}
      <footer className="border-t border-black/[0.06] bg-[#FAF8F5] py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-slate-500">
          <div className="flex items-center gap-3">
            <span className="font-extrabold text-slate-900 tracking-tight text-sm font-sans">
              HAKI
            </span>
            <span className="text-slate-300 font-light">|</span>
            <span className="font-mono text-[10px] text-blue-600 font-bold uppercase tracking-widest">
              FMCG 2.0
            </span>
            <span className="text-slate-400 hidden sm:inline">— Enterprise RFP & Procurement Platform</span>
          </div>

          <div className="flex items-center gap-6">
            <a href="#pipeline" className="hover:text-slate-900 transition-colors">
              RFP Pipeline
            </a>
            <a href="#catalog" className="hover:text-slate-900 transition-colors">
              Catalog
            </a>
            <Link to="/vendors" className="hover:text-slate-900 transition-colors">
              Vendors
            </Link>
            <a href="http://localhost:8000/api/v1/docs" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 transition-colors flex items-center gap-1">
              API Docs
              <ExternalLink size={11} />
            </a>
          </div>

          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>All Procurement Services Operational</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
