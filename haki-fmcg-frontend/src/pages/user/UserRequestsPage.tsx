import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  FileText,
  Plus,
  Search,
  Clock,
  CheckCircle2,
  ChevronRight,
  Calendar,
  Package,
} from 'lucide-react';
import { Card, Badge, Button, Input } from '@/components/ui';

const statusConfig: Record<string, { label: string; color: 'cyan' | 'emerald' | 'amber' | 'coral' | 'rose' | 'violet' | 'silver' }> = {
  draft: { label: 'Draft', color: 'silver' },
  submitted: { label: 'Submitted', color: 'cyan' },
  extracting: { label: 'Processing', color: 'violet' },
  matching: { label: 'Matching', color: 'violet' },
  pricing: { label: 'Pricing', color: 'amber' },
  review: { label: 'Under Review', color: 'rose' },
  won: { label: 'Awarded', color: 'emerald' },
  lost: { label: 'Not Selected', color: 'coral' },
  cancelled: { label: 'Cancelled', color: 'silver' },
};

const requests = [
  { id: 'REQ-2026-0042', title: 'Electrical Cables for Nairobi Office', status: 'review', priority: 'high', items: 12, value: 2450000, deadline: '2026-02-15', created: '2026-02-08', progress: 75 },
  { id: 'REQ-2026-0041', title: 'FMCG Products Q1 Restock', status: 'pricing', priority: 'medium', items: 45, value: 8750000, deadline: '2026-02-20', created: '2026-02-06', progress: 60 },
  { id: 'REQ-2026-0038', title: 'Safety Equipment — Warehouse', status: 'submitted', priority: 'high', items: 8, value: 890000, deadline: '2026-02-25', created: '2026-02-02', progress: 90 },
  { id: 'REQ-2026-0035', title: 'Office Supplies Annual Contract', status: 'won', priority: 'low', items: 32, value: 1200000, deadline: '2026-01-30', created: '2026-01-20', progress: 100 },
  { id: 'REQ-2026-0033', title: 'Industrial Lubricants Bulk Order', status: 'lost', priority: 'medium', items: 15, value: 3200000, deadline: '2026-01-25', created: '2026-01-12', progress: 100 },
  { id: 'REQ-2026-0030', title: 'Electrical Switchgear Set', status: 'won', priority: 'critical', items: 22, value: 5600000, deadline: '2026-01-15', created: '2025-12-28', progress: 100 },
  { id: 'REQ-2026-0028', title: 'Cleaning Supplies Monthly', status: 'draft', priority: 'low', items: 18, value: 320000, deadline: '2026-03-01', created: '2026-02-09', progress: 10 },
];

const priorityColors: Record<string, string> = {
  critical: 'text-coral-flame',
  high: 'text-amber-glow',
  medium: 'text-electric-cyan',
  low: 'text-muted-silver',
};

const tabs = ['All', 'Active', 'Awarded', 'Draft', 'Completed'];

export default function UserRequestsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('All');

  const filteredRequests = requests.filter((req) => {
    const matchesSearch = req.title.toLowerCase().includes(searchQuery.toLowerCase()) || req.id.toLowerCase().includes(searchQuery.toLowerCase());
    if (activeTab === 'Active') return matchesSearch && ['submitted', 'extracting', 'matching', 'pricing', 'review'].includes(req.status);
    if (activeTab === 'Awarded') return matchesSearch && req.status === 'won';
    if (activeTab === 'Draft') return matchesSearch && req.status === 'draft';
    if (activeTab === 'Completed') return matchesSearch && ['won', 'lost', 'cancelled'].includes(req.status);
    return matchesSearch;
  });

  const stats = {
    total: requests.length,
    active: requests.filter((r) => ['submitted', 'extracting', 'matching', 'pricing', 'review'].includes(r.status)).length,
    won: requests.filter((r) => r.status === 'won').length,
    totalValue: requests.reduce((sum, r) => sum + r.value, 0),
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ghost-white">My Requests</h1>
          <p className="text-body text-muted-silver mt-1">Manage your procurement requests and track their progress</p>
        </div>
        <Link to="/user/new-request">
          <Button variant="primary" leftIcon={<Plus size={16} />}>
            New Request
          </Button>
        </Link>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-electric-cyan/10 flex items-center justify-center">
            <FileText size={18} className="text-electric-cyan" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.total}</p>
            <p className="text-xs text-muted-silver">Total Requests</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-glow/10 flex items-center justify-center">
            <Clock size={18} className="text-amber-glow" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.active}</p>
            <p className="text-xs text-muted-silver">Active</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-neon-emerald/10 flex items-center justify-center">
            <CheckCircle2 size={18} className="text-neon-emerald" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.won}</p>
            <p className="text-xs text-muted-silver">Awarded</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-violet-pulse/10 flex items-center justify-center">
            <Package size={18} className="text-violet-pulse" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">₹{(stats.totalValue / 100000).toFixed(0)}L</p>
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
              <motion.div layoutId="request-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-electric-cyan rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Search */}
      <Input
        placeholder="Search requests..."
        leftIcon={<Search size={16} />}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      {/* Request list */}
      <div className="space-y-3">
        {filteredRequests.map((req) => {
          const config = statusConfig[req.status] || statusConfig.draft!;
          return (
            <Link key={req.id} to="/user/rfp-analyzer" state={{ analysisId: req.id }}>
              <Card variant="interactive">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="w-12 h-12 rounded-xl bg-steel-slate/30 flex items-center justify-center flex-shrink-0">
                      <FileText size={20} className="text-electric-cyan" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-mono text-muted-silver">{req.id}</span>
                        <Badge variant="soft" color={config.color} size="sm">{config.label}</Badge>
                        <span className={`text-[10px] font-semibold uppercase ${priorityColors[req.priority]}`}>
                          {req.priority}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-ghost-white truncate">{req.title}</h3>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted-silver">
                        <span className="flex items-center gap-1"><Package size={10} /> {req.items} items</span>
                        <span className="flex items-center gap-1"><Calendar size={10} /> Due: {req.deadline}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    {/* Progress bar */}
                    <div className="hidden md:block w-32">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] text-muted-silver">Progress</span>
                        <span className="text-[10px] text-ghost-white">{req.progress}%</span>
                      </div>
                      <div className="h-1.5 bg-steel-slate/30 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${req.progress}%` }}
                          className={`h-full rounded-full ${req.status === 'won' ? 'bg-neon-emerald' : req.status === 'lost' ? 'bg-coral-flame' : 'bg-electric-cyan'}`}
                        />
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="text-sm font-bold text-ghost-white">₹{(req.value / 100000).toFixed(1)}L</p>
                      <p className="text-[10px] text-muted-silver">{req.created}</p>
                    </div>

                    <ChevronRight size={16} className="text-muted-silver" />
                  </div>
                </div>
              </Card>
            </Link>
          );
        })}

        {filteredRequests.length === 0 && (
          <Card className="flex flex-col items-center justify-center py-12">
            <FileText size={40} className="text-muted-silver/30 mb-3" />
            <p className="text-sm text-muted-silver">No requests found</p>
            <Link to="/user/new-request">
              <Button variant="primary" size="sm" className="mt-3" leftIcon={<Plus size={14} />}>
                Create Request
              </Button>
            </Link>
          </Card>
        )}
      </div>
    </motion.div>
  );
}
