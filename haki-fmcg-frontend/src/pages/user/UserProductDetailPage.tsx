import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Star,
  Heart,
  ShoppingCart,
  Building2,
  Clock,
  Shield,
  TrendingDown,
  TrendingUp,
  Minus,
  Package,
  Receipt,
  ChevronRight,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Badge, Button } from '@/components/ui';

// Mock product detail
const mockProduct = {
  id: 1,
  sku: 'CAB-001',
  name: 'FR PVC Insulated Copper Cable 1.5 sq mm',
  description: 'High-quality flame retardant PVC insulated copper conductor cable suitable for domestic and industrial wiring applications. Compliant with IS 694 standards. Temperature rating: 70°C. Voltage grade: 1100V.',
  category: 'Cables & Wires',
  subcategory: 'PVC Insulated',
  brand: 'Havells',
  manufacturer: 'Havells India Ltd',
  price: 1250,
  currency: 'INR',
  unit: 'per 100m',
  moq: 5,
  leadTime: 7,
  rating: 4.5,
  reviews: 128,
  inStock: true,
  stockQty: 450,
  certifications: ['ISI Mark', 'IS 694:2010', 'BIS Certified', 'REACH Compliant'],
  specifications: {
    'Conductor Material': 'Electrolytic Copper',
    'Cross Section': '1.5 sq mm',
    'No. of Strands': '7/0.52mm',
    'Insulation': 'FR PVC',
    'Voltage Grade': '1100V',
    'Temperature Rating': '70°C',
    'Current Rating': '18A',
    'Color Options': 'Red, Yellow, Blue, Green, Black',
    'Standard': 'IS 694:2010',
    'Packing': '90m coil / 200m drum',
  },
  vendors: [
    { id: 1, name: 'Havells India Ltd', tier: 'platinum', price: 1250, rating: 4.7, leadTime: 5, onTimeRate: 98 },
    { id: 2, name: 'Polycab Wires Ltd', tier: 'gold', price: 1180, rating: 4.5, leadTime: 7, onTimeRate: 96 },
    { id: 3, name: 'Finolex Cables', tier: 'gold', price: 1320, rating: 4.4, leadTime: 10, onTimeRate: 94 },
    { id: 4, name: 'KEI Industries', tier: 'silver', price: 1150, rating: 4.2, leadTime: 12, onTimeRate: 91 },
  ],
  priceHistory: [
    { date: 'Sep 2025', price: 1400 },
    { date: 'Oct 2025', price: 1380 },
    { date: 'Nov 2025', price: 1320 },
    { date: 'Dec 2025', price: 1280 },
    { date: 'Jan 2026', price: 1260 },
    { date: 'Feb 2026', price: 1250 },
  ],
  relatedProducts: [
    { sku: 'CAB-002', name: 'XLPE Power Cable 4 Core 16 sq mm', price: 8500, brand: 'Polycab' },
    { sku: 'CAB-003', name: 'Armoured Cable 3.5 Core 25 sq mm', price: 14200, brand: 'Finolex' },
    { sku: 'ELC-001', name: 'MCB 32A Single Pole', price: 385, brand: 'ABB' },
  ],
};

export default function UserProductDetailPage() {
  const { sku } = useParams();
  const [activeTab, setActiveTab] = useState<'specs' | 'vendors' | 'history'>('specs');
  const [quantity, setQuantity] = useState(mockProduct.moq);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const product = { ...mockProduct, ...(sku ? { sku } : {}) };

  const firstPrice = product.priceHistory[0]!.price;
  const lastPrice = product.priceHistory[product.priceHistory.length - 1]!.price;
  const priceTrend = lastPrice < firstPrice ? 'falling' : lastPrice > firstPrice ? 'rising' : 'stable';
  const priceChange = ((lastPrice - firstPrice) / firstPrice * 100).toFixed(1);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      {/* Back nav */}
      <Link to="/user/catalog" className="inline-flex items-center gap-2 text-sm text-muted-silver hover:text-ghost-white transition-colors">
        <ArrowLeft size={16} />
        Back to Catalog
      </Link>

      {/* Product header */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Image */}
        <Card className="lg:col-span-1 flex items-center justify-center h-72">
          <div className="text-center">
            <Package size={64} className="text-muted-silver/20 mx-auto mb-3" />
            <p className="text-xs text-muted-silver">Product Image</p>
          </div>
        </Card>

        {/* Details */}
        <Card className="lg:col-span-2">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="soft" color="cyan" size="sm">{product.category}</Badge>
                <span className="text-xs text-muted-silver font-mono">{product.sku}</span>
              </div>
              <h1 className="text-xl font-bold text-ghost-white mb-1">{product.name}</h1>
              <p className="text-sm text-muted-silver">by <span className="text-electric-cyan">{product.brand}</span></p>
            </div>
            <button
              onClick={() => setIsWishlisted(!isWishlisted)}
              className="p-2 rounded-lg hover:bg-steel-slate/30 transition-colors"
            >
              <Heart size={20} className={isWishlisted ? 'text-coral-flame fill-coral-flame' : 'text-muted-silver'} />
            </button>
          </div>

          <p className="text-sm text-muted-silver mb-4 leading-relaxed">{product.description}</p>

          <div className="flex items-center gap-6 mb-4">
            <div className="flex items-center gap-1">
              <Star size={16} className="text-amber-glow fill-amber-glow" />
              <span className="text-sm text-ghost-white font-semibold">{product.rating}</span>
              <span className="text-xs text-muted-silver">({product.reviews} reviews)</span>
            </div>
            <span className={`flex items-center gap-1 text-xs ${product.inStock ? 'text-neon-emerald' : 'text-coral-flame'}`}>
              <span className={`w-2 h-2 rounded-full ${product.inStock ? 'bg-neon-emerald' : 'bg-coral-flame'}`} />
              {product.inStock ? `In Stock (${product.stockQty} units)` : 'Out of Stock'}
            </span>
          </div>

          {/* Pricing */}
          <div className="flex items-end gap-4 mb-4 p-4 rounded-xl bg-steel-slate/20">
            <div>
              <p className="text-xs text-muted-silver mb-1">Unit Price</p>
              <p className="text-2xl font-bold text-ghost-white">₹{product.price.toLocaleString()}</p>
              <p className="text-xs text-muted-silver">{product.unit}</p>
            </div>
            <div className="flex items-center gap-1.5">
              {priceTrend === 'falling' && <TrendingDown size={14} className="text-neon-emerald" />}
              {priceTrend === 'rising' && <TrendingUp size={14} className="text-coral-flame" />}
              {priceTrend === 'stable' && <Minus size={14} className="text-muted-silver" />}
              <span className={`text-xs font-medium ${priceTrend === 'falling' ? 'text-neon-emerald' : priceTrend === 'rising' ? 'text-coral-flame' : 'text-muted-silver'}`}>
                {priceChange}% from 6 months ago
              </span>
            </div>
          </div>

          {/* Quantity & Actions */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-xs text-muted-silver">Qty:</label>
              <div className="flex items-center border border-steel-slate/30 rounded-lg">
                <button
                  onClick={() => setQuantity(Math.max(product.moq, quantity - 1))}
                  className="px-3 py-1.5 text-muted-silver hover:text-ghost-white transition-colors"
                >-</button>
                <span className="px-3 py-1.5 text-sm text-ghost-white border-x border-steel-slate/30 min-w-[40px] text-center">{quantity}</span>
                <button
                  onClick={() => setQuantity(quantity + 1)}
                  className="px-3 py-1.5 text-muted-silver hover:text-ghost-white transition-colors"
                >+</button>
              </div>
              <span className="text-[10px] text-muted-silver">MOQ: {product.moq}</span>
            </div>
            <div className="flex gap-2">
              <Button variant="primary" leftIcon={<Receipt size={16} />}>
                Request Quote
              </Button>
              <Button variant="secondary" leftIcon={<ShoppingCart size={16} />}>
                Add to Request
              </Button>
            </div>
          </div>

          {/* Quick info */}
          <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-steel-slate/20">
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-muted-silver" />
              <span className="text-xs text-muted-silver">Lead Time: <span className="text-ghost-white">{product.leadTime} days</span></span>
            </div>
            <div className="flex items-center gap-2">
              <Building2 size={14} className="text-muted-silver" />
              <span className="text-xs text-muted-silver">Vendors: <span className="text-ghost-white">{product.vendors.length}</span></span>
            </div>
            <div className="flex items-center gap-2">
              <Shield size={14} className="text-muted-silver" />
              <span className="text-xs text-muted-silver">Certs: <span className="text-ghost-white">{product.certifications.length}</span></span>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-steel-slate/20">
        {(['specs', 'vendors', 'history'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors relative ${
              activeTab === tab ? 'text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'
            }`}
          >
            {tab === 'specs' ? 'Specifications' : tab === 'vendors' ? 'Vendor Options' : 'Price History'}
            {activeTab === tab && (
              <motion.div layoutId="product-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-electric-cyan rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'specs' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Technical Specifications</CardTitle>
            </CardHeader>
            <div className="space-y-2">
              {Object.entries(product.specifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between py-2 border-b border-steel-slate/10 last:border-0">
                  <span className="text-sm text-muted-silver">{key}</span>
                  <span className="text-sm text-ghost-white font-medium">{value}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Certifications</CardTitle>
            </CardHeader>
            <div className="flex flex-wrap gap-2">
              {product.certifications.map((cert) => (
                <Badge key={cert} variant="soft" color="emerald">{cert}</Badge>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'vendors' && (
        <Card>
          <CardHeader>
            <CardTitle>Available Vendors ({product.vendors.length})</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {product.vendors.map((vendor) => (
              <div key={vendor.id} className="flex items-center justify-between p-4 rounded-xl bg-steel-slate/10 hover:bg-steel-slate/20 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-electric-cyan/10 flex items-center justify-center">
                    <Building2 size={18} className="text-electric-cyan" />
                  </div>
                  <div>
                    <p className="text-sm text-ghost-white font-medium">{vendor.name}</p>
                    <div className="flex items-center gap-3 mt-0.5">
                      <Badge variant="soft" color={vendor.tier === 'platinum' ? 'silver' : vendor.tier === 'gold' ? 'amber' : 'cyan'} size="sm">
                        {vendor.tier}
                      </Badge>
                      <span className="flex items-center gap-1">
                        <Star size={10} className="text-amber-glow fill-amber-glow" />
                        <span className="text-xs text-ghost-white">{vendor.rating}</span>
                      </span>
                      <span className="text-xs text-muted-silver">On-time: {vendor.onTimeRate}%</span>
                    </div>
                  </div>
                </div>
                <div className="text-right flex items-center gap-4">
                  <div>
                    <p className="text-lg font-bold text-ghost-white">₹{vendor.price.toLocaleString()}</p>
                    <p className="text-[10px] text-muted-silver">Lead: {vendor.leadTime} days</p>
                  </div>
                  <Button variant="secondary" size="sm">Request Quote</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'history' && (
        <Card>
          <CardHeader>
            <CardTitle>Price Trend (6 Months)</CardTitle>
          </CardHeader>
          <div className="flex items-end gap-3 h-48 px-4 pb-4">
            {product.priceHistory.map((point, idx) => {
              const maxPrice = Math.max(...product.priceHistory.map((p) => p.price));
              const minPrice = Math.min(...product.priceHistory.map((p) => p.price));
              const range = maxPrice - minPrice || 1;
              const height = ((point.price - minPrice) / range) * 150 + 20;
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-[10px] text-muted-silver">₹{point.price}</span>
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height }}
                    transition={{ duration: 0.5, delay: idx * 0.1 }}
                    className="w-full rounded-t-lg bg-gradient-to-t from-electric-cyan/30 to-electric-cyan/60"
                  />
                  <span className="text-[10px] text-muted-silver">{point.date.split(' ')[0]}</span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Related Products */}
      <Card>
        <CardHeader>
          <CardTitle>Related Products</CardTitle>
        </CardHeader>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {product.relatedProducts.map((rp) => (
            <Link key={rp.sku} to={`/user/catalog/${rp.sku}`}>
              <div className="p-4 rounded-xl bg-steel-slate/10 hover:bg-steel-slate/20 transition-colors flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-steel-slate/30 flex items-center justify-center flex-shrink-0">
                  <Package size={18} className="text-muted-silver/40" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm text-ghost-white font-medium truncate">{rp.name}</p>
                  <p className="text-xs text-muted-silver">{rp.brand} · ₹{rp.price.toLocaleString()}</p>
                </div>
                <ChevronRight size={16} className="text-muted-silver flex-shrink-0" />
              </div>
            </Link>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}
