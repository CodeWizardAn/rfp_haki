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
  // DRAFT
  { id: 'B-4418', rfpId: 'RFP-2026-4418', vendor: 'Haki FMCG Procurement', amount: 4850000, status: 'draft', deadline: '2026-03-15', items: 5, createdAt: '2026-10-16', approvalLevel: 1, maxApproval: 4, probability: 78 },
  { id: 'B-0090', rfpId: 'RFP-2026-0003', vendor: 'Finolex Cables', amount: 3200000, status: 'draft', deadline: '2026-02-25', items: 6, createdAt: '2026-02-07', approvalLevel: 0, maxApproval: 4, probability: 45 },
  { id: 'B-0091', rfpId: 'RFP-2026-0003', vendor: 'RR Kabel', amount: 2800000, status: 'draft', deadline: '2026-02-25', items: 4, createdAt: '2026-02-07', approvalLevel: 0, maxApproval: 4, probability: 40 },

  // SUBMITTED
  { id: 'B-0088', rfpId: 'RFP-2026-0001', vendor: 'Polycab India', amount: 5640000, status: 'submitted', deadline: '2026-02-15', items: 4, createdAt: '2026-02-05', approvalLevel: 1, maxApproval: 4, probability: 72 },
  { id: 'B-0092', rfpId: 'RFP-2026-0004', vendor: 'Schneider Electric', amount: 6400000, status: 'submitted', deadline: '2026-03-01', items: 5, createdAt: '2026-02-10', approvalLevel: 2, maxApproval: 4, probability: 68 },

  // UNDER REVIEW
  { id: 'B-0089', rfpId: 'RFP-2026-0002', vendor: 'KEI Industries', amount: 5920000, status: 'under_review', deadline: '2026-02-20', items: 3, createdAt: '2026-02-06', approvalLevel: 2, maxApproval: 4, probability: 60 },
  { id: 'B-0093', rfpId: 'RFP-2026-0005', vendor: 'ABB India', amount: 8250000, status: 'under_review', deadline: '2026-03-05', items: 7, createdAt: '2026-02-11', approvalLevel: 3, maxApproval: 4, probability: 65 },

  // APPROVED
  { id: 'B-0087', rfpId: 'RFP-2026-0001', vendor: 'Havells India', amount: 5860000, status: 'approved', deadline: '2026-02-15', items: 5, createdAt: '2026-02-05', approvalLevel: 4, maxApproval: 4, probability: 85 },
  { id: 'B-0094', rfpId: 'RFP-2026-0006', vendor: 'Siemens Energy', amount: 7500000, status: 'approved', deadline: '2026-02-28', items: 6, createdAt: '2026-02-12', approvalLevel: 4, maxApproval: 4, probability: 88 },

  // WON
  { id: 'B-0085', rfpId: 'RFP-2025-0098', vendor: 'Havells India', amount: 12400000, status: 'won', deadline: '2026-01-20', items: 8, createdAt: '2026-01-10', approvalLevel: 4, maxApproval: 4, probability: 100 },
  { id: 'B-0095', rfpId: 'RFP-2025-0095', vendor: 'Larsen & Toubro', amount: 21000000, status: 'won', deadline: '2026-01-10', items: 12, createdAt: '2025-12-28', approvalLevel: 4, maxApproval: 4, probability: 100 },

  // LOST
  { id: 'B-0084', rfpId: 'RFP-2025-0097', vendor: 'Polycab India', amount: 9100000, status: 'lost', deadline: '2026-01-15', items: 6, createdAt: '2026-01-05', approvalLevel: 4, maxApproval: 4, probability: 0 },
  { id: 'B-0096', rfpId: 'RFP-2025-0092', vendor: 'KEC International', amount: 4500000, status: 'lost', deadline: '2025-12-20', items: 4, createdAt: '2025-12-05', approvalLevel: 4, maxApproval: 4, probability: 0 },
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

  /* Merge backend bids with mock fallback & localStorage custom bids, deduplicating by ID */
  const allBids: Bid[] = useMemo(() => {
    let customBids: Bid[] = [];
    try {
      const saved = localStorage.getItem('haki_custom_bids');
      if (saved) customBids = JSON.parse(saved);
    } catch {
      // ignore
    }
    const items = (apiBids as unknown as { data?: Bid[] })?.data;
    const baseList = (items?.length ? items : Array.isArray(apiBids) && apiBids.length ? (apiBids as unknown as Bid[]) : mockBids);

    const combined: Bid[] = [...customBids];
    const seenIds = new Set(customBids.map((b) => b.id));
    for (const b of baseList) {
      if (!seenIds.has(b.id)) {
        combined.push(b);
        seenIds.add(b.id);
      }
    }
    return combined;
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

      {/* Kanban Board with proper column lanes */}
      {viewMode === 'board' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5 items-start">
          {columns.map((col) => {
            const colBids = allBids.filter((b) => b.status === col.id);
            const colTotal = colBids.reduce((sum, b) => sum + b.amount, 0);

            return (
              <div
                key={col.id}
                className="flex flex-col rounded-2xl bg-slate-100/70 dark:bg-steel-slate/[0.08] border border-slate-200/80 dark:border-steel-slate/20 p-2.5 min-h-[580px] shadow-sm transition-all"
              >
                {/* Column Lane Header */}
                <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-slate-200/70 dark:border-steel-slate/15 px-1">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full shadow-sm" style={{ backgroundColor: col.color }} />
                    <span className="text-xs font-bold text-slate-800 dark:text-ghost-white tracking-wider uppercase">
                      {col.label}
                    </span>
                    <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-slate-200/90 dark:bg-steel-slate/30 text-slate-700 dark:text-slate-300">
                      {colBids.length}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-slate-500 dark:text-muted-silver">
                    {formatCompactCurrency(colTotal)}
                  </span>
                </div>

                {/* Cards Container with smooth scroll and clean spacing */}
                <div className="space-y-2.5 flex-1 overflow-y-auto max-h-[calc(100vh-320px)] pr-0.5 custom-scrollbar">
                  {colBids.map((bid) => (
                    <motion.div
                      key={bid.id}
                      whileHover={{ y: -2, scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => navigate(`/bids/${bid.id}/preview`)}
                      className="cursor-pointer group"
                    >
                      <div className="p-3 rounded-xl bg-white dark:bg-[#121833]/90 border border-slate-200/90 dark:border-steel-slate/25 hover:border-blue-500/60 dark:hover:border-electric-cyan/50 shadow-sm hover:shadow-md transition-all relative overflow-hidden">
                        {/* Status bar on top */}
                        <div className="absolute top-0 left-0 right-0 h-1" style={{ backgroundColor: col.color }} />

                        <div className="flex items-center justify-between mb-1.5 pt-0.5">
                          <span className="text-xs font-mono font-bold text-blue-600 dark:text-electric-cyan group-hover:underline flex items-center gap-1">
                            {bid.id}
                            <Eye size={11} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                          </span>
                          <Badge variant="soft" color={statusBadgeColor(bid.status)} size="sm">
                            {bid.status.replace('_', ' ')}
                          </Badge>
                        </div>

                        <p className="text-xs font-bold text-slate-900 dark:text-ghost-white line-clamp-1">{bid.rfpId}</p>

                        <div className="flex items-center gap-1.5 mt-1 text-slate-600 dark:text-muted-silver">
                          <Building2 size={11} className="shrink-0" />
                          <span className="text-xs truncate">{bid.vendor}</span>
                        </div>

                        <div className="flex items-baseline justify-between mt-2.5 pt-2 border-t border-slate-100 dark:border-steel-slate/15">
                          <span className="text-sm font-extrabold text-slate-900 dark:text-ghost-white">
                            {formatCompactCurrency(bid.amount)}
                          </span>
                          <span className="text-[10px] font-semibold text-slate-500 dark:text-muted-silver">
                            {bid.items} items
                          </span>
                        </div>

                        {/* Probability indicator */}
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-[10px] mb-1">
                            <span className="text-slate-500 dark:text-muted-silver">Win Probability</span>
                            <span className="font-bold text-slate-700 dark:text-slate-200">{bid.probability}%</span>
                          </div>
                          <div className="w-full h-1.5 rounded-full bg-slate-100 dark:bg-steel-slate/30 overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-300"
                              style={{
                                width: `${bid.probability}%`,
                                backgroundColor: bid.probability >= 70 ? '#10B981' : bid.probability >= 40 ? '#F59E0B' : '#EF4444',
                              }}
                            />
                          </div>
                        </div>

                        {/* Card footer with deadline and action */}
                        <div className="flex items-center justify-between mt-2.5 pt-1.5 border-t border-slate-100 dark:border-steel-slate/15 text-[10px] text-slate-500 dark:text-muted-silver">
                          <span className="flex items-center gap-1"><Clock size={10} /> {bid.deadline}</span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadBid(bid);
                            }}
                            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-steel-slate/20 hover:text-blue-600 dark:hover:text-electric-cyan transition-colors"
                            title="Download proposal CSV"
                          >
                            <Download size={11} />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))}

                  {/* Empty placeholder if column has no bids */}
                  {colBids.length === 0 && (
                    <div className="h-32 border-2 border-dashed border-slate-200 dark:border-steel-slate/20 rounded-xl flex items-center justify-center text-xs text-slate-400 dark:text-muted-silver/40">
                      No bids in {col.label}
                    </div>
                  )}
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
                  <tr key={bid.id} className="border-b border-steel-slate/15 hover:bg-steel-slate/10 transition-colors cursor-pointer" onClick={() => navigate(`/bids/${bid.id}/preview`)}>
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
