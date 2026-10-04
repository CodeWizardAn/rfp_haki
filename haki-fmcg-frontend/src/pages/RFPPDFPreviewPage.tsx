import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, ZoomIn, ZoomOut, Download, ChevronLeft, ChevronRight, Search, Maximize2 } from 'lucide-react';
import { Card } from '@/components/ui';

export default function RFPPDFPreviewPage() {
  const [zoom, setZoom] = useState(100);
  const [page, setPage] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const totalPages = 12;

  const handleDownload = () => {
    toast.success('Downloading RFP-2026-0044 document...');
  };

  const handleToggleFullscreen = () => {
    setIsFullscreen((prev) => !prev);
    toast.success(isFullscreen ? 'Exited fullscreen preview' : 'Entered fullscreen preview');
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Link to="/rfps" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">RFP Document Preview</h1><p className="text-body text-muted-silver">RFP-2026-0044 — Power Cables Supply Tender</p></div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownload}
            title="Download PDF"
            className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver hover:text-ghost-white cursor-pointer transition-colors"
          >
            <Download size={16} />
          </button>
          <button
            onClick={handleToggleFullscreen}
            title="Toggle Fullscreen"
            className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver hover:text-ghost-white cursor-pointer transition-colors"
          >
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 mb-3">
        <div className="flex items-center gap-1 bg-deep-navy/50 border border-steel-slate/20 rounded-lg px-2">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="p-1 text-muted-silver hover:text-ghost-white disabled:opacity-30"><ChevronLeft size={14} /></button>
          <span className="text-xs text-ghost-white px-2">Page {page} of {totalPages}</span>
          <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} className="p-1 text-muted-silver hover:text-ghost-white disabled:opacity-30"><ChevronRight size={14} /></button>
        </div>
        <div className="flex items-center gap-1 bg-deep-navy/50 border border-steel-slate/20 rounded-lg px-2">
          <button onClick={() => setZoom(Math.max(50, zoom - 10))} className="p-1 text-muted-silver hover:text-ghost-white"><ZoomOut size={14} /></button>
          <span className="text-xs text-ghost-white px-2">{zoom}%</span>
          <button onClick={() => setZoom(Math.min(200, zoom + 10))} className="p-1 text-muted-silver hover:text-ghost-white"><ZoomIn size={14} /></button>
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input placeholder="Search in document..." className="w-full bg-deep-navy/50 border border-steel-slate/20 rounded-lg pl-9 pr-3 py-1.5 text-xs text-ghost-white placeholder:text-muted-silver/50 focus:outline-none focus:ring-1 focus:ring-electric-cyan/40" />
        </div>
      </div>

      <Card variant="glass" className="flex-1 overflow-auto">
        <div className="p-8 min-h-full" style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }}>
          <div className="max-w-2xl mx-auto bg-white/5 backdrop-blur-sm rounded-lg p-8 border border-steel-slate/20 space-y-6">
            <div className="text-center border-b border-steel-slate/20 pb-6">
              <h2 className="text-xl font-bold text-ghost-white">TENDER DOCUMENT</h2>
              <p className="text-sm text-electric-cyan mt-2">RFP/ELEC/2026-0044/PWR-CBL</p>
              <p className="text-xs text-muted-silver mt-1">Supply of Power Cables for 33kV Sub-Station Expansion</p>
            </div>
            <div className="space-y-4">
              <section>
                <h3 className="text-sm font-bold text-ghost-white mb-2">1. SCOPE OF WORK</h3>
                <p className="text-xs text-muted-silver leading-relaxed">Supply, testing, and delivery of XLPE insulated power cables conforming to IS 7098 (Part 2) for 33kV rated voltage. The scope includes 240mm² and 400mm² cross-section cables with copper conductor, suitable for underground installation with steel wire armour.</p>
              </section>
              <section>
                <h3 className="text-sm font-bold text-ghost-white mb-2">2. TECHNICAL SPECIFICATIONS</h3>
                <div className="text-xs text-muted-silver space-y-1">
                  <p>• Rated Voltage: 33kV (Um = 36kV)</p>
                  <p>• Conductor: Stranded Copper, Class 2 as per IS 8130</p>
                  <p>• Insulation: XLPE (Cross-linked Polyethylene)</p>
                  <p>• Inner Sheath: PVC (ST2 type)</p>
                  <p>• Armour: Galvanized Steel Wire</p>
                  <p>• Outer Sheath: PVC (ST2 type), Black</p>
                  <p>• Temperature Rating: 90°C continuous, 250°C short-circuit</p>
                </div>
              </section>
              <section>
                <h3 className="text-sm font-bold text-ghost-white mb-2">3. QUANTITY SCHEDULE</h3>
                <table className="w-full text-xs border border-steel-slate/20 rounded">
                  <thead><tr className="bg-steel-slate/10"><th className="p-2 text-left text-muted-silver">Item</th><th className="p-2 text-left text-muted-silver">Size</th><th className="p-2 text-right text-muted-silver">Qty (m)</th></tr></thead>
                  <tbody>
                    <tr className="border-t border-steel-slate/10"><td className="p-2 text-ghost-white">XLPE Cable</td><td className="p-2 text-ghost-white">3C × 240mm²</td><td className="p-2 text-right text-ghost-white">5,000</td></tr>
                    <tr className="border-t border-steel-slate/10"><td className="p-2 text-ghost-white">XLPE Cable</td><td className="p-2 text-ghost-white">3C × 400mm²</td><td className="p-2 text-right text-ghost-white">3,000</td></tr>
                    <tr className="border-t border-steel-slate/10"><td className="p-2 text-ghost-white">FR Cable</td><td className="p-2 text-ghost-white">4C × 25mm²</td><td className="p-2 text-right text-ghost-white">2,000</td></tr>
                  </tbody>
                </table>
              </section>
            </div>
            <div className="text-center text-[10px] text-muted-silver/40 mt-8">Page {page} of {totalPages}</div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
