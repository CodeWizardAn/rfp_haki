import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Building2,
  Search,
  Star,
  MapPin,
  Phone,
  Mail,
  Globe,
  ChevronRight,
  ArrowUpDown,
  Shield,
  Clock,
  Package,
} from 'lucide-react';
import { Card, Badge, Button, Input } from '@/components/ui';
import { useVendors } from '@/hooks/useApi';

const fallbackVendors = [
  { id: 1, name: 'Havells India Ltd', tier: 'platinum', rating: 4.7, orders: 156, onTime: 98, quality: 96, city: 'Noida', country: 'India', categories: ['Cables & Wires', 'Electrical'], contact: 'Rajesh Kumar', email: 'rajesh@havells.com', phone: '+91 98765 43210', website: 'havells.com' },
  { id: 2, name: 'Polycab Wires Ltd', tier: 'gold', rating: 4.5, orders: 128, onTime: 96, quality: 94, city: 'Mumbai', country: 'India', categories: ['Cables & Wires'], contact: 'Priya Sharma', email: 'priya@polycab.com', phone: '+91 98765 43211', website: 'polycab.com' },
  { id: 3, name: 'Schneider Electric', tier: 'platinum', rating: 4.8, orders: 89, onTime: 99, quality: 98, city: 'Bengaluru', country: 'India', categories: ['Electrical', 'Industrial'], contact: 'Amit Singh', email: 'amit@se.com', phone: '+91 98765 43212', website: 'se.com' },
  { id: 4, name: 'Karam Industries', tier: 'gold', rating: 4.4, orders: 67, onTime: 95, quality: 93, city: 'Gurugram', country: 'India', categories: ['Safety Equipment'], contact: 'Sanjay Verma', email: 'sanjay@karam.in', phone: '+91 98765 43213', website: 'karam.in' },
  { id: 5, name: 'ABB India', tier: 'platinum', rating: 4.9, orders: 112, onTime: 99, quality: 99, city: 'Bengaluru', country: 'India', categories: ['Electrical', 'Industrial'], contact: 'Vikram Patel', email: 'vikram@abb.com', phone: '+91 98765 43214', website: 'abb.com' },
  { id: 6, name: 'Finolex Cables', tier: 'silver', rating: 4.2, orders: 78, onTime: 92, quality: 90, city: 'Pune', country: 'India', categories: ['Cables & Wires'], contact: 'Neha Gupta', email: 'neha@finolex.com', phone: '+91 98765 43215', website: 'finolex.com' },
  { id: 7, name: 'Parker Hannifin', tier: 'gold', rating: 4.6, orders: 45, onTime: 97, quality: 96, city: 'Mumbai', country: 'India', categories: ['Industrial'], contact: 'John Davis', email: 'john@parker.com', phone: '+91 98765 43216', website: 'parker.com' },
  { id: 8, name: 'KEI Industries', tier: 'silver', rating: 4.1, orders: 56, onTime: 90, quality: 88, city: 'Delhi', country: 'India', categories: ['Cables & Wires'], contact: 'Ravi Khanna', email: 'ravi@kei.com', phone: '+91 98765 43217', website: 'keiindia.com' },
];

const categories = ['All', 'Cables & Wires', 'Electrical', 'Safety Equipment', 'Industrial', 'FMCG'];
const tierOrder: Record<string, number> = { platinum: 3, gold: 2, silver: 1, bronze: 0, new: -1 };
const tierColors: Record<string, 'silver' | 'amber' | 'cyan'> = { platinum: 'silver', gold: 'amber', silver: 'cyan' };

export default function UserVendorsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [sortBy, setSortBy] = useState<'rating' | 'orders' | 'name' | 'tier'>('rating');

  // ── API ──
  const { data: vendorResponse } = useVendors();

  const vendors = useMemo(() => {
    const apiItems = vendorResponse?.data ?? (vendorResponse as Record<string, any> | undefined)?.items;
    if (Array.isArray(apiItems) && apiItems.length > 0) {
      return apiItems.map((v: any) => ({
        id: v.id ?? v.vendor_id,
        name: v.name ?? v.company_name ?? 'Unknown',
        tier: v.tier ?? 'silver',
        rating: v.rating ?? v.overall_score ?? 4.0,
        orders: v.orders ?? v.total_orders ?? 0,
        onTime: v.onTime ?? v.on_time_delivery ?? 90,
        quality: v.quality ?? v.quality_score ?? 90,
        city: v.city ?? v.location ?? '',
        country: v.country ?? 'India',
        categories: v.categories ?? v.product_categories ?? [],
        contact: v.contact ?? v.contact_person ?? '',
        email: v.email ?? v.contact_email ?? '',
        phone: v.phone ?? v.contact_phone ?? '',
        website: v.website ?? '',
      }));
    }
    return fallbackVendors;
  }, [vendorResponse]);

  const filtered = vendors
    .filter((v) => {
      const matchesSearch = v.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategory === 'All' || v.categories.includes(selectedCategory);
      return matchesSearch && matchesCategory;
    })
    .sort((a, b) => {
      if (sortBy === 'rating') return b.rating - a.rating;
      if (sortBy === 'orders') return b.orders - a.orders;
      if (sortBy === 'tier') return (tierOrder[b.tier] ?? 0) - (tierOrder[a.tier] ?? 0);
      return a.name.localeCompare(b.name);
    });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ghost-white">Vendor Directory</h1>
        <p className="text-body text-muted-silver mt-1">Browse approved vendors and their performance metrics</p>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[300px]">
          <Input
            placeholder="Search vendors..."
            leftIcon={<Search size={16} />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
          className="glass-input px-3 py-2 text-sm text-ghost-white bg-transparent rounded-lg border border-steel-slate/30"
        >
          <option value="rating" className="bg-deep-navy">Sort: Rating</option>
          <option value="tier" className="bg-deep-navy">Sort: Tier</option>
          <option value="orders" className="bg-deep-navy">Sort: Orders</option>
          <option value="name" className="bg-deep-navy">Sort: Name</option>
        </select>
      </div>

      {/* Category pills */}
      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              selectedCategory === cat
                ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30'
                : 'bg-steel-slate/20 text-muted-silver hover:text-ghost-white border border-transparent'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      <p className="text-sm text-muted-silver">
        Showing <span className="text-ghost-white font-medium">{filtered.length}</span> vendors
      </p>

      {/* Vendor cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filtered.map((vendor) => (
          <Card key={vendor.id} variant="interactive">
            <div className="flex items-start gap-4">
              <div className="w-14 h-14 rounded-xl bg-electric-cyan/10 flex items-center justify-center flex-shrink-0">
                <Building2 size={22} className="text-electric-cyan" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-ghost-white truncate">{vendor.name}</h3>
                  <Badge variant="soft" color={tierColors[vendor.tier] || 'cyan'} size="sm">{vendor.tier}</Badge>
                </div>

                <div className="flex items-center gap-3 text-xs text-muted-silver mb-3">
                  <span className="flex items-center gap-1"><MapPin size={10} /> {vendor.city}, {vendor.country}</span>
                  <span className="flex items-center gap-1">
                    <Star size={10} className="text-amber-glow fill-amber-glow" />
                    {vendor.rating}
                  </span>
                  <span>{vendor.orders} orders</span>
                </div>

                <div className="flex flex-wrap gap-1.5 mb-3">
                  {vendor.categories.map((cat: string) => (
                    <Badge key={cat} variant="outline" color="cyan" size="sm">{cat}</Badge>
                  ))}
                </div>

                {/* Performance metrics */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-2 rounded-lg bg-steel-slate/10">
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      <Clock size={10} className="text-muted-silver" />
                      <span className="text-xs text-muted-silver">On-Time</span>
                    </div>
                    <span className={`text-sm font-bold ${vendor.onTime >= 95 ? 'text-neon-emerald' : 'text-amber-glow'}`}>
                      {vendor.onTime}%
                    </span>
                  </div>
                  <div className="text-center p-2 rounded-lg bg-steel-slate/10">
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      <Shield size={10} className="text-muted-silver" />
                      <span className="text-xs text-muted-silver">Quality</span>
                    </div>
                    <span className={`text-sm font-bold ${vendor.quality >= 95 ? 'text-neon-emerald' : 'text-amber-glow'}`}>
                      {vendor.quality}%
                    </span>
                  </div>
                  <div className="text-center p-2 rounded-lg bg-steel-slate/10">
                    <div className="flex items-center justify-center gap-1 mb-0.5">
                      <Package size={10} className="text-muted-silver" />
                      <span className="text-xs text-muted-silver">Orders</span>
                    </div>
                    <span className="text-sm font-bold text-ghost-white">{vendor.orders}</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}
