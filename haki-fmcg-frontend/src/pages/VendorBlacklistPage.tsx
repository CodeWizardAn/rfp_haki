import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Ban, AlertTriangle, CheckCircle2, Plus, Search, Clock, Shield } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface BlacklistEntry { id: number; vendor: string; reason: string; addedDate: string; addedBy: string; status: 'active' | 'under-review' | 'removed'; severity: 'critical' | 'moderate' | 'low'; notes: string; }

const entries: BlacklistEntry[] = [
  { id: 1, vendor: 'CheapWire Corp', reason: 'Substandard material quality — failed BIS testing 3 times', addedDate: '2025-11-15', addedBy: 'Quality Team', status: 'active', severity: 'critical', notes: 'Copper purity below 99.9% in 3 consecutive batches' },
  { id: 2, vendor: 'QuickCable Ltd', reason: 'Fraudulent BIS certificate submitted', addedDate: '2025-09-20', addedBy: 'Compliance Dept', status: 'active', severity: 'critical', notes: 'Certificate number not found in BIS registry' },
  { id: 3, vendor: 'MetalLinks Inc', reason: 'Persistent delivery delays — 5 orders >30 days late', addedDate: '2025-12-01', addedBy: 'Procurement', status: 'under-review', severity: 'moderate', notes: 'Vendor claims supply chain issues resolved' },
  { id: 4, vendor: 'CablePro Mfg', reason: 'Price manipulation during bid process', addedDate: '2024-06-10', addedBy: 'Audit Team', status: 'removed', severity: 'moderate', notes: 'Removed after corrective action and monitoring period' },
];

const sevColor: Record<string, string> = { critical: 'coral', moderate: 'amber', low: 'teal' };
const statusColor: Record<string, string> = { active: 'coral', 'under-review': 'amber', removed: 'emerald' };

export default function VendorBlacklistPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filtered = entries.filter((e) => {
    if (search && !e.vendor.toLowerCase().includes(search.toLowerCase())) return false;
    if (statusFilter !== 'all' && e.status !== statusFilter) return false;
    return true;
  });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Vendor Blacklist Management</h1><p className="text-body text-muted-silver">Manage restricted and suspended vendors</p></div>
        </div>
        <button className="flex items-center gap-2 bg-coral-flame/20 text-coral-flame px-4 py-2 rounded-lg hover:bg-coral-flame/30 text-sm font-medium"><Plus size={14} />Add to Blacklist</button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { l: 'Active Blocks', v: entries.filter((e) => e.status === 'active').length, icon: Ban, c: 'text-coral-flame' },
          { l: 'Under Review', v: entries.filter((e) => e.status === 'under-review').length, icon: AlertTriangle, c: 'text-amber-glow' },
          { l: 'Removed', v: entries.filter((e) => e.status === 'removed').length, icon: CheckCircle2, c: 'text-neon-emerald' },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-4 text-center">
            <s.icon size={18} className={`${s.c} mx-auto mb-2`} />
            <span className={`text-2xl font-bold ${s.c}`}>{s.v}</span>
            <span className="text-xs text-muted-silver block mt-1">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search vendor..." className="w-full bg-deep-navy/50 border border-steel-slate/20 rounded-lg pl-9 pr-3 py-2 text-sm text-ghost-white placeholder:text-muted-silver/50 focus:outline-none focus:ring-1 focus:ring-electric-cyan/40" />
        </div>
        <div className="flex gap-1">
          {['all', 'active', 'under-review', 'removed'].map((s) => (
            <button key={s} onClick={() => setStatusFilter(s)} className={`px-3 py-2 rounded-lg text-xs capitalize ${statusFilter === s ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'}`}>{s.replace('-', ' ')}</button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {filtered.map((entry) => (
          <Card key={entry.id} variant="glass" className="p-5">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <Ban size={18} className="text-coral-flame" />
                <div>
                  <h3 className="text-sm font-bold text-ghost-white">{entry.vendor}</h3>
                  <p className="text-xs text-muted-silver">{entry.reason}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Badge variant="soft" color={sevColor[entry.severity] as 'coral' | 'amber' | 'teal'} size="sm">{entry.severity}</Badge>
                <Badge variant="soft" color={statusColor[entry.status] as 'coral' | 'amber' | 'emerald'} size="sm">{entry.status}</Badge>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 text-xs mt-3 bg-deep-navy/30 rounded-lg p-3">
              <div><span className="text-muted-silver block"><Calendar size={9} className="inline mr-1" />Added</span><span className="text-ghost-white">{entry.addedDate}</span></div>
              <div><span className="text-muted-silver block"><Shield size={9} className="inline mr-1" />Added By</span><span className="text-ghost-white">{entry.addedBy}</span></div>
              <div><span className="text-muted-silver block">Notes</span><span className="text-ghost-white">{entry.notes}</span></div>
            </div>
            <div className="flex gap-3 mt-3">
              {entry.status === 'active' && <button className="text-xs text-amber-glow hover:underline">Request Review</button>}
              {entry.status === 'under-review' && <button className="text-xs text-neon-emerald hover:underline">Approve Removal</button>}
              <button className="text-xs text-electric-cyan hover:underline">View History</button>
            </div>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}

function Calendar(props: { size: number; className?: string }) {
  return <Clock {...props} />;
}
