import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ScrollText,
  Search,
  Download,
  ChevronDown,
  ChevronUp,
  Shield,
  FileText,
  Edit3,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Upload,
  Trash2,
  Eye,
  User,
  Clock,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

type AuditAction = 'created' | 'updated' | 'deleted' | 'approved' | 'rejected' | 'exported' | 'verified' | 'uploaded';

interface AuditEntry {
  id: string;
  action: AuditAction;
  entity: string;
  entityId: string;
  user: string;
  role: string;
  timestamp: string;
  detail: string;
  beforeData?: string;
  afterData?: string;
  ip?: string;
  status: 'success' | 'failure';
}

const actionConfig: Record<AuditAction, { icon: React.ReactNode; color: string; bg: string; badge: string }> = {
  created:  { icon: <FileText size={14} />, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10', badge: 'emerald' },
  updated:  { icon: <Edit3 size={14} />, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10', badge: 'cyan' },
  deleted:  { icon: <Trash2 size={14} />, color: 'text-coral-flame', bg: 'bg-coral-flame/10', badge: 'coral' },
  approved: { icon: <CheckCircle2 size={14} />, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10', badge: 'emerald' },
  rejected: { icon: <XCircle size={14} />, color: 'text-coral-flame', bg: 'bg-coral-flame/10', badge: 'coral' },
  exported: { icon: <Upload size={14} />, color: 'text-violet-pulse', bg: 'bg-violet-pulse/10', badge: 'violet' },
  verified: { icon: <Shield size={14} />, color: 'text-amber-glow', bg: 'bg-amber-glow/10', badge: 'amber' },
  uploaded: { icon: <Upload size={14} />, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10', badge: 'cyan' },
};

const mockEntries: AuditEntry[] = [
  {
    id: 'AUD-001', action: 'created', entity: 'RFP', entityId: 'RFP-2026-0001',
    user: 'Rajesh Kumar', role: 'Procurement Officer', timestamp: '2026-02-06 14:32:15',
    detail: 'New RFP created from PDF upload — Power Cable Supply Phase 1',
    status: 'success', ip: '192.168.1.45',
  },
  {
    id: 'AUD-002', action: 'updated', entity: 'RFP', entityId: 'RFP-2026-0001',
    user: 'System (Pipeline)', role: 'Automated', timestamp: '2026-02-06 14:35:48',
    detail: 'Status changed: draft → extracting (pipeline pipe-8a3f started)',
    beforeData: '{ "status": "draft" }', afterData: '{ "status": "extracting" }',
    status: 'success',
  },
  {
    id: 'AUD-003', action: 'verified', entity: 'Compliance', entityId: 'CR-001',
    user: 'System (Pipeline)', role: 'Automated', timestamp: '2026-02-06 14:38:22',
    detail: 'Compliance check passed — IS 7098 Part 1 verified for all HT cable products',
    status: 'success',
  },
  {
    id: 'AUD-004', action: 'approved', entity: 'Bid', entityId: 'BID-2026-001',
    user: 'Priya Sharma', role: 'Manager', timestamp: '2026-02-06 14:40:10',
    detail: 'Bid BID-2026-001 approved at Manager level — ₹2.53 Cr for Havells India',
    status: 'success', ip: '192.168.1.22',
  },
  {
    id: 'AUD-005', action: 'rejected', entity: 'Bid', entityId: 'BID-2026-006',
    user: 'Amit Patel', role: 'Director', timestamp: '2026-02-06 14:42:05',
    detail: 'Bid BID-2026-006 rejected — pricing exceeds budget by 18%',
    status: 'success', ip: '192.168.1.10',
  },
  {
    id: 'AUD-006', action: 'exported', entity: 'Analytics', entityId: 'RPT-20260206',
    user: 'Sunita Reddy', role: 'CFO', timestamp: '2026-02-06 14:45:33',
    detail: 'Analytics report exported as PDF — Monthly procurement summary Feb 2026',
    status: 'success', ip: '192.168.1.5',
  },
  {
    id: 'AUD-007', action: 'uploaded', entity: 'RFP', entityId: 'RFP-2026-0009',
    user: 'Rajesh Kumar', role: 'Procurement Officer', timestamp: '2026-02-06 15:10:05',
    detail: 'PDF uploaded — LT Wiring Factory Expansion tender document (2.4MB)',
    status: 'success', ip: '192.168.1.45',
  },
  {
    id: 'AUD-008', action: 'updated', entity: 'Vendor', entityId: 'VND-003',
    user: 'System', role: 'Automated', timestamp: '2026-02-06 15:15:22',
    detail: 'KEI Industries rating recalculated — score changed from 84 to 86',
    beforeData: '{ "score": 84, "rating": 4.2 }', afterData: '{ "score": 86, "rating": 4.3 }',
    status: 'success',
  },
  {
    id: 'AUD-009', action: 'deleted', entity: 'RFP', entityId: 'RFP-2026-0012',
    user: 'Rajesh Kumar', role: 'Procurement Officer', timestamp: '2026-02-06 15:30:00',
    detail: 'Duplicate RFP deleted — duplicate of RFP-2026-0005',
    status: 'success', ip: '192.168.1.45',
  },
  {
    id: 'AUD-010', action: 'verified', entity: 'Compliance', entityId: 'CR-007',
    user: 'System (Pipeline)', role: 'Automated', timestamp: '2026-02-06 15:45:18',
    detail: 'Compliance check FAILED — KEI 11kV cable CPRI type test report expired',
    status: 'failure',
  },
];

const entityTypes = ['All', 'RFP', 'Bid', 'Vendor', 'Compliance', 'Analytics'];
const actionTypes: AuditAction[] = ['created', 'updated', 'deleted', 'approved', 'rejected', 'exported', 'verified', 'uploaded'];

export default function AuditTrailPage() {
  const [expandedEntry, setExpandedEntry] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterEntity, setFilterEntity] = useState('All');
  const [filterAction, setFilterAction] = useState<AuditAction | 'all'>('all');

  const filtered = mockEntries.filter((e) => {
    if (filterEntity !== 'All' && e.entity !== filterEntity) return false;
    if (filterAction !== 'all' && e.action !== filterAction) return false;
    if (searchQuery && !e.detail.toLowerCase().includes(searchQuery.toLowerCase()) && !e.entityId.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const successCount = mockEntries.filter((e) => e.status === 'success').length;
  const failureCount = mockEntries.filter((e) => e.status === 'failure').length;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-violet-pulse/10">
            <ScrollText size={24} className="text-violet-pulse" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Audit Trail</h1>
            <p className="text-body text-muted-silver">Complete system activity log with full traceability</p>
          </div>
        </div>
        <Button variant="secondary" leftIcon={<Download size={14} />}>Export Log</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {([
          { label: 'Total Entries', value: mockEntries.length, color: 'text-electric-cyan' },
          { label: 'Successful', value: successCount, color: 'text-neon-emerald' },
          { label: 'Failed', value: failureCount, color: 'text-coral-flame' },
          { label: 'Users Active', value: 4, color: 'text-violet-pulse' },
        ]).map((stat) => (
          <Card key={stat.label} variant="glass">
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-muted-silver">{stat.label}</p>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search entries, entity IDs…"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50"
          />
        </div>
        <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1 overflow-x-auto">
          {entityTypes.map((et) => (
            <button
              key={et}
              onClick={() => setFilterEntity(et)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
                filterEntity === et ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'
              }`}
            >
              {et}
            </button>
          ))}
        </div>
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value as any)}
          className="px-3 py-2 rounded-xl bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm focus:outline-none"
        >
          <option value="all">All Actions</option>
          {actionTypes.map((a) => (
            <option key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</option>
          ))}
        </select>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical Line */}
        <div className="absolute left-6 top-0 bottom-0 w-px bg-steel-slate/20" />

        <div className="space-y-4">
          {filtered.map((entry, i) => {
            const config = actionConfig[entry.action];
            const isExpanded = expandedEntry === entry.id;

            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="relative pl-14"
              >
                {/* Timeline Dot */}
                <div className={`absolute left-3 top-4 w-6 h-6 rounded-full ${config.bg} flex items-center justify-center z-10`}>
                  <span className={config.color}>{config.icon}</span>
                </div>

                <Card
                  variant="glass"
                  className={`cursor-pointer transition-all ${entry.status === 'failure' ? 'border-coral-flame/20' : ''}`}
                  onClick={() => setExpandedEntry(isExpanded ? null : entry.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="soft" color={config.badge as any} size="sm">{entry.action}</Badge>
                        <Badge variant="outline" color="cyan" size="sm">{entry.entity}</Badge>
                        <span className="text-xs font-mono text-electric-cyan">{entry.entityId}</span>
                        {entry.status === 'failure' && (
                          <Badge variant="soft" color="coral" size="sm">
                            <AlertTriangle size={8} className="mr-1" />Failed
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-ghost-white mt-1">{entry.detail}</p>
                      <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-silver">
                        <span className="flex items-center gap-1"><User size={9} />{entry.user}</span>
                        <span className="flex items-center gap-1"><Shield size={9} />{entry.role}</span>
                        <span className="flex items-center gap-1"><Clock size={9} />{entry.timestamp}</span>
                      </div>
                    </div>
                    <div className="flex-shrink-0 mt-1">
                      {isExpanded ? <ChevronUp size={14} className="text-muted-silver" /> : <ChevronDown size={14} className="text-muted-silver" />}
                    </div>
                  </div>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-4 pt-4 border-t border-steel-slate/20 space-y-3">
                          <div className="grid grid-cols-2 gap-4 text-xs">
                            <div>
                              <span className="text-muted-silver">Audit ID:</span>
                              <span className="ml-2 font-mono text-ghost-white">{entry.id}</span>
                            </div>
                            {entry.ip && (
                              <div>
                                <span className="text-muted-silver">IP Address:</span>
                                <span className="ml-2 font-mono text-ghost-white">{entry.ip}</span>
                              </div>
                            )}
                            <div>
                              <span className="text-muted-silver">Status:</span>
                              <span className={`ml-2 font-semibold ${entry.status === 'success' ? 'text-neon-emerald' : 'text-coral-flame'}`}>
                                {entry.status === 'success' ? '✅ Success' : '❌ Failure'}
                              </span>
                            </div>
                          </div>

                          {(entry.beforeData || entry.afterData) && (
                            <div className="grid grid-cols-2 gap-4">
                              {entry.beforeData && (
                                <div>
                                  <p className="text-[10px] text-muted-silver uppercase tracking-wide mb-1">Before</p>
                                  <pre className="text-xs font-mono text-coral-flame/70 bg-coral-flame/5 p-2 rounded-lg overflow-x-auto">{entry.beforeData}</pre>
                                </div>
                              )}
                              {entry.afterData && (
                                <div>
                                  <p className="text-[10px] text-muted-silver uppercase tracking-wide mb-1">After</p>
                                  <pre className="text-xs font-mono text-neon-emerald/70 bg-neon-emerald/5 p-2 rounded-lg overflow-x-auto">{entry.afterData}</pre>
                                </div>
                              )}
                            </div>
                          )}

                          <div className="flex gap-2">
                            <Button variant="secondary" size="xs" leftIcon={<Eye size={10} />}>View Entity</Button>
                            <Button variant="secondary" size="xs" leftIcon={<Download size={10} />}>Export Entry</Button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-xs text-muted-silver">
        <span>Showing {filtered.length} of {mockEntries.length} entries</span>
        <div className="flex gap-1">
          <button className="px-3 py-1.5 rounded-lg bg-steel-slate/15 text-muted-silver hover:text-ghost-white transition-colors">Prev</button>
          <button className="px-3 py-1.5 rounded-lg bg-electric-cyan/15 text-electric-cyan">1</button>
          <button className="px-3 py-1.5 rounded-lg bg-steel-slate/15 text-muted-silver hover:text-ghost-white transition-colors">2</button>
          <button className="px-3 py-1.5 rounded-lg bg-steel-slate/15 text-muted-silver hover:text-ghost-white transition-colors">Next</button>
        </div>
      </div>
    </motion.div>
  );
}
