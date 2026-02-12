import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Receipt,
  Plus,
  Search,
  Clock,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Building2,
  Package,
  FileText,
  MessageSquare,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Badge, Button, Input } from '@/components/ui';

const quoteStatusConfig: Record<string, { label: string; color: 'cyan' | 'emerald' | 'amber' | 'coral' | 'silver' | 'violet' }> = {
  pending: { label: 'Pending', color: 'amber' },
  received: { label: 'Received', color: 'cyan' },
  accepted: { label: 'Accepted', color: 'emerald' },
  rejected: { label: 'Rejected', color: 'coral' },
  expired: { label: 'Expired', color: 'silver' },
  negotiating: { label: 'Negotiating', color: 'violet' },
};

const quotes = [
  { id: 'QT-0162', product: 'FR PVC Insulated Copper Cable 1.5 sq mm', vendor: 'Havells India Ltd', qty: 50, unit: 'coils', requestedPrice: 1250, quotedPrice: 1180, status: 'received', created: '2026-02-08', validUntil: '2026-02-22', responses: 1 },
  { id: 'QT-0158', product: 'XLPE Power Cable 4 Core 16 sq mm', vendor: 'Polycab Wires Ltd', qty: 20, unit: 'drums', requestedPrice: 8500, quotedPrice: 8200, status: 'negotiating', created: '2026-02-05', validUntil: '2026-02-19', responses: 3 },
  { id: 'QT-0156', product: 'MCB 32A Single Pole', vendor: 'ABB India', qty: 200, unit: 'units', requestedPrice: 385, quotedPrice: 365, status: 'received', created: '2026-02-03', validUntil: '2026-02-17', responses: 1 },
  { id: 'QT-0152', product: 'Industrial Safety Helmet ISI Mark', vendor: 'Karam Industries', qty: 100, unit: 'units', requestedPrice: 680, quotedPrice: 620, status: 'accepted', created: '2026-01-28', validUntil: '2026-02-11', responses: 2 },
  { id: 'QT-0148', product: 'Armoured Cable 3.5 Core 25 sq mm', vendor: 'Finolex Cables', qty: 10, unit: 'drums', requestedPrice: 14200, quotedPrice: null, status: 'pending', created: '2026-02-09', validUntil: '2026-02-23', responses: 0 },
  { id: 'QT-0145', product: 'Cut-Resistant Gloves Level 5', vendor: 'Multiple Vendors', qty: 500, unit: 'pairs', requestedPrice: 950, quotedPrice: 880, status: 'expired', created: '2026-01-10', validUntil: '2026-01-24', responses: 4 },
];

const tabs = ['All', 'Pending', 'Received', 'Accepted', 'Expired'];

export default function UserQuotesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('All');

  const filtered = quotes.filter((q) => {
    const matchesSearch = q.product.toLowerCase().includes(searchQuery.toLowerCase()) || q.id.toLowerCase().includes(searchQuery.toLowerCase());
    if (activeTab === 'Pending') return matchesSearch && q.status === 'pending';
    if (activeTab === 'Received') return matchesSearch && ['received', 'negotiating'].includes(q.status);
    if (activeTab === 'Accepted') return matchesSearch && q.status === 'accepted';
    if (activeTab === 'Expired') return matchesSearch && q.status === 'expired';
    return matchesSearch;
  });

  const stats = {
    total: quotes.length,
    pending: quotes.filter((q) => q.status === 'pending').length,
    received: quotes.filter((q) => ['received', 'negotiating'].includes(q.status)).length,
    savings: quotes
      .filter((q) => q.quotedPrice && q.quotedPrice < q.requestedPrice)
      .reduce((s, q) => s + (q.requestedPrice - (q.quotedPrice || 0)) * q.qty, 0),
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ghost-white">Price Quotes</h1>
          <p className="text-body text-muted-silver mt-1">Request and manage vendor price quotations</p>
        </div>
        <Button variant="primary" leftIcon={<Plus size={16} />}>
          Request Quote
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-electric-cyan/10 flex items-center justify-center">
            <Receipt size={18} className="text-electric-cyan" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.total}</p>
            <p className="text-xs text-muted-silver">Total Quotes</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-glow/10 flex items-center justify-center">
            <Clock size={18} className="text-amber-glow" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.pending}</p>
            <p className="text-xs text-muted-silver">Pending</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-violet-pulse/10 flex items-center justify-center">
            <MessageSquare size={18} className="text-violet-pulse" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">{stats.received}</p>
            <p className="text-xs text-muted-silver">Responses</p>
          </div>
        </Card>
        <Card className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-neon-emerald/10 flex items-center justify-center">
            <CheckCircle2 size={18} className="text-neon-emerald" />
          </div>
          <div>
            <p className="text-lg font-bold text-ghost-white">₹{(stats.savings / 100000).toFixed(1)}L</p>
            <p className="text-xs text-muted-silver">Savings</p>
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
              <motion.div layoutId="quote-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-electric-cyan rounded-full" />
            )}
          </button>
        ))}
      </div>

      <Input
        placeholder="Search quotes..."
        leftIcon={<Search size={16} />}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      {/* Quotes list */}
      <div className="space-y-3">
        {filtered.map((quote) => {
          const config = quoteStatusConfig[quote.status];
          const savings = quote.quotedPrice ? quote.requestedPrice - quote.quotedPrice : 0;
          return (
            <Card key={quote.id} variant="interactive">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className="w-12 h-12 rounded-xl bg-violet-pulse/10 flex items-center justify-center flex-shrink-0">
                    <Receipt size={20} className="text-violet-pulse" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-mono text-muted-silver">{quote.id}</span>
                      <Badge variant="soft" color={config.color} size="sm">{config.label}</Badge>
                      {quote.responses > 0 && (
                        <Badge variant="soft" color="cyan" size="sm">{quote.responses} response{quote.responses > 1 ? 's' : ''}</Badge>
                      )}
                    </div>
                    <h3 className="text-sm font-semibold text-ghost-white truncate">{quote.product}</h3>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-silver">
                      <span className="flex items-center gap-1"><Building2 size={10} /> {quote.vendor}</span>
                      <span>{quote.qty} {quote.unit}</span>
                      <span>Valid until: {quote.validUntil}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      {quote.quotedPrice && (
                        <>
                          <span className="text-xs text-muted-silver line-through">₹{quote.requestedPrice.toLocaleString()}</span>
                          <span className="text-sm font-bold text-ghost-white">₹{quote.quotedPrice.toLocaleString()}</span>
                        </>
                      )}
                      {!quote.quotedPrice && (
                        <span className="text-sm text-muted-silver">₹{quote.requestedPrice.toLocaleString()}</span>
                      )}
                    </div>
                    {savings > 0 && (
                      <span className="text-[10px] text-neon-emerald font-medium">
                        Save ₹{savings.toLocaleString()}/unit
                      </span>
                    )}
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
