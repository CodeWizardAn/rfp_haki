import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Building2,
  Search,
  Plus,
  Star,
  MapPin,

  ExternalLink,
  LayoutGrid,
  List,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';
import { formatCompactCurrency } from '@/utils/formatters';
import { useVendors } from '@/hooks/useApi';
import { useNavigate } from 'react-router-dom';

const mockVendors = [
  {
    id: 'V-001', name: 'Havells India Ltd', category: 'OEM',
    rating: 4.8, totalBids: 42, wonBids: 35, avgDelivery: '12 days',
    revenue: 15800000, products: 33, location: 'Noida, UP',
    contact: { email: 'procurement@havells.com', phone: '+91-120-4771000' },
    tags: ['cables', 'wires', 'switchgear'], status: 'active',
    compliance: 98, trend: 'up' as const,
  },
  {
    id: 'V-002', name: 'Polycab India Ltd', category: 'OEM',
    rating: 4.6, totalBids: 38, wonBids: 28, avgDelivery: '10 days',
    revenue: 12400000, products: 285, location: 'Halol, Gujarat',
    contact: { email: 'sales@polycab.com', phone: '+91-2676-232000' },
    tags: ['cables', 'wires', 'fans'], status: 'active',
    compliance: 95, trend: 'up' as const,
  },
  {
    id: 'V-003', name: 'KEI Industries Ltd', category: 'OEM',
    rating: 4.5, totalBids: 24, wonBids: 18, avgDelivery: '15 days',
    revenue: 8600000, products: 45, location: 'Delhi',
    contact: { email: 'info@keiind.com', phone: '+91-11-4150-9400' },
    tags: ['ht-cable', 'lt-cable', 'house-wire'], status: 'active',
    compliance: 92, trend: 'stable' as const,
  },
  {
    id: 'V-004', name: 'Finolex Cables Ltd', category: 'OEM',
    rating: 4.7, totalBids: 31, wonBids: 22, avgDelivery: '14 days',
    revenue: 10200000, products: 164, location: 'Pune, Maharashtra',
    contact: { email: 'cables@finolex.com', phone: '+91-20-2740-6200' },
    tags: ['wires', 'cables', 'pipes'], status: 'active',
    compliance: 96, trend: 'up' as const,
  },
  {
    id: 'V-005', name: 'RR Kabel Ltd', category: 'OEM',
    rating: 4.4, totalBids: 19, wonBids: 12, avgDelivery: '18 days',
    revenue: 5800000, products: 166, location: 'Waghodia, Gujarat',
    contact: { email: 'enquiry@rfrshcables.com', phone: '+91-2668-264202' },
    tags: ['cables', 'wires'], status: 'active',
    compliance: 89, trend: 'down' as const,
  },
  {
    id: 'V-006', name: 'Moglix Industrial', category: 'Distributor',
    rating: 4.2, totalBids: 11, wonBids: 6, avgDelivery: '8 days',
    revenue: 3200000, products: 450, location: 'Noida, UP',
    contact: { email: 'business@moglix.com', phone: '+91-120-4600-000' },
    tags: ['industrial', 'multi-brand'], status: 'active',
    compliance: 85, trend: 'stable' as const,
  },
];

const trendColor = (t: string) => t === 'up' ? 'text-neon-emerald' : t === 'down' ? 'text-coral-flame' : 'text-muted-silver';
const trendIcon = (t: string) => t === 'up' ? '↑' : t === 'down' ? '↓' : '→';

export default function VendorsPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null);
  const navigate = useNavigate();

  /* ── Backend hooks ── */
  const { data: apiVendors } = useVendors({ search: searchQuery || undefined });

  /* Merge with mock fallback */
  const allVendors = useMemo(() => {
    const raw = (apiVendors as unknown as { data?: Record<string, any>[] })?.data
      ?? (Array.isArray(apiVendors) ? (apiVendors as unknown as Record<string, any>[]) : undefined);
    if (!raw?.length) return mockVendors;
    // API vendor shape (categories, is_active, total_orders, compliance_score, flat
    // email/phone) doesn't match the mock shape — map fields explicitly.
    return raw.map((v): (typeof mockVendors)[number] => ({
      id: v.vendor_id ?? String(v.id ?? ''),
      name: v.name ?? 'Unknown Vendor',
      category: v.categories?.[0] ?? 'Vendor',
      rating: v.rating ?? 0,
      totalBids: v.total_orders ?? 0,
      wonBids: 0,
      avgDelivery: v.on_time_delivery_rate != null ? `${v.on_time_delivery_rate}% on-time` : '—',
      revenue: 0,
      products: Array.isArray(v.products) ? v.products.length : 0,
      location: v.city || v.address || '—',
      contact: { email: v.email ?? '', phone: v.phone ?? '' },
      tags: v.categories ?? [],
      status: v.is_active ? 'active' : 'inactive',
      compliance: v.compliance_score ?? 0,
      trend: 'stable' as const,
    }));
  }, [apiVendors]);

  const filtered = allVendors.filter((v) =>
    !searchQuery || v.name.toLowerCase().includes(searchQuery.toLowerCase()) || v.tags.some((t) => t.includes(searchQuery.toLowerCase())),
  );

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-violet-pulse/10">
            <Building2 size={24} className="text-violet-pulse" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Vendor Directory</h1>
            <p className="text-body text-muted-silver">{allVendors.length} vendors · {allVendors.filter((v) => v.status === 'active').length} active</p>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button variant="primary" leftIcon={<Plus size={14} />} onClick={() => navigate('/vendors/register')}>
            Add Vendor
          </Button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Revenue', value: formatCompactCurrency(allVendors.reduce((s, v) => s + v.revenue, 0)), color: 'text-neon-emerald' },
          { label: 'Avg Rating', value: (allVendors.reduce((s, v) => s + v.rating, 0) / (allVendors.length || 1)).toFixed(1), color: 'text-amber-glow' },
          { label: 'Win Rate', value: `${Math.round((allVendors.reduce((s, v) => s + v.wonBids, 0) / (allVendors.reduce((s, v) => s + v.totalBids, 0) || 1)) * 100)}%`, color: 'text-electric-cyan' },
          { label: 'Products', value: allVendors.reduce((s, v) => s + v.products, 0).toLocaleString(), color: 'text-violet-pulse' },
        ].map((stat) => (
          <Card key={stat.label} variant="glass" className="!p-3">
            <p className="text-xs text-muted-silver">{stat.label}</p>
            <p className={`text-lg font-bold ${stat.color}`}>{stat.value}</p>
          </Card>
        ))}
      </div>

      {/* Search + View */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search vendors, categories, tags…"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50"
          />
        </div>
        <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1.5 rounded-lg ${viewMode === 'grid' ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'}`}
          >
            <LayoutGrid size={16} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1.5 rounded-lg ${viewMode === 'list' ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'}`}
          >
            <List size={16} />
          </button>
        </div>
      </div>

      {/* Vendor Cards */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-3'}>
        {filtered.map((v) => (
          <motion.div key={v.id} whileHover={{ y: -2 }}>
            <Card
              variant="glass"
              className={`cursor-pointer transition-all ${selectedVendor === v.id ? 'ring-2 ring-violet-pulse/40' : ''}`}
              onClick={() => setSelectedVendor(selectedVendor === v.id ? null : v.id)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-pulse/20 to-electric-cyan/20 flex items-center justify-center text-ghost-white font-bold text-sm">
                    {v.name.split(' ').slice(0, 2).map((w) => w[0]).join('')}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ghost-white">{v.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge variant="soft" color={v.category === 'OEM' ? 'cyan' : 'amber'} size="sm">{v.category}</Badge>
                      <span className="flex items-center gap-0.5 text-xs text-amber-glow">
                        <Star size={10} fill="currentColor" /> {v.rating}
                      </span>
                    </div>
                  </div>
                </div>
                <span className={`text-sm font-bold ${trendColor(v.trend)}`}>{trendIcon(v.trend)}</span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center mb-3">
                <div className="py-1.5 rounded-lg bg-steel-slate/10">
                  <p className="text-xs font-bold text-ghost-white">{v.wonBids}/{v.totalBids}</p>
                  <p className="text-[10px] text-muted-silver">Bids Won</p>
                </div>
                <div className="py-1.5 rounded-lg bg-steel-slate/10">
                  <p className="text-xs font-bold text-ghost-white">{v.products}</p>
                  <p className="text-[10px] text-muted-silver">Products</p>
                </div>
                <div className="py-1.5 rounded-lg bg-steel-slate/10">
                  <p className="text-xs font-bold text-ghost-white">{v.avgDelivery}</p>
                  <p className="text-[10px] text-muted-silver">Avg Delivery</p>
                </div>
              </div>

              {/* Compliance bar */}
              <div className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-silver">Compliance</span>
                  <span className={v.compliance >= 95 ? 'text-neon-emerald' : v.compliance >= 85 ? 'text-amber-glow' : 'text-coral-flame'}>{v.compliance}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-steel-slate/30">
                  <div
                    className={`h-full rounded-full ${v.compliance >= 95 ? 'bg-neon-emerald' : v.compliance >= 85 ? 'bg-amber-glow' : 'bg-coral-flame'}`}
                    style={{ width: `${v.compliance}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-muted-silver mb-2">
                <MapPin size={10} /> {v.location}
              </div>

              <div className="flex flex-wrap gap-1">
                {v.tags.map((tag) => (
                  <Badge key={tag} variant="outline" color="cyan" size="sm">{tag}</Badge>
                ))}
              </div>

              <div className="flex items-center justify-between mt-3 pt-3 border-t border-steel-slate/15">
                <p className="text-sm font-bold text-ghost-white">{formatCompactCurrency(v.revenue)}</p>
                <Button variant="ghost" size="xs" leftIcon={<ExternalLink size={10} />} onClick={(e) => { e.stopPropagation(); navigate(`/vendors/${v.id}`); }}>View</Button>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
