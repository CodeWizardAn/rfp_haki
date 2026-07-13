import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Banknote,
  Search,
  Clock,
  CheckCircle2,
  XCircle,
  Trophy,
  ChevronRight,
  FileText,
  TrendingUp,
  Eye,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Badge, Button, Input } from '@/components/ui';
import { useBids } from '@/hooks/useApi';

const bidStatusConfig: Record<string, { label: string; color: 'cyan' | 'emerald' | 'amber' | 'coral' | 'silver'; icon: React.ReactNode }> = {
  draft: { label: 'Draft', color: 'silver', icon: <Clock size={14} /> },
  in_review: { label: 'In Review', color: 'cyan', icon: <Eye size={14} /> },
  approved: { label: 'Approved', color: 'emerald', icon: <CheckCircle2 size={14} /> },
  rejected: { label: 'Rejected', color: 'coral', icon: <XCircle size={14} /> },
  submitted: { label: 'Submitted', color: 'cyan', icon: <TrendingUp size={14} /> },
  won: { label: 'Won', color: 'emerald', icon: <Trophy size={14} /> },
  lost: { label: 'Lost', color: 'coral', icon: <XCircle size={14} /> },
};

const fallbackBids = [
  { id: 'BID-0087', rfpId: 'REQ-2026-0042', title: 'Electrical Cables for Nairobi Office', status: 'in_review', value: 2450000, items: 12, techScore: 85, commercialScore: 78, created: '2026-02-08', deadline: '2026-02-15' },
  { id: 'BID-0084', rfpId: 'REQ-2026-0041', title: 'FMCG Products Q1 Restock', status: 'approved', value: 8750000, items: 45, techScore: 92, commercialScore: 88, created: '2026-02-06', deadline: '2026-02-20' },
  { id: 'BID-0082', rfpId: 'REQ-2026-0039', title: 'Wiring Harness Set — Factory Floor', status: 'submitted', value: 4200000, items: 18, techScore: 88, commercialScore: 82, created: '2026-02-04', deadline: '2026-02-18' },
  { id: 'BID-0079', rfpId: 'REQ-2026-0035', title: 'Office Supplies Annual Contract', status: 'won', value: 1200000, items: 32, techScore: 90, commercialScore: 91, created: '2026-01-28', deadline: '2026-01-30' },
  { id: 'BID-0076', rfpId: 'REQ-2026-0033', title: 'Industrial Lubricants Bulk Order', status: 'lost', value: 3200000, items: 15, techScore: 75, commercialScore: 70, created: '2026-01-20', deadline: '2026-01-25' },
  { id: 'BID-0072', rfpId: 'REQ-2026-0030', title: 'Electrical Switchgear Set', status: 'won', value: 5600000, items: 22, techScore: 94, commercialScore: 89, created: '2026-01-10', deadline: '2026-01-15' },
];

function ScoreBar({ label, score }: { label: string; score: number }) {
  const color = score >= 85 ? 'bg-neon-emerald' : score >= 70 ? 'bg-amber-glow' : 'bg-coral-flame';
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-muted-silver w-20">{label}</span>
      <div className="flex-1 h-1.5 bg-steel-slate/30 rounded-full overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${score}%` }} className={`h-full rounded-full ${color}`} />
      </div>
      <span className="text-xs text-ghost-white font-medium w-8 text-right">{score}</span>
    </div>
  );
}

const tabs = ['All', 'Active', 'Won', 'Lost'];

export default function UserBidsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('All');

  // ── API ──
  const { data: bidResponse } = useBids();

  const bids = useMemo(() => {
    const apiItems = bidResponse?.data ?? (bidResponse as Record<string, any> | undefined)?.items;
    if (Array.isArray(apiItems) && apiItems.length > 0) {
      return apiItems.map((b: any) => ({
        id: b.id ?? b.bid_id ?? `BID-${b.id}`,
        rfpId: b.rfpId ?? b.rfp_id ?? '',
        title: b.title ?? b.rfp_title ?? 'Untitled Bid',
        status: b.status ?? 'draft',
        value: b.value ?? b.total_value ?? b.amount ?? 0,
        items: Array.isArray(b.items) ? b.items.length : b.item_count ?? b.line_items?.length ?? 0,
        techScore: b.techScore ?? b.technical_score ?? 0,
        commercialScore: b.commercialScore ?? b.commercial_score ?? 0,
        created: b.created ?? b.created_at ?? '',
        deadline: b.deadline ?? b.due_date ?? '',
      }));
    }
    return fallbackBids;
  }, [bidResponse]);

  const filteredBids = bids.filter((bid) => {
    const matchesSearch = bid.title.toLowerCase().includes(searchQuery.toLowerCase()) || String(bid.id).toLowerCase().includes(searchQuery.toLowerCase());
    if (activeTab === 'Active') return matchesSearch && ['draft', 'in_review', 'approved', 'submitted'].includes(bid.status);
    if (activeTab === 'Won') return matchesSearch && bid.status === 'won';
    if (activeTab === 'Lost') return matchesSearch && bid.status === 'lost';
    return matchesSearch;
  });

  const stats = {
    total: bids.length,
    active: bids.filter((b) => ['draft', 'in_review', 'approved', 'submitted'].includes(b.status)).length,
    won: bids.filter((b) => b.status === 'won').length,
    winRate: (() => {
      const decided = bids.filter((b) => ['won', 'lost'].includes(b.status));
      if (decided.length === 0) return 0;
      return Math.round((bids.filter((b) => b.status === 'won').length / decided.length) * 100);
    })(),
    totalValue: bids.reduce((s, b) => s + b.value, 0),
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ghost-white">My Bids</h1>
        <p className="text-body text-muted-silver mt-1">Track bid status and performance across your requests</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-electric-cyan/10 flex items-center justify-center">
            <Banknote size={18} className="text-electric-cyan" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.total}</p>
            <p className="text-xs text-muted-silver">Total Bids</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-glow/10 flex items-center justify-center">
            <Clock size={18} className="text-amber-glow" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.active}</p>
            <p className="text-xs text-muted-silver">Active Bids</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-neon-emerald/10 flex items-center justify-center">
            <Trophy size={18} className="text-neon-emerald" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.winRate}%</p>
            <p className="text-xs text-muted-silver">Win Rate</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-violet-pulse/10 flex items-center justify-center">
            <TrendingUp size={18} className="text-violet-pulse" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">₹{(stats.totalValue / 10000000).toFixed(1)}Cr</p>
            <p className="text-xs text-muted-silver">Total Value</p>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-4 border-b border-steel-slate/20">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2.5 text-sm font-medium transition-colors relative ${
              activeTab === tab ? 'text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'
            }`}
          >
            {tab}
            {activeTab === tab && (
              <motion.div layoutId="bid-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-electric-cyan rounded-full" />
            )}
          </button>
        ))}
      </div>

      <Input
        placeholder="Search bids..."
        leftIcon={<Search size={16} />}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      {/* Bid list */}
      <div className="space-y-3">
        {filteredBids.map((bid) => {
          const config = bidStatusConfig[bid.status] ?? bidStatusConfig.draft!;
          return (
            <Card key={bid.id} variant="interactive">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  <div className="w-12 h-12 rounded-xl bg-amber-glow/10 flex items-center justify-center flex-shrink-0">
                    <Banknote size={20} className="text-amber-glow" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-mono text-electric-cyan">{bid.id}</span>
                      <Badge variant="soft" color={config.color} size="sm">{config.label}</Badge>
                    </div>
                    <h3 className="text-sm font-semibold text-ghost-white truncate">{bid.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-silver">
                      <span className="flex items-center gap-1"><FileText size={10} /> {bid.rfpId}</span>
                      <span>{bid.items} items</span>
                      <span>Deadline: {bid.deadline}</span>
                    </div>

                    {/* Scores */}
                    <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 max-w-sm">
                      <ScoreBar label="Technical" score={bid.techScore} />
                      <ScoreBar label="Commercial" score={bid.commercialScore} />
                    </div>
                  </div>
                </div>

                <div className="text-right flex items-center gap-4">
                  <div>
                    <p className="text-lg font-bold text-ghost-white">₹{(bid.value / 100000).toFixed(1)}L</p>
                    <p className="text-[10px] text-muted-silver">{bid.created}</p>
                  </div>
                  <ChevronRight size={16} className="text-muted-silver" />
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
