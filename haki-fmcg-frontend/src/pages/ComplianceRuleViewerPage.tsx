import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Shield, Book, ChevronRight, ChevronDown, CheckCircle2, AlertTriangle, FileText } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface Rule { id: string; name: string; category: string; description: string; severity: 'mandatory' | 'recommended' | 'optional'; status: 'active' | 'draft'; conditions: string[]; }

const rules: Rule[] = [
  { id: 'CR-001', name: 'BIS Certification Required', category: 'Product Compliance', description: 'All cable products must have valid BIS ISI mark certification for the relevant IS standard', severity: 'mandatory', status: 'active', conditions: ['Product type = Cable', 'Market = India', 'Valid BIS certificate exists'] },
  { id: 'CR-002', name: 'Vendor Minimum Rating', category: 'Vendor Qualification', description: 'Vendors must maintain a minimum rating of 3.5/5 based on historical performance', severity: 'mandatory', status: 'active', conditions: ['Vendor rating ≥ 3.5', 'No active blacklist entries', 'Active vendor status'] },
  { id: 'CR-003', name: 'Price Variance Check', category: 'Pricing', description: 'Bid prices must be within ±15% of the last approved price for the same product', severity: 'recommended', status: 'active', conditions: ['Historical price data exists', 'Variance ≤ 15%', 'Exception approval for > 15%'] },
  { id: 'CR-004', name: 'Document Completeness', category: 'Bid Submission', description: 'All required sections (tech specs, pricing, compliance certs) must be present in bid document', severity: 'mandatory', status: 'active', conditions: ['Technical section present', 'Pricing section present', 'Compliance certificates attached'] },
  { id: 'CR-005', name: 'EMD Compliance', category: 'Commercial', description: 'Earnest Money Deposit must meet minimum 2% of estimated bid value', severity: 'mandatory', status: 'active', conditions: ['EMD amount ≥ 2% of bid value', 'Valid bank guarantee or DD'] },
  { id: 'CR-006', name: 'Environmental Certification', category: 'Sustainability', description: 'Prefer vendors with ISO 14001 environmental management certification', severity: 'optional', status: 'active', conditions: ['ISO 14001 certificate present', 'Valid within 3 years'] },
  { id: 'CR-007', name: 'Fire Safety Standards', category: 'Product Compliance', description: 'FR cables must pass fire propagation test as per IS 10810', severity: 'mandatory', status: 'draft', conditions: ['Product = FR cable', 'IS 10810 type test certificate', 'Test within last 5 years'] },
];

const sevColor: Record<string, 'coral' | 'amber' | 'teal'> = { mandatory: 'coral', recommended: 'amber', optional: 'teal' };

export default function ComplianceRuleViewerPage() {
  const [expanded, setExpanded] = useState<string[]>([]);
  const [catFilter, setCatFilter] = useState('All');
  const cats = ['All', ...new Set(rules.map((r) => r.category))];

  const toggle = (id: string) => setExpanded((p) => p.includes(id) ? p.filter((i) => i !== id) : [...p, id]);
  const filtered = catFilter === 'All' ? rules : rules.filter((r) => r.category === catFilter);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/compliance" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Compliance Rule Viewer</h1><p className="text-body text-muted-silver">{rules.length} rules configured across {new Set(rules.map((r) => r.category)).size} categories</p></div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { l: 'Mandatory', v: rules.filter((r) => r.severity === 'mandatory').length, c: 'text-coral-flame', icon: Shield },
          { l: 'Recommended', v: rules.filter((r) => r.severity === 'recommended').length, c: 'text-amber-glow', icon: AlertTriangle },
          { l: 'Optional', v: rules.filter((r) => r.severity === 'optional').length, c: 'text-teal-depth', icon: Book },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-4 text-center">
            <s.icon size={18} className={`${s.c} mx-auto mb-2`} />
            <span className="text-2xl font-bold text-ghost-white">{s.v}</span>
            <span className="text-xs text-muted-silver block mt-1">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="flex gap-2 flex-wrap">
        {cats.map((c) => (
          <button key={c} onClick={() => setCatFilter(c)} className={`px-3 py-1.5 rounded-lg text-xs ${catFilter === c ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30' : 'text-muted-silver border border-transparent hover:text-ghost-white'}`}>{c}</button>
        ))}
      </div>

      <div className="space-y-2">
        {filtered.map((rule) => {
          const isOpen = expanded.includes(rule.id);
          return (
            <Card key={rule.id} variant="glass" className="overflow-hidden">
              <button onClick={() => toggle(rule.id)} className="w-full flex items-center gap-3 p-4 text-left hover:bg-steel-slate/5 transition-colors">
                <Shield size={14} className="text-electric-cyan flex-shrink-0" />
                <Badge variant="soft" color="cyan" size="sm">{rule.id}</Badge>
                <h3 className="text-sm font-semibold text-ghost-white flex-1">{rule.name}</h3>
                <Badge variant="soft" color={sevColor[rule.severity]} size="sm">{rule.severity}</Badge>
                <Badge variant={rule.status === 'active' ? 'soft' : 'outline'} color={rule.status === 'active' ? 'emerald' : 'silver'} size="sm">{rule.status}</Badge>
                {isOpen ? <ChevronDown size={12} className="text-muted-silver" /> : <ChevronRight size={12} className="text-muted-silver" />}
              </button>
              {isOpen && (
                <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} className="px-4 pb-4 space-y-3 overflow-hidden">
                  <p className="text-xs text-muted-silver">{rule.description}</p>
                  <div className="text-xs text-muted-silver"><FileText size={10} className="inline mr-1" />Category: <span className="text-ghost-white">{rule.category}</span></div>
                  <div>
                    <h4 className="text-[10px] font-semibold text-muted-silver mb-1">CONDITIONS</h4>
                    <div className="space-y-1">
                      {rule.conditions.map((c, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs"><CheckCircle2 size={10} className="text-neon-emerald flex-shrink-0" /><span className="text-ghost-white">{c}</span></div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
