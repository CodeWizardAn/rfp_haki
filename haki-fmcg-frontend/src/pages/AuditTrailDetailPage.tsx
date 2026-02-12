import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Clock, User, FileText, Shield, Database, Settings, ChevronRight } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface AuditEvent { id: number; action: string; entity: string; entityId: string; user: string; timestamp: string; details: string; changes?: { field: string; from: string; to: string }[]; }

const events: AuditEvent[] = [
  { id: 1, action: 'Bid Submitted', entity: 'Bid', entityId: 'BID-2026-0044', user: 'Rajesh Kumar', timestamp: '2026-02-06 14:32:01', details: 'Bid submitted for RFP-2026-0044', changes: [{ field: 'Status', from: 'Draft', to: 'Submitted' }, { field: 'Total Value', from: '₹0', to: '₹1,78,73,000' }] },
  { id: 2, action: 'Pipeline Completed', entity: 'Pipeline', entityId: 'WF-2026-044', user: 'System', timestamp: '2026-02-06 14:33:05', details: 'Pipeline workflow completed in 64.2s with 92% match score' },
  { id: 3, action: 'Vendor Rating Updated', entity: 'Vendor', entityId: 'V-HAV-001', user: 'Quality Team', timestamp: '2026-02-06 12:00:00', details: 'Havells India rating updated', changes: [{ field: 'Rating', from: '4.2', to: '4.5' }, { field: 'Tier', from: 'Silver', to: 'Gold' }] },
  { id: 4, action: 'Compliance Check', entity: 'Compliance', entityId: 'CC-2026-088', user: 'System', timestamp: '2026-02-06 10:15:30', details: 'Automated compliance check passed — 7/7 rules satisfied' },
  { id: 5, action: 'RFP Uploaded', entity: 'RFP', entityId: 'RFP-2026-0045', user: 'Priya Sharma', timestamp: '2026-02-05 16:45:00', details: 'New RFP uploaded: Control Cable Supply for Railway Project', changes: [{ field: 'Status', from: 'None', to: 'Pending Analysis' }] },
  { id: 6, action: 'Price Override', entity: 'Pricing', entityId: 'PRICE-2026-112', user: 'VP Sales', timestamp: '2026-02-05 14:20:00', details: 'Price override approved for XLPE-400 — strategic bid', changes: [{ field: 'Margin', from: '15%', to: '8%' }, { field: 'Approval', from: 'Required', to: 'Approved' }] },
  { id: 7, action: 'Agent Restart', entity: 'System', entityId: 'AGENT-TECH', user: 'System', timestamp: '2026-02-05 09:00:00', details: 'Technical Agent auto-restarted after OOM error' },
];

const entityColor: Record<string, 'cyan' | 'emerald' | 'amber' | 'violet' | 'teal' | 'coral'> = { Bid: 'cyan', Pipeline: 'emerald', Vendor: 'amber', Compliance: 'violet', RFP: 'teal', Pricing: 'coral', System: 'teal' };
const entityIcon: Record<string, typeof FileText> = { Bid: FileText, Pipeline: Settings, Vendor: User, Compliance: Shield, RFP: FileText, Pricing: Database, System: Settings };

export default function AuditTrailDetailPage() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/audit" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Audit Trail — Detail View</h1><p className="text-body text-muted-silver">Comprehensive change history across all entities</p></div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {[
          { l: 'Total Events', v: events.length, c: 'text-electric-cyan' },
          { l: 'Users', v: new Set(events.map((e) => e.user)).size, c: 'text-amber-glow' },
          { l: 'Entities', v: new Set(events.map((e) => e.entity)).size, c: 'text-neon-emerald' },
          { l: 'With Changes', v: events.filter((e) => e.changes).length, c: 'text-violet-pulse' },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-3 text-center">
            <span className={`text-xl font-bold ${s.c}`}>{s.v}</span>
            <span className="text-[10px] text-muted-silver block">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="relative">
        <div className="absolute left-[19px] top-0 bottom-0 w-px bg-steel-slate/20" />
        <div className="space-y-4">
          {events.map((evt, i) => {
            const Icon = entityIcon[evt.entity] ?? FileText;
            const color = entityColor[evt.entity] ?? 'cyan';
            return (
              <motion.div key={evt.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }} className="flex gap-4 relative">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 z-10 bg-${color === 'cyan' ? 'electric-cyan' : color === 'emerald' ? 'neon-emerald' : color === 'amber' ? 'amber-glow' : color === 'violet' ? 'violet-pulse' : color === 'coral' ? 'coral-flame' : 'teal-depth'}/10 border-2 border-deep-navy`}>
                  <Icon size={16} className={`text-${color === 'cyan' ? 'electric-cyan' : color === 'emerald' ? 'neon-emerald' : color === 'amber' ? 'amber-glow' : color === 'violet' ? 'violet-pulse' : color === 'coral' ? 'coral-flame' : 'teal-depth'}`} />
                </div>
                <Card variant="glass" className="flex-1 p-4">
                  <div className="flex items-start justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-ghost-white">{evt.action}</h3>
                      <Badge variant="soft" color={color} size="sm">{evt.entity}</Badge>
                      <Badge variant="outline" color="silver" size="sm">{evt.entityId}</Badge>
                    </div>
                    <span className="text-[10px] text-muted-silver font-mono whitespace-nowrap"><Clock size={9} className="inline mr-0.5" />{evt.timestamp}</span>
                  </div>
                  <p className="text-xs text-muted-silver">{evt.details}</p>
                  <div className="text-[10px] text-muted-silver mt-1"><User size={9} className="inline mr-0.5" />{evt.user}</div>
                  {evt.changes && (
                    <div className="mt-2 space-y-1">
                      {evt.changes.map((ch, ci) => (
                        <div key={ci} className="flex items-center gap-2 text-[10px] bg-deep-navy/40 rounded px-2 py-1">
                          <span className="text-muted-silver">{ch.field}:</span>
                          <span className="text-coral-flame line-through">{ch.from}</span>
                          <ChevronRight size={8} className="text-muted-silver" />
                          <span className="text-neon-emerald">{ch.to}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
