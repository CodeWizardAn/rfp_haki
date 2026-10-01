import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Gavel,
  Plus,
  LayoutGrid,
  List,
  Calendar,
  Clock,
  FileText,
  Download,
  Building2,

  Eye,

} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { BidAnalyticsWidget } from '@/components/bids';
import { formatCompactCurrency } from '@/utils/formatters';
import { useBids } from '@/hooks/useApi';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

type BidStatus = 'draft' | 'submitted' | 'under_review' | 'approved' | 'won' | 'lost';

interface Bid {
  id: string;
  rfpId: string;
  vendor: string;
  amount: number;
  status: BidStatus;
  deadline: string;
  items: number;
  createdAt: string;
  approvalLevel: number;
  maxApproval: number;
  probability: number;
}

const mockBids: Bid[] = [
  { id: 'B-0087', rfpId: 'RFP-2026-0001', vendor: 'Havells India', amount: 5860000, status: 'approved', deadline: '2026-02-15', items: 5, createdAt: '2026-02-05', approvalLevel: 4, maxApproval: 4, probability: 85 },
  { id: 'B-0088', rfpId: 'RFP-2026-0001', vendor: 'Polycab India', amount: 5640000, status: 'submitted', deadline: '2026-02-15', items: 4, createdAt: '2026-02-05', approvalLevel: 1, maxApproval: 4, probability: 72 },
  { id: 'B-0089', rfpId: 'RFP-2026-0002', vendor: 'KEI Industries', amount: 5920000, status: 'under_review', deadline: '2026-02-20', items: 3, createdAt: '2026-02-06', approvalLevel: 2, maxApproval: 4, probability: 60 },
  { id: 'B-0090', rfpId: 'RFP-2026-0003', vendor: 'Finolex Cables', amount: 3200000, status: 'draft', deadline: '2026-02-25', items: 6, createdAt: '2026-02-07', approvalLevel: 0, maxApproval: 4, probability: 45 },
  { id: 'B-0091', rfpId: 'RFP-2026-0003', vendor: 'RR Kabel', amount: 2800000, status: 'draft', deadline: '2026-02-25', items: 4, createdAt: '2026-02-07', approvalLevel: 0, maxApproval: 4, probability: 40 },
  { id: 'B-0085', rfpId: 'RFP-2025-0098', vendor: 'Havells India', amount: 12400000, status: 'won', deadline: '2026-01-20', items: 8, createdAt: '2026-01-10', approvalLevel: 4, maxApproval: 4, probability: 100 },
  { id: 'B-0084', rfpId: 'RFP-2025-0097', vendor: 'Polycab India', amount: 9100000, status: 'lost', deadline: '2026-01-15', items: 6, createdAt: '2026-01-05', approvalLevel: 4, maxApproval: 4, probability: 0 },
];

const columns: { id: BidStatus; label: string; color: string }[] = [
  { id: 'draft', label: 'Draft', color: '#8892B0' },
  { id: 'submitted', label: 'Submitted', color: '#00D4FF' },
  { id: 'under_review', label: 'Under Review', color: '#FFB224' },
  { id: 'approved', label: 'Approved', color: '#00E68A' },
  { id: 'won', label: 'Won', color: '#00E68A' },
  { id: 'lost', label: 'Lost', color: '#FF4757' },
];

const statusBadgeColor = (s: BidStatus): 'cyan' | 'emerald' | 'amber' | 'coral' | 'silver' => {
  const map: Record<BidStatus, 'cyan' | 'emerald' | 'amber' | 'coral' | 'silver'> = { draft: 'silver', submitted: 'cyan', under_review: 'amber', approved: 'emerald', won: 'emerald', lost: 'coral' };
  return map[s] || 'silver';
};

export default function BidsPage() {
  const [viewMode, setViewMode] = useState<'board' | 'list' | 'calendar'>('board');
  const navigate = useNavigate();

  /* ── Backend hooks ── */
  const { data: apiBids } = useBids();

  /* Merge backend bids with mock fallback */
  const allBids: Bid[] = useMemo(() => {
    const items = (apiBids as unknown as { data?: Bid[] })?.data;
    if (items?.length) return items;
    if (Array.isArray(apiBids) && apiBids.length) return apiBids as unknown as Bid[];
    return mockBids;
  }, [apiBids]);

  const totalValue = allBids.reduce((s, b) => s + b.amount, 0);
  const wonValue = allBids.filter((b) => b.status === 'won').reduce((s, b) => s + b.amount, 0);

  const handleDownloadBid = (bid: Bid) => {
    const csvContent = 'data:text/csv;charset=utf-8,' + [
      'Bid ID,RFP Reference,Vendor,Amount,Status,Deadline,Probability',
      `"${bid.id}","${bid.rfpId}","${bid.vendor}",Rs ${bid.amount},"${bid.status}","${bid.deadline}",${bid.probability}%`,
    ].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${bid.id.toLowerCase()}_proposal.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success(`Commercial bid ${bid.id} proposal downloaded!`);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-amber-glow/10">
            <Gavel size={24} className="text-amber-glow" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Bid Management</h1>
            <p className="text-body text-muted-silver">{allBids.length} bids · Pipeline {formatCompactCurrency(totalValue)}</p>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button variant="secondary" leftIcon={<FileText size={14} />} onClick={() => navigate('/bids/templates')}>
            Templates
          </Button>
          <Button variant="primary" leftIcon={<Plus size={14} />} onClick={() => navigate('/bids/builder')}>
            New Bid
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Pipeline', value: formatCompactCurrency(totalValue), color: 'text-electric-cyan' },
          { label: 'Won Revenue', value: formatCompactCurrency(wonValue), color: 'text-neon-emerald' },
          { label: 'Win Rate', value: `${Math.round((allBids.filter((b) => b.status === 'won').length / (allBids.filter((b) => ['won', 'lost'].includes(b.status)).length || 1)) * 100)}%`, color: 'text-amber-glow' },
          { label: 'Active Bids', value: allBids.filter((b) => !['won', 'lost'].includes(b.status)).length.toString(), color: 'text-violet-pulse' },
        ].map((stat) => (
          <Card key={stat.label} variant="glass" className="!p-3">
            <p className="text-xs text-muted-silver">{stat.label}</p>
            <p className={`text-lg font-bold ${stat.color}`}>{stat.value}</p>
          </Card>
        ))}
      </div>

      {/* View Toggle */}
      <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1 w-fit">
        {[
          { id: 'board' as const, label: 'Board', icon: <LayoutGrid size={14} /> },
          { id: 'list' as const, label: 'List', icon: <List size={14} /> },
          { id: 'calendar' as const, label: 'Calendar', icon: <Calendar size={14} /> },
        ].map((v) => (
          <button
            key={v.id}
            onClick={() => setViewMode(v.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              viewMode === v.id ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'
            }`}
          >
            {v.icon} {v.label}
          </button>
        ))}
      </div>

      {/* Kanban Board */}
      {viewMode === 'board' && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 overflow-x-auto">
          {columns.map((col) => {
            const colBids = allBids.filter((b) => b.status === col.id);
            return (
              <div key={col.id} className="min-w-[200px]">
                <div className="flex items-center gap-2 mb-3 px-1">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: col.color }} />
                  <span className="text-xs font-semibold text-ghost-white uppercase tracking-wider">{col.label}</span>
                  <Badge variant="soft" color="cyan" size="sm">{colBids.length}</Badge>
                </div>
                <div className="space-y-2">
                  {colBids.map((bid) => (
                    <motion.div key={bid.id} whileHover={{ y: -2 }} className="cursor-pointer">
                      <Card variant="glass" className="!p-3 relative overflow-hidden">
                        <div className="absolute top-0 left-0 right-0 h-0.5" style={{ backgroundColor: col.color }} />
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-mono text-electric-cyan">{bid.id}</span>
                          <Badge variant="soft" color={statusBadgeColor(bid.status)} size="sm">
                            {bid.status.replace('_', ' ')}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-silver">{bid.rfpId}</p>
                        <div className="flex items-center gap-1.5 mt-1">
                          <Building2 size={10} className="text-muted-silver" />
                          <span className="text-xs text-ghost-white">{bid.vendor}</span>
                        </div>
                        <p className="text-sm font-bold text-ghost-white mt-2">{formatCompactCurrency(bid.amount)}</p>
                        {/* Probability indicator */}
                        <div className="mt-2">
                          <div className="w-full h-1 rounded-full bg-steel-slate/30">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${bid.probability}%`,
                                backgroundColor: bid.probability >= 70 ? '#00E68A' : bid.probability >= 40 ? '#FFB224' : '#FF4757',
                              }}
                            />
                          </div>
                          <p className="text-[10px] text-muted-silver mt-0.5">{bid.probability}% probability</p>
                        </div>
                        {/* Approval progress */}
                        <div className="flex gap-0.5 mt-2">
                          {Array.from({ length: bid.maxApproval }).map((_, i) => (
                            <div
                              key={i}
                              className={`flex-1 h-1 rounded-full ${
                                i < bid.approvalLevel ? 'bg-neon-emerald' : 'bg-steel-slate/30'
                              }`}
                            />
                          ))}
                        </div>
                        <div className="flex items-center gap-1 mt-2 text-[10px] text-muted-silver">
                          <Clock size={8} /> {bid.deadline}
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <Card variant="glass">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted-silver uppercase tracking-wider border-b border-steel-slate/30">
                  <th className="px-4 py-3">Bid ID</th>
                  <th className="px-4 py-3">RFP</th>
                  <th className="px-4 py-3">Vendor</th>
                  <th className="px-4 py-3 text-right">Amount</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Deadline</th>
                  <th className="px-4 py-3">Approval</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {allBids.map((bid) => (
                  <tr key={bid.id} className="border-b border-steel-slate/15 hover:bg-steel-slate/10 transition-colors cursor-pointer" onClick={() => navigate(`/bids/${bid.id}`)}>
                    <td className="px-4 py-3 font-mono text-electric-cyan text-xs">{bid.id}</td>
                    <td className="px-4 py-3 text-muted-silver text-xs">{bid.rfpId}</td>
                    <td className="px-4 py-3 text-ghost-white">{bid.vendor}</td>
                    <td className="px-4 py-3 text-ghost-white font-bold text-right">{formatCompactCurrency(bid.amount)}</td>
                    <td className="px-4 py-3">
                      <Badge variant="soft" color={statusBadgeColor(bid.status)} size="sm">{bid.status.replace('_', ' ')}</Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-silver text-xs">{bid.deadline}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-0.5 w-16">
                        {Array.from({ length: bid.maxApproval }).map((_, i) => (
                          <div key={i} className={`flex-1 h-1.5 rounded-full ${i < bid.approvalLevel ? 'bg-neon-emerald' : 'bg-steel-slate/30'}`} />
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="xs"
                          leftIcon={<Eye size={10} />}
                          onClick={() => navigate(`/bids/${bid.id}/preview`)}
                        >
                          View
                        </Button>
                        <Button
                          variant="ghost"
                          size="xs"
                          leftIcon={<Download size={10} />}
                          onClick={() => handleDownloadBid(bid)}
                        >
                          PDF
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Calendar View (Simplified) */}
      {viewMode === 'calendar' && (
        <Card variant="glass">
          <CardHeader><CardTitle>Deadline Calendar</CardTitle></CardHeader>
          <div className="grid grid-cols-7 gap-1 text-center">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
              <div key={d} className="text-xs text-muted-silver py-2">{d}</div>
            ))}
            {Array.from({ length: 28 }).map((_, i) => {
              const day = i + 1;
              const bidsOnDay = allBids.filter((b) => {
                const d = new Date(b.deadline).getDate();
                return d === day;
              });
              return (
                <div
                  key={i}
                  className={`py-3 rounded-lg text-sm transition-colors ${
                    bidsOnDay.length > 0
                      ? 'bg-electric-cyan/10 text-electric-cyan font-medium cursor-pointer hover:bg-electric-cyan/20'
                      : 'text-muted-silver/40'
                  }`}
                >
                  {day}
                  {bidsOnDay.length > 0 && (
                    <div className="flex justify-center gap-0.5 mt-1">
                      {bidsOnDay.map((b) => (
                        <span key={b.id} className="w-1.5 h-1.5 rounded-full bg-electric-cyan" />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* ── Bid Analytics ── */}
      <BidAnalyticsWidget />
    </motion.div>
  );
}
