import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Search,
  ArrowRight,
  CheckCircle2,
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
import { HakiLogo } from '@/components/common';

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

const PIPELINE_CARDS = [
  {
    step: '01',
    title: 'Intake & OCR',
    description: 'PyPDF + Tesseract parses complex PDF, scanned images, and Excel BOQs.',
    highlight: false,
  },
  {
    step: '02',
    title: 'Normalization',
    description: 'Standardizes voltage (1.1kV vs 1100V), core counts, and AWG to mm².',
    highlight: false,
  },
  {
    step: '03',
    title: 'Vector Search',
    description: 'Dense 384-dim semantic matching queries 22,028 products in under 50ms.',
    highlight: false,
  },
  {
    step: '04',
    title: 'Pricing Engine',
    description: 'Commodity index lookup and automated margin optimizations.',
    highlight: false,
  },
  {
    step: '05',
    title: 'Commercial Bid',
    description: 'Full compliance matrix and exportable tender response.',
    highlight: true,
  },
];

const CATALOG_MARQUEE_CARDS = [
  { title: 'LT Power Cables', subtitle: '1.1 kV XLPE & PVC Armoured', count: '7,420 SKUs', brand: 'Polycab / Havells' },
  { title: 'HT Power Cables', subtitle: '3.3 kV to 33 kV Heavy Duty', count: '4,810 SKUs', brand: 'KEI / Universal' },
  { title: 'Flexible Multicore', subtitle: 'Industrial Grade Copper', count: '5,140 SKUs', brand: 'Finolex / RR Kabel' },
  { title: 'Specialty & Solar', subtitle: 'FR-LSH, Fire Survival, PV', count: '4,658 SKUs', brand: 'Polycab / Siechem' },
  { title: 'Control & Shielded', subtitle: 'Armoured Instrumentation Pairs', count: '3,210 SKUs', brand: 'Havells / KEI' },
  { title: 'Building Wires', subtitle: 'IS 694 FR / FRLSH Pure Copper', count: '3,980 SKUs', brand: 'Finolex / Polycab' },
];

export default function LandingPage() {
  const { isAuthenticated, user } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeSpecIndex, setActiveSpecIndex] = useState(0);
  const [customSearch, setCustomSearch] = useState('');

  const currentSpec = SAMPLE_SPECS[activeSpecIndex] ?? SAMPLE_SPECS[0]!;

  return (
    <div className="min-h-screen bg-faded-grid text-slate-900 font-sans selection:bg-blue-100 selection:text-blue-900 relative overflow-x-hidden">
      {/* ── Fixed Top Navbar (Haki) ── */}
      <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-[#FAF8F5]/90 backdrop-blur-md border-b border-black/[0.06]">
        <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-3">
            <HakiLogo size="lg" asLink to="/" />
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
            <a href="#snapshots" className="hover:text-slate-900 transition-colors">
              Platform Modules
            </a>
            <Link to="/vendors" className="hover:text-slate-900 transition-colors">
              Vendors
            </Link>
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
                  to="/login?redirect=/user/rfp-analyzer"
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
              href="#snapshots"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-slate-700"
            >
              Platform Modules
            </a>
            <div className="pt-2 border-t border-slate-200 flex flex-col gap-2">
              <Link
                to="/login?redirect=/user/rfp-analyzer"
                className="w-full text-center py-2 text-sm font-semibold text-white bg-[#2563EB] rounded-md flex items-center justify-center gap-1.5"
              >
                <UploadCloud size={14} />
                Upload RFP
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ── Hero Section ── */}
      <section className="pt-24 md:pt-28 pb-16 px-6 max-w-7xl mx-auto">
        <div className="mb-4">
          <span className="text-[#2563EB] text-xs sm:text-sm md:text-[15px] font-bold tracking-[0.16em] uppercase font-mono">
            THE AI PROCUREMENT & TENDER ENGINE FOR ELECTRICALS & INDUSTRIAL GOODS
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
          <div className="lg:col-span-7">
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black text-slate-900 tracking-[-0.035em] leading-[1.04]">
              Smart RFPs.
              <br />
              <span className="text-[#2563EB]">Lasting precision.</span>
            </h1>

            {/* Minimalist divider line below headline */}
            <div className="w-full my-5 border-b border-slate-200/90" />

            {/* Single elegant sentence with refined typography */}
            <p className="text-base sm:text-lg md:text-xl text-slate-600 font-normal leading-relaxed tracking-tight max-w-2xl">
              Turn complex technical tender specifications into verified, audit-ready commercial bids with absolute precision.
            </p>
          </div>

          <div className="lg:col-span-5 flex items-center justify-center lg:justify-end relative lg:pt-2">
            {/* Ambient soft glow behind robot */}
            <div className="absolute w-64 h-64 sm:w-72 sm:h-72 rounded-full bg-gradient-to-tr from-blue-400/20 via-cyan-300/15 to-transparent blur-3xl pointer-events-none" />
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              className="relative z-10 flex flex-col items-center select-none"
            >
              <img
                src="/haki-mascot.png"
                alt="Haki AI Mascot"
                className="w-56 h-56 sm:w-64 sm:h-64 lg:w-72 lg:h-72 object-contain drop-shadow-[0_20px_35px_rgba(37,99,235,0.18)] transition-transform duration-500 hover:scale-105"
              />
            </motion.div>
          </div>
        </div>

        {/* Tinted Banner Card */}
        <motion.div
          initial={{ opacity: 0.25, y: 55, filter: 'blur(3px)' }}
          whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          viewport={{ once: false, amount: 0.2, margin: '0px 0px -70px 0px' }}
          transition={{ duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
          className="mt-14 p-8 md:p-10 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE]/80 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-[0_2px_12px_rgba(37,99,235,0.06)]"
        >
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
        </motion.div>
      </section>

      {/* ── Continuous Moving Marquees: Workflow Pipeline & Catalog Categories ── */}
      <section id="pipeline" className="py-16 border-y border-black/[0.06] overflow-hidden bg-white/40 space-y-12">
        {/* Track 1: Workflow Pipeline Heading */}
        <div>
          <div className="max-w-7xl mx-auto px-6 mb-5 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#2563EB] animate-pulse"></span>
              <span className="text-xs uppercase tracking-[0.18em] font-extrabold text-slate-800 font-mono">
                END-TO-END TENDER WORKFLOW PIPELINE
              </span>
            </div>
            <span className="text-xs font-semibold text-slate-500 hidden sm:inline">
              Continuous multi-agent flow • Ingestion to commercial bid
            </span>
          </div>

          {/* Marquee Wrapper: Pipeline Flow */}
          <div className="relative w-full overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)]">
            <div className="animate-marquee flex gap-6 py-2">
              {/* First Set of Pipeline Cards */}
              {PIPELINE_CARDS.map((card, idx) => (
                <div
                  key={`pipe-1-${idx}`}
                  className={`w-[390px] md:w-[420px] h-[220px] flex-shrink-0 p-8 rounded-2xl border transition-all flex flex-col justify-between ${
                    card.highlight
                      ? 'bg-[#EFF6FF] border-[#BFDBFE] shadow-sm'
                      : 'bg-white border-slate-200/90 shadow-[0_2px_12px_rgba(0,0,0,0.03)]'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-extrabold text-[#2563EB] font-mono tracking-wider">
                        STAGE {card.step}
                      </span>
                      <span className="w-2.5 h-2.5 rounded-full bg-blue-500/30"></span>
                    </div>
                    <h4 className="text-xl font-extrabold text-slate-900 mt-2.5 tracking-tight">{card.title}</h4>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">{card.description}</p>
                </div>
              ))}
              {/* Duplicated Set for Gapless Infinite Right-to-Left Scroll */}
              {PIPELINE_CARDS.map((card, idx) => (
                <div
                  key={`pipe-2-${idx}`}
                  className={`w-[390px] md:w-[420px] h-[220px] flex-shrink-0 p-8 rounded-2xl border transition-all flex flex-col justify-between ${
                    card.highlight
                      ? 'bg-[#EFF6FF] border-[#BFDBFE] shadow-sm'
                      : 'bg-white border-slate-200/90 shadow-[0_2px_12px_rgba(0,0,0,0.03)]'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-extrabold text-[#2563EB] font-mono tracking-wider">
                        STAGE {card.step}
                      </span>
                      <span className="w-2.5 h-2.5 rounded-full bg-blue-500/30"></span>
                    </div>
                    <h4 className="text-xl font-extrabold text-slate-900 mt-2.5 tracking-tight">{card.title}</h4>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">{card.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Track 2: Catalog Inventory Heading */}
        <div>
          <div className="max-w-7xl mx-auto px-6 mb-5 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs uppercase tracking-[0.18em] font-extrabold text-slate-800 font-mono">
                22,028 PRE-INDEXED WIRES & CABLES INVENTORY
              </span>
            </div>
            <span className="text-xs font-semibold text-slate-500 hidden sm:inline">
              Live manufacturer database • Polycab, Havells, KEI, Finolex, RR Kabel
            </span>
          </div>

          {/* Marquee Wrapper: Catalog Categories */}
          <div className="relative w-full overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)]">
            <div className="animate-marquee-slow flex gap-6 py-2">
              {CATALOG_MARQUEE_CARDS.map((cat, idx) => (
                <div
                  key={`cat-1-${idx}`}
                  className="w-[390px] md:w-[420px] h-[220px] flex-shrink-0 p-8 rounded-2xl bg-white border border-slate-200/90 shadow-[0_2px_12px_rgba(0,0,0,0.03)] flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{cat.brand}</span>
                      <span className="text-xs font-extrabold text-[#2563EB] font-mono bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200/50">
                        {cat.count}
                      </span>
                    </div>
                    <h5 className="text-xl font-extrabold text-slate-900 mt-2.5 tracking-tight">{cat.title}</h5>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">{cat.subtitle}</p>
                </div>
              ))}
              {/* Duplicate Set for Gapless Infinite Scroll */}
              {CATALOG_MARQUEE_CARDS.map((cat, idx) => (
                <div
                  key={`cat-2-${idx}`}
                  className="w-[390px] md:w-[420px] h-[220px] flex-shrink-0 p-8 rounded-2xl bg-white border border-slate-200/90 shadow-[0_2px_12px_rgba(0,0,0,0.03)] flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{cat.brand}</span>
                      <span className="text-xs font-extrabold text-[#2563EB] font-mono bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200/50">
                        {cat.count}
                      </span>
                    </div>
                    <h5 className="text-xl font-extrabold text-slate-900 mt-2.5 tracking-tight">{cat.title}</h5>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">{cat.subtitle}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Staggered Website Snapshots with Window Controls (🔴 ⚪ 🟢) ── */}
      <section id="snapshots" className="py-24 px-6 max-w-7xl mx-auto space-y-28">
        <div className="text-center max-w-3xl mx-auto">
          <span className="text-[#2563EB] text-xs font-bold tracking-[0.2em] uppercase font-mono">
            LIVE PLATFORM MODULES
          </span>
          <h2 className="text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight mt-2">
            Inside the Haki Engine
          </h2>
          <p className="text-slate-600 text-sm md:text-base mt-3">
            Precise technical intelligence modules built for tenders, specifications, and margin security.
          </p>
        </div>

        {/* ── Snapshot 1: Left Aligned (RFP Intake & OCR Parser) ── */}
        <motion.div
          initial={{ opacity: 0.2, y: 60, filter: 'blur(4px)' }}
          whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          viewport={{ once: false, amount: 0.2, margin: '0px 0px -80px 0px' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center"
        >
          {/* Left Window Snapshot */}
          <div className="lg:col-span-7">
            <div className="rounded-xl overflow-hidden border border-slate-300/80 shadow-[0_16px_40px_rgba(0,0,0,0.08)] bg-white">
              {/* macOS Style Window Bar with Red, White, Green Controls */}
              <div className="h-10 bg-slate-100/90 border-b border-slate-200 px-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#EF4444] border border-red-500 inline-block"></span>
                  <span className="w-3 h-3 rounded-full bg-[#FFFFFF] border border-slate-300 inline-block"></span>
                  <span className="w-3 h-3 rounded-full bg-[#10B981] border border-emerald-500 inline-block"></span>
                </div>
                <div className="text-xs font-medium text-slate-500 font-mono flex items-center gap-1.5">
                  <FileCheck size={12} className="text-blue-600" />
                  haki-rfp-parser-v2.pdf [Processed: 99.4% Confidence]
                </div>
                <div className="w-10"></div>
              </div>

              {/* Realistic App Content */}
              <div className="p-6 bg-slate-50/50 space-y-4">
                <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-slate-200">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-xs font-bold font-mono">
                      NIT-ELECTRICAL-2026-09
                    </span>
                    <span className="text-xs text-slate-600 font-medium">Bokaro Steel Substation Cable Supply</span>
                  </div>
                  <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                    <CheckCircle2 size={13} /> OCR Verified
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 uppercase font-semibold">
                        <th className="pb-2">Line</th>
                        <th className="pb-2">Parsed Specification</th>
                        <th className="pb-2">Standard</th>
                        <th className="pb-2">Normalized Gauge</th>
                        <th className="pb-2">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                      <tr>
                        <td className="py-2.5 font-mono text-slate-500">01</td>
                        <td>3C x 2.5 sq mm Armoured Cu Cable</td>
                        <td>IS 7098 Pt 1</td>
                        <td className="font-mono text-blue-600">2.5 mm² (1100V)</td>
                        <td><span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold">MATCHED</span></td>
                      </tr>
                      <tr>
                        <td className="py-2.5 font-mono text-slate-500">02</td>
                        <td>4 Core 16 sq mm Aluminium LT Cable</td>
                        <td>IS 1554 Pt 1</td>
                        <td className="font-mono text-blue-600">16.0 mm² (1100V)</td>
                        <td><span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold">MATCHED</span></td>
                      </tr>
                      <tr>
                        <td className="py-2.5 font-mono text-slate-500">03</td>
                        <td>1.5 sq mm Multicore Flexible Copper</td>
                        <td>IS 694</td>
                        <td className="font-mono text-blue-600">1.5 mm² (Class 5)</td>
                        <td><span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold">MATCHED</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-200/80 text-xs">
                  <span className="text-slate-500">Tesseract OCR multilingual engine auto-detected</span>
                  <span className="font-bold text-[#2563EB]">14 Line Items Extracted • 0 Errors</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Text Description */}
          <div className="lg:col-span-5 space-y-4">
            <span className="text-xs font-bold text-[#2563EB] tracking-widest uppercase font-mono">
              01 • INGESTION & EXTRACTION
            </span>
            <h3 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              Automated Tender PDF & OCR Extraction
            </h3>
            <p className="text-slate-600 text-sm md:text-base leading-relaxed">
              Upload raw government NITs, private enterprise RFPs, and scanned tender specifications. The engine automatically executes optical character recognition, strips watermarks, and parses tabular schedules into normalized data structures.
            </p>
            <div className="pt-2">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 text-sm font-semibold text-[#2563EB] hover:underline"
              >
                Upload sample tender PDF →
              </Link>
            </div>
          </div>
        </motion.div>

        {/* ── Snapshot 2: Right Aligned (22,000+ Vector Product Catalog) ── */}
        <motion.div
          initial={{ opacity: 0.2, y: 60, filter: 'blur(4px)' }}
          whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          viewport={{ once: false, amount: 0.2, margin: '0px 0px -80px 0px' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center"
        >
          {/* Left Text Description */}
          <div className="lg:col-span-5 space-y-4 order-2 lg:order-1">
            <span className="text-xs font-bold text-[#2563EB] tracking-widest uppercase font-mono">
              02 • VECTOR SIMILARITY ENGINE
            </span>
            <h3 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              22,028 Pre-Indexed Wires & Cables Catalog
            </h3>
            <p className="text-slate-600 text-sm md:text-base leading-relaxed">
              Cross-standard vector matching powered by domain-specialized 384-dimensional embeddings. Automatically translates American Wire Gauge (AWG) to metric mm², XLPE vs PVC insulation grades, and matches exact SKUs across Polycab, Havells, KEI, and Finolex.
            </p>
            <div className="pt-2">
              <Link
                to="/products"
                className="inline-flex items-center gap-2 text-sm font-semibold text-[#2563EB] hover:underline"
              >
                Search all 22,028 catalog products →
              </Link>
            </div>
          </div>

          {/* Right Window Snapshot */}
          <div className="lg:col-span-7 order-1 lg:order-2">
            <div className="rounded-xl overflow-hidden border border-slate-300/80 shadow-[0_16px_40px_rgba(0,0,0,0.08)] bg-white">
              {/* Window Bar with Red, White, Green Controls */}
              <div className="h-10 bg-slate-100/90 border-b border-slate-200 px-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#EF4444] border border-red-500 inline-block"></span>
                  <span className="w-3 h-3 rounded-full bg-[#FFFFFF] border border-slate-300 inline-block"></span>
                  <span className="w-3 h-3 rounded-full bg-[#10B981] border border-emerald-500 inline-block"></span>
                </div>
                <div className="text-xs font-medium text-slate-500 font-mono flex items-center gap-1.5">
                  <Database size={12} className="text-blue-600" />
                  haki-vector-catalog-22k.index [Active: 22,028 SKUs]
                </div>
                <div className="w-10"></div>
              </div>

              {/* Realistic App Content */}
              <div className="p-6 bg-slate-50/50 space-y-4">
                <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-slate-200 text-xs">
                  <Search size={14} className="text-slate-400" />
                  <span className="font-mono text-slate-900 font-medium">3C 2.5 mm² XLPE Armoured Cu</span>
                  <span className="ml-auto text-[11px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                    Query Latency: 42ms
                  </span>
                </div>

                <div className="space-y-2.5">
                  <div className="bg-white p-3.5 rounded-lg border border-slate-200 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-xs">Polycab 3C x 2.5 sq mm Armoured XLPE Cable</span>
                        <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded">
                          99.4% Match
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">IS 7098 Pt 1 • 1100V • Electrolytic Copper</p>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-slate-900 text-xs">₹ 148.50 / m</div>
                      <span className="text-[10px] font-semibold text-emerald-600">+18.2% margin</span>
                    </div>
                  </div>

                  <div className="bg-white p-3.5 rounded-lg border border-slate-200 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-xs">Havells 3 Core 2.5 mm² Heavy Duty Armoured</span>
                        <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 text-[10px] font-bold rounded">
                          97.8% Match
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">IS 1554 Pt 1 • 1100V • Copper Conductor</p>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-slate-900 text-xs">₹ 152.00 / m</div>
                      <span className="text-[10px] font-semibold text-emerald-600">+16.5% margin</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs pt-1 text-slate-500">
                  <span>Cross-standard equivalence verified against BIS standard matrices</span>
                  <span className="font-bold text-slate-700">Top 3 Candidates Selected</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* ── Snapshot 3: Left Aligned (Pricing Engine & Margin Optimizer) ── */}
        <motion.div
          initial={{ opacity: 0.2, y: 60, filter: 'blur(4px)' }}
          whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          viewport={{ once: false, amount: 0.2, margin: '0px 0px -80px 0px' }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center"
        >
          {/* Left Window Snapshot */}
          <div className="lg:col-span-7">
            <div className="rounded-xl overflow-hidden border border-slate-300/80 shadow-[0_16px_40px_rgba(0,0,0,0.08)] bg-white">
              {/* Window Bar with Red, White, Green Controls */}
              <div className="h-10 bg-slate-100/90 border-b border-slate-200 px-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#EF4444] border border-red-500 inline-block"></span>
                  <span className="w-3 h-3 rounded-full bg-[#FFFFFF] border border-slate-300 inline-block"></span>
                  <span className="w-3 h-3 rounded-full bg-[#10B981] border border-emerald-500 inline-block"></span>
                </div>
                <div className="text-xs font-medium text-slate-500 font-mono flex items-center gap-1.5">
                  <TrendingUp size={12} className="text-emerald-600" />
                  haki-pricing-margin-engine.live [Commodity Index Linked]
                </div>
                <div className="w-10"></div>
              </div>

              {/* Realistic App Content */}
              <div className="p-6 bg-slate-50/50 space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-white p-3 rounded-lg border border-slate-200">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">MCX Copper Spot</span>
                    <span className="font-bold text-slate-900 text-sm">₹ 784.50 / kg</span>
                    <span className="text-[10px] text-emerald-600 font-semibold block">+0.8% today</span>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-slate-200">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">MCX Aluminium</span>
                    <span className="font-bold text-slate-900 text-sm">₹ 212.80 / kg</span>
                    <span className="text-[10px] text-slate-500 font-semibold block">-0.2% today</span>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                    <span className="text-[10px] uppercase font-bold text-blue-700 block">Target Floor Margin</span>
                    <span className="font-bold text-blue-900 text-sm">18.5% Protected</span>
                    <span className="text-[10px] text-blue-600 font-semibold block">Risk Controlled</span>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-600 font-medium">Estimated Tender Cost Basis</span>
                    <span className="font-mono font-bold text-slate-900">₹ 42,85,600</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-600 font-medium">Recommended Bid Rate (Competitive L1)</span>
                    <span className="font-mono font-bold text-[#2563EB]">₹ 51,20,000</span>
                  </div>
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
                    <span className="text-slate-900 font-bold">Projected Net Commercial Margin</span>
                    <span className="font-mono font-extrabold text-emerald-600 text-sm">₹ 8,34,400 (19.47%)</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="text-slate-500">Automated volume discounting curves applied</span>
                  <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded">
                    Optimal Margin Score: 96/100
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Text Description */}
          <div className="lg:col-span-5 space-y-4">
            <span className="text-xs font-bold text-[#2563EB] tracking-widest uppercase font-mono">
              03 • PRICING & MARGIN INTELLIGENCE
            </span>
            <h3 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              Commodity Cost & Margin Optimization Engine
            </h3>
            <p className="text-slate-600 text-sm md:text-base leading-relaxed">
              Price bids with complete confidence. HAKI dynamically tracks copper and aluminium indices against manufacturer master price lists, automatically recommending winning L1 bid numbers while enforcing your mandatory margin floors.
            </p>
            <div className="pt-2">
              <Link
                to="/bids"
                className="inline-flex items-center gap-2 text-sm font-semibold text-[#2563EB] hover:underline"
              >
                Open bid margin builder →
              </Link>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── Interactive Live Spec Matcher Sandbox ── */}
      <section id="matcher" className="py-20 px-6 max-w-7xl mx-auto border-t border-black/[0.06]">
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
              to={isAuthenticated ? (user?.role === 'admin' || user?.role === 'manager' ? '/rfps/upload' : '/user/rfp-analyzer') : '/login?redirect=/user/rfp-analyzer'}
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
            <HakiLogo size="sm" asLink to="/" />
            <span className="text-slate-400 hidden sm:inline">— Enterprise RFP & Procurement Platform</span>
          </div>

          <div className="flex items-center gap-6">
            <a href="#pipeline" className="hover:text-slate-900 transition-colors">
              RFP Pipeline
            </a>
            <a href="#snapshots" className="hover:text-slate-900 transition-colors">
              Modules
            </a>
            <Link to="/vendors" className="hover:text-slate-900 transition-colors">
              Vendors
            </Link>
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
