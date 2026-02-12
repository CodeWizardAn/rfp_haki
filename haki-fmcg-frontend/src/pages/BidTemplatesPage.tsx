import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText, Copy, Plus, Pencil, Trash2, Play, Clock, FileCheck } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface Template { id: string; name: string; description: string; sections: string[]; lastUsed: string; uses: number; category: string; }

const templates: Template[] = [
  { id: 'tmpl-1', name: 'Standard Power Cable Bid', description: 'Complete bid template for power cable tenders with all standard sections', sections: ['Executive Summary', 'Technical Specifications', 'Product Catalogue', 'Pricing Schedule', 'Delivery Timeline', 'Terms & Conditions', 'Compliance Certificates'], lastUsed: '2d ago', uses: 28, category: 'Power Cables' },
  { id: 'tmpl-2', name: 'Quick Quotation', description: 'Minimal template for quick price quotes', sections: ['Cover Letter', 'Pricing Table', 'Validity & Terms'], lastUsed: '1d ago', uses: 42, category: 'General' },
  { id: 'tmpl-3', name: 'Government Tender', description: 'Comprehensive template compliant with PSU requirements', sections: ['Executive Summary', 'Company Profile', 'Technical Specifications', 'BIS Compliance', 'Past Performance', 'Pricing BOQ', 'EMD Details', 'Delivery Schedule', 'T&C'], lastUsed: '5d ago', uses: 15, category: 'Government' },
  { id: 'tmpl-4', name: 'Fire Safety Bid', description: 'FR cable focused with fire test certificates', sections: ['Executive Summary', 'FR Cable Specifications', 'Fire Test Reports', 'Pricing', 'Installation Guide', 'Warranty'], lastUsed: '1w ago', uses: 9, category: 'Fire Resistant' },
];

export default function BidTemplatesPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const tpl = templates.find((t) => t.id === selected);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/bids" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Bid Templates</h1><p className="text-body text-muted-silver">Reusable bid document templates</p></div>
        </div>
        <button className="flex items-center gap-2 bg-electric-cyan/20 text-electric-cyan px-4 py-2 rounded-lg hover:bg-electric-cyan/30 text-sm font-medium"><Plus size={14} />New Template</button>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {[
          { l: 'Total Templates', v: templates.length, icon: FileText, c: 'text-electric-cyan' },
          { l: 'Total Uses', v: templates.reduce((a, t) => a + t.uses, 0), icon: Play, c: 'text-neon-emerald' },
          { l: 'Most Popular', v: 'Quick Quote', icon: FileCheck, c: 'text-amber-glow' },
          { l: 'Last Created', v: '3 days ago', icon: Clock, c: 'text-muted-silver' },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-3">
            <s.icon size={14} className={`${s.c} mb-1`} />
            <span className="text-sm font-bold text-ghost-white block">{s.v}</span>
            <span className="text-[10px] text-muted-silver">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2">
          {templates.map((t) => (
            <Card key={t.id} variant="glass" className={`p-4 cursor-pointer transition-all ${selected === t.id ? 'ring-1 ring-electric-cyan/40' : 'hover:bg-steel-slate/5'}`} onClick={() => setSelected(t.id)}>
              <div className="flex justify-between items-start mb-1">
                <h3 className="text-sm font-semibold text-ghost-white">{t.name}</h3>
                <Badge variant="soft" color="cyan" size="sm">{t.category}</Badge>
              </div>
              <p className="text-[10px] text-muted-silver mb-2 line-clamp-2">{t.description}</p>
              <div className="flex gap-3 text-[10px] text-muted-silver">
                <span>{t.sections.length} sections</span>
                <span>{t.uses} uses</span>
                <span>{t.lastUsed}</span>
              </div>
            </Card>
          ))}
        </div>

        <div className="lg:col-span-2">
          {tpl ? (
            <Card variant="glass" className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-ghost-white">{tpl.name}</h2>
                <div className="flex gap-2">
                  <button className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver" title="Edit"><Pencil size={14} /></button>
                  <button className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver" title="Duplicate"><Copy size={14} /></button>
                  <button className="p-2 rounded-lg hover:bg-coral-flame/10 text-coral-flame" title="Delete"><Trash2 size={14} /></button>
                </div>
              </div>
              <p className="text-sm text-muted-silver">{tpl.description}</p>
              <Badge variant="soft" color="teal" size="sm">{tpl.category}</Badge>

              <div>
                <h4 className="text-xs font-semibold text-muted-silver mb-2">TEMPLATE SECTIONS</h4>
                <div className="space-y-1">
                  {tpl.sections.map((s, i) => (
                    <div key={s} className="flex items-center gap-3 p-2 rounded-lg bg-deep-navy/40">
                      <span className="w-6 h-6 rounded-full bg-electric-cyan/10 text-electric-cyan text-[10px] flex items-center justify-center font-bold">{i + 1}</span>
                      <span className="text-sm text-ghost-white flex-1">{s}</span>
                      <Pencil size={10} className="text-muted-silver/30 hover:text-muted-silver cursor-pointer" />
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button className="flex items-center gap-2 bg-neon-emerald/20 text-neon-emerald px-4 py-2 rounded-lg hover:bg-neon-emerald/30 text-sm font-medium"><Play size={14} />Use Template</button>
                <button className="flex items-center gap-2 bg-steel-slate/20 text-ghost-white px-4 py-2 rounded-lg hover:bg-steel-slate/30 text-sm font-medium"><Copy size={14} />Duplicate</button>
              </div>
            </Card>
          ) : (
            <Card variant="glass" className="p-12 flex flex-col items-center justify-center text-center">
              <FileText size={32} className="text-muted-silver/30 mb-3" />
              <p className="text-sm text-muted-silver">Select a template to view details</p>
            </Card>
          )}
        </div>
      </div>
    </motion.div>
  );
}
