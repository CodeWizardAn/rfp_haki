import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Clock, User } from 'lucide-react';
import { useState } from 'react';
import { Card, Badge } from '@/components/ui';

interface AuditEntry { id: number; vendor: string; action: string; user: string; timestamp: string; details: string; category: 'profile' | 'compliance' | 'pricing' | 'communication' | 'system'; }

const auditLog: AuditEntry[] = [
  { id: 1, vendor: 'Havells India', action: 'Profile Updated', user: 'Admin', timestamp: '2026-02-06 14:30', details: 'Payment terms changed from Net-30 to Net-45', category: 'profile' },
  { id: 2, vendor: 'Polycab', action: 'Certificate Uploaded', user: 'Vendor Rep', timestamp: '2026-02-06 12:15', details: 'BIS ISI Mark certificate uploaded for IS 7098', category: 'compliance' },
  { id: 3, vendor: 'KEI Industries', action: 'Price Revision', user: 'Procurement Mgr', timestamp: '2026-02-05 16:40', details: 'Power cable prices revised — avg 5% increase', category: 'pricing' },
  { id: 4, vendor: 'Finolex Cables', action: 'Status Changed', user: 'System', timestamp: '2026-02-05 09:00', details: 'Status changed from Active to Suspended — BIS cert expired', category: 'system' },
  { id: 5, vendor: 'Havells India', action: 'Communication Sent', user: 'Sales Exec', timestamp: '2026-02-04 11:20', details: 'RFQ sent for EHV cable requirements', category: 'communication' },
  { id: 6, vendor: 'RR Kabel', action: 'Vendor Registered', user: 'Admin', timestamp: '2026-02-03 10:00', details: 'New vendor onboarded with provisional status', category: 'profile' },
  { id: 7, vendor: 'Polycab', action: 'Rating Updated', user: 'Quality Team', timestamp: '2026-02-02 15:30', details: 'Vendor rating updated from 4.2 to 4.5 after audit', category: 'system' },
];

const catColor: Record<string, 'cyan' | 'emerald' | 'amber' | 'violet' | 'teal'> = {
  profile: 'cyan', compliance: 'emerald', pricing: 'amber', communication: 'violet', system: 'teal',
};

export default function VendorAuditTrailPage() {
  const [filter, setFilter] = useState<string>('all');
  const filtered = filter === 'all' ? auditLog : auditLog.filter((a) => a.category === filter);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Vendor Audit Trail</h1><p className="text-body text-muted-silver">Complete history of vendor-related changes</p></div>
      </div>

      <div className="flex gap-2">
        {['all', 'profile', 'compliance', 'pricing', 'communication', 'system'].map((f) => (
          <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs capitalize ${filter === f ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30' : 'text-muted-silver border border-transparent hover:text-ghost-white'}`}>{f}</button>
        ))}
      </div>

      <Card variant="glass" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-steel-slate/20">
                {['Timestamp', 'Vendor', 'Action', 'Category', 'User', 'Details'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-muted-silver font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry) => (
                <motion.tr key={entry.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="border-b border-steel-slate/10 hover:bg-steel-slate/5">
                  <td className="px-4 py-3 text-muted-silver font-mono whitespace-nowrap"><Clock size={10} className="inline mr-1" />{entry.timestamp}</td>
                  <td className="px-4 py-3 text-ghost-white font-semibold">{entry.vendor}</td>
                  <td className="px-4 py-3 text-ghost-white">{entry.action}</td>
                  <td className="px-4 py-3"><Badge variant="soft" color={catColor[entry.category] ?? 'cyan'} size="sm">{entry.category}</Badge></td>
                  <td className="px-4 py-3 text-muted-silver"><User size={10} className="inline mr-1" />{entry.user}</td>
                  <td className="px-4 py-3 text-muted-silver max-w-xs truncate">{entry.details}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
