import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Search, Hash, BookOpen, Tag } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface Term { id: number; term: string; category: string; definition: string; frequency: number; lastSeen: string; aliases: string[]; }

const terms: Term[] = [
  { id: 1, term: 'XLPE', category: 'Material', definition: 'Cross-linked Polyethylene — thermoset insulation material for HT/EHV cables', frequency: 847, lastSeen: 'RFP-2026-0044', aliases: ['Cross-linked PE', 'PEX'] },
  { id: 2, term: 'IS 7098', category: 'Standard', definition: 'BIS standard for XLPE insulated PVC sheathed cables rated 1.1kV to 33kV', frequency: 623, lastSeen: 'RFP-2026-0044', aliases: ['IS7098', 'BIS 7098'] },
  { id: 3, term: 'EMD', category: 'Commercial', definition: 'Earnest Money Deposit — security deposit required with bid submission', frequency: 412, lastSeen: 'RFP-2026-0043', aliases: ['Bid Security', 'Bid Bond'] },
  { id: 4, term: 'FR-LSH', category: 'Material', definition: 'Fire Retardant Low Smoke Halogen-free — cable sheath material for fire safety', frequency: 356, lastSeen: 'RFP-2026-0042', aliases: ['FRLS', 'FR-LSZH', 'LSHF'] },
  { id: 5, term: 'BOQ', category: 'Commercial', definition: 'Bill of Quantities — detailed list of materials and services with quantities', frequency: 289, lastSeen: 'RFP-2026-0044', aliases: ['BoQ', 'Bill of Qty'] },
  { id: 6, term: 'Type Test', category: 'Testing', definition: 'Certificate proving cable design meets standard requirements (one-time per design)', frequency: 234, lastSeen: 'RFP-2026-0041', aliases: ['Design Test', 'TT Certificate'] },
  { id: 7, term: 'FAT', category: 'Testing', definition: 'Factory Acceptance Test — testing at manufacturer premises before dispatch', frequency: 198, lastSeen: 'RFP-2026-0040', aliases: ['Factory Test', 'Works Testing'] },
  { id: 8, term: 'DLP', category: 'Commercial', definition: 'Defect Liability Period — warranty period post-commissioning', frequency: 176, lastSeen: 'RFP-2026-0039', aliases: ['Warranty Period', 'Guarantee Period'] },
];

const categories = ['All', 'Material', 'Standard', 'Commercial', 'Testing'];
const catColor: Record<string, 'cyan' | 'emerald' | 'amber' | 'violet' | 'teal'> = { Material: 'cyan', Standard: 'emerald', Commercial: 'amber', Testing: 'violet' };

export default function RFPTermsDatabasePage() {
  const [search, setSearch] = useState('');
  const [cat, setCat] = useState('All');

  const filtered = terms.filter((t) => {
    if (search && !t.term.toLowerCase().includes(search.toLowerCase()) && !t.definition.toLowerCase().includes(search.toLowerCase())) return false;
    if (cat !== 'All' && t.category !== cat) return false;
    return true;
  });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/rfps" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">RFP Terms Database</h1><p className="text-body text-muted-silver">{terms.length} terms indexed from {new Set(terms.map((t) => t.lastSeen)).size} RFPs</p></div>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search terms or definitions..." className="w-full bg-deep-navy/50 border border-steel-slate/20 rounded-lg pl-9 pr-3 py-2 text-sm text-ghost-white placeholder:text-muted-silver/50 focus:outline-none focus:ring-1 focus:ring-electric-cyan/40" />
        </div>
        <div className="flex gap-1">
          {categories.map((c) => (
            <button key={c} onClick={() => setCat(c)} className={`px-3 py-2 rounded-lg text-xs ${cat === c ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30' : 'text-muted-silver border border-transparent hover:text-ghost-white'}`}>{c}</button>
          ))}
        </div>
      </div>

      <div className="text-xs text-muted-silver">{filtered.length} terms found</div>

      <div className="space-y-2">
        {filtered.map((t, i) => (
          <motion.div key={t.id} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.02 }}>
            <Card variant="glass" className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <BookOpen size={14} className="text-electric-cyan" />
                  <h3 className="text-sm font-bold text-ghost-white">{t.term}</h3>
                  <Badge variant="soft" color={catColor[t.category] ?? 'cyan'} size="sm">{t.category}</Badge>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-muted-silver">
                  <span><Hash size={9} className="inline" />{t.frequency} uses</span>
                  <span>Last: {t.lastSeen}</span>
                </div>
              </div>
              <p className="text-xs text-muted-silver mb-2">{t.definition}</p>
              <div className="flex gap-1">
                {t.aliases.map((a) => <Badge key={a} variant="outline" color="silver" size="sm"><Tag size={8} className="inline mr-0.5" />{a}</Badge>)}
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
