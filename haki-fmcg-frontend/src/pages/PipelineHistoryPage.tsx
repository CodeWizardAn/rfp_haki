import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Clock, CheckCircle2, XCircle, AlertTriangle, Search, Download, Filter } from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

const runs = [
  { id: 'PL-2026-001', rfp: 'RFP-2026-0001', started: 'Feb 6, 2026 14:32', duration: '3m 28s', status: 'success' as const, stages: '8/8', errors: 0 },
  { id: 'PL-2026-002', rfp: 'RFP-2026-0002', started: 'Feb 6, 2026 11:15', duration: '4m 12s', status: 'success' as const, stages: '8/8', errors: 0 },
  { id: 'PL-2026-003', rfp: 'RFP-2026-0003', started: 'Feb 5, 2026 16:42', duration: '2m 01s', status: 'failed' as const, stages: '5/8', errors: 2 },
  { id: 'PL-2026-004', rfp: 'RFP-2026-0004', started: 'Feb 5, 2026 09:55', duration: '3m 57s', status: 'success' as const, stages: '8/8', errors: 0 },
  { id: 'PL-2026-005', rfp: 'RFP-2026-0005', started: 'Feb 4, 2026 14:10', duration: '1m 42s', status: 'warning' as const, stages: '7/8', errors: 1 },
  { id: 'PL-2026-006', rfp: 'RFP-2026-0006', started: 'Feb 4, 2026 10:20', duration: '5m 15s', status: 'success' as const, stages: '8/8', errors: 0 },
  { id: 'PL-2026-007', rfp: 'RFP-2026-0007', started: 'Feb 3, 2026 15:30', duration: '2m 34s', status: 'success' as const, stages: '8/8', errors: 0 },
  { id: 'PL-2026-008', rfp: 'RFP-2026-0008', started: 'Feb 3, 2026 08:45', duration: '6m 02s', status: 'failed' as const, stages: '3/8', errors: 3 },
];

const statusCfg = { success: { color: 'emerald' as const, icon: <CheckCircle2 size={13} className="text-neon-emerald" /> }, failed: { color: 'coral' as const, icon: <XCircle size={13} className="text-coral-flame" /> }, warning: { color: 'amber' as const, icon: <AlertTriangle size={13} className="text-amber-glow" /> } };

export default function PipelineHistoryPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [compareA, setCompareA] = useState<string | null>(null);
  const [compareB, setCompareB] = useState<string | null>(null);

  const filtered = runs.filter((r) => (statusFilter === 'all' || r.status === statusFilter) && (r.id.toLowerCase().includes(search.toLowerCase()) || r.rfp.toLowerCase().includes(search.toLowerCase())));

  const toggleCompare = (id: string) => {
    if (compareA === id) setCompareA(null);
    else if (compareB === id) setCompareB(null);
    else if (!compareA) setCompareA(id);
    else if (!compareB) setCompareB(id);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/pipeline" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div className="flex-1">
          <h1 className="text-h1 text-ghost-white">Pipeline History</h1>
          <p className="text-body text-muted-silver">{runs.length} pipeline runs</p>
        </div>
        <Button variant="secondary" size="sm" leftIcon={<Download size={14} />}>Export</Button>
      </div>

      <div className="flex flex-col md:flex-row gap-3">
        <div className="relative flex-1"><Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search runs..." className="glass-input w-full rounded-lg pl-9 pr-3 py-2 text-sm text-ghost-white" /></div>
        <div className="flex gap-1.5">
          {['all', 'success', 'failed', 'warning'].map((s) => (
            <button key={s} onClick={() => setStatusFilter(s)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${statusFilter === s ? 'bg-electric-cyan/10 text-electric-cyan border border-electric-cyan/30' : 'text-muted-silver border border-steel-slate/15 hover:border-steel-slate/30'}`}>{s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}</button>
          ))}
        </div>
      </div>

      {(compareA || compareB) && (
        <Card variant="glass" className="p-3 flex items-center gap-3 text-xs">
          <Filter size={13} className="text-electric-cyan" />
          <span className="text-muted-silver">Comparing:</span>
          {compareA && <Badge variant="soft" color="cyan" size="sm">{compareA}</Badge>}
          {compareB && <Badge variant="soft" color="violet" size="sm">{compareB}</Badge>}
          {compareA && compareB && <Link to={`/pipeline/compare?a=${compareA}&b=${compareB}`}><Button size="sm">Compare</Button></Link>}
          <button onClick={() => { setCompareA(null); setCompareB(null); }} className="text-muted-silver hover:text-ghost-white ml-auto">Clear</button>
        </Card>
      )}

      <Card variant="glass" className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-steel-slate/20">
            <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase w-10" />
            <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase">Run ID</th>
            <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase">RFP</th>
            <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase">Started</th>
            <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Duration</th>
            <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Stages</th>
            <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Status</th>
            <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Errors</th>
          </tr></thead>
          <tbody>
            {filtered.map((r, idx) => {
              const cfg = statusCfg[r.status];
              const selected = r.id === compareA || r.id === compareB;
              return (
                <motion.tr key={r.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: idx * 0.03 }} className={`border-b border-steel-slate/10 hover:bg-steel-slate/10 transition-colors ${selected ? 'bg-electric-cyan/5' : ''}`}>
                  <td className="py-3 px-4"><input type="checkbox" checked={selected} onChange={() => toggleCompare(r.id)} className="accent-electric-cyan" /></td>
                  <td className="py-3 px-4"><Link to={`/pipeline/${r.id}`} className="font-mono text-electric-cyan hover:underline">{r.id}</Link></td>
                  <td className="py-3 px-4 text-ghost-white">{r.rfp}</td>
                  <td className="py-3 px-4 text-muted-silver flex items-center gap-1"><Clock size={11} />{r.started}</td>
                  <td className="py-3 px-4 text-center font-mono text-ghost-white">{r.duration}</td>
                  <td className="py-3 px-4 text-center text-muted-silver">{r.stages}</td>
                  <td className="py-3 px-4 text-center"><Badge variant="soft" color={cfg.color} size="sm"><span className="flex items-center gap-1">{cfg.icon}{r.status}</span></Badge></td>
                  <td className="py-3 px-4 text-center"><span className={r.errors > 0 ? 'text-coral-flame font-semibold' : 'text-muted-silver'}>{r.errors}</span></td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </motion.div>
  );
}
