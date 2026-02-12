import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Search,
  SlidersHorizontal,
  Grid3X3,
  List,
  Heart,
  ShoppingCart,
  Star,
  ChevronDown,
  Filter,
  X,
} from 'lucide-react';
import { Card, Badge, Button, Input } from '@/components/ui';

// --- Mock catalog data ---

const categories = ['All', 'Cables & Wires', 'FMCG', 'Safety Equipment', 'Electrical', 'Industrial', 'Office Supplies'];

const products = [
  { id: 1, sku: 'CAB-001', name: 'FR PVC Insulated Copper Cable 1.5 sq mm', category: 'Cables & Wires', brand: 'Havells', price: 1250, unit: 'per 100m', rating: 4.5, reviews: 128, inStock: true, image: null, specs: { 'Conductor': 'Copper', 'Size': '1.5 sq mm', 'Voltage': '1100V' } },
  { id: 2, sku: 'CAB-002', name: 'XLPE Power Cable 4 Core 16 sq mm', category: 'Cables & Wires', brand: 'Polycab', price: 8500, unit: 'per 100m', rating: 4.7, reviews: 89, inStock: true, image: null, specs: { 'Conductor': 'Copper', 'Cores': '4', 'Size': '16 sq mm' } },
  { id: 3, sku: 'FMCG-001', name: 'Premium Dishwash Liquid 5L', category: 'FMCG', brand: 'Harpic', price: 450, unit: 'per unit', rating: 4.2, reviews: 256, inStock: true, image: null, specs: { 'Volume': '5L', 'Type': 'Liquid' } },
  { id: 4, sku: 'FMCG-002', name: 'Industrial Hand Sanitizer 500ml', category: 'FMCG', brand: 'Dettol', price: 320, unit: 'per unit', rating: 4.0, reviews: 412, inStock: false, image: null, specs: { 'Volume': '500ml', 'Alcohol': '70%' } },
  { id: 5, sku: 'SAF-001', name: 'Industrial Safety Helmet ISI Mark', category: 'Safety Equipment', brand: 'Karam', price: 680, unit: 'per unit', rating: 4.8, reviews: 67, inStock: true, image: null, specs: { 'Standard': 'IS 2925', 'Material': 'HDPE' } },
  { id: 6, sku: 'ELC-001', name: 'MCB 32A Single Pole', category: 'Electrical', brand: 'ABB', price: 385, unit: 'per unit', rating: 4.6, reviews: 193, inStock: true, image: null, specs: { 'Rating': '32A', 'Poles': '1', 'Curve': 'C' } },
  { id: 7, sku: 'CAB-003', name: 'Armoured Cable 3.5 Core 25 sq mm', category: 'Cables & Wires', brand: 'Finolex', price: 14200, unit: 'per 100m', rating: 4.4, reviews: 45, inStock: true, image: null, specs: { 'Conductor': 'Aluminium', 'Cores': '3.5', 'Armour': 'Steel Wire' } },
  { id: 8, sku: 'IND-001', name: 'Hydraulic Pipe Fitting Set', category: 'Industrial', brand: 'Parker', price: 5600, unit: 'per set', rating: 4.3, reviews: 34, inStock: true, image: null, specs: { 'Material': 'SS304', 'Pressure': '400 bar' } },
  { id: 9, sku: 'OFF-001', name: 'A4 Copy Paper 80 GSM (5 Ream)', category: 'Office Supplies', brand: 'JK Copier', price: 1450, unit: 'per box', rating: 4.1, reviews: 589, inStock: true, image: null, specs: { 'GSM': '80', 'Sheets': '2500' } },
  { id: 10, sku: 'SAF-002', name: 'Cut-Resistant Gloves Level 5', category: 'Safety Equipment', brand: 'Ansell', price: 950, unit: 'per pair', rating: 4.9, reviews: 78, inStock: true, image: null, specs: { 'Level': '5', 'Material': 'HPPE + Glass Fiber' } },
  { id: 11, sku: 'ELC-002', name: 'RCCB 63A 4 Pole 30mA', category: 'Electrical', brand: 'Schneider', price: 2450, unit: 'per unit', rating: 4.7, reviews: 112, inStock: true, image: null, specs: { 'Rating': '63A', 'Sensitivity': '30mA', 'Poles': '4' } },
  { id: 12, sku: 'FMCG-003', name: 'Floor Cleaner Concentrate 5L', category: 'FMCG', brand: 'Lizol', price: 520, unit: 'per unit', rating: 4.3, reviews: 345, inStock: true, image: null, specs: { 'Volume': '5L', 'Dilution': '1:20' } },
];

const sortOptions = ['Relevance', 'Price: Low to High', 'Price: High to Low', 'Rating', 'Newest'];

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.04 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

export default function UserCatalogPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState('Relevance');
  const [showFilters, setShowFilters] = useState(false);
  const [wishlist, setWishlist] = useState<number[]>([]);

  const filteredProducts = products.filter((p) => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.brand.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || p.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const sortedProducts = [...filteredProducts].sort((a, b) => {
    if (sortBy === 'Price: Low to High') return a.price - b.price;
    if (sortBy === 'Price: High to Low') return b.price - a.price;
    if (sortBy === 'Rating') return b.rating - a.rating;
    return 0;
  });

  const toggleWishlist = (id: number) => {
    setWishlist((prev) => prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]);
  };

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* Page header */}
      <motion.div variants={fadeUp} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ghost-white">Product Catalog</h1>
          <p className="text-body text-muted-silver mt-1">
            Browse {products.length} products across {categories.length - 1} categories
          </p>
        </div>
      </motion.div>

      {/* Search & Controls */}
      <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[300px]">
          <Input
            placeholder="Search products by name, SKU, or brand..."
            leftIcon={<Search size={16} />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            rightIcon={
              searchQuery ? (
                <button onClick={() => setSearchQuery('')} className="hover:text-ghost-white">
                  <X size={14} />
                </button>
              ) : undefined
            }
          />
        </div>

        <Button
          variant={showFilters ? 'primary' : 'secondary'}
          size="sm"
          leftIcon={<Filter size={16} />}
          onClick={() => setShowFilters(!showFilters)}
        >
          Filters
        </Button>

        <div className="flex items-center gap-1 border border-steel-slate/30 rounded-lg p-0.5">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'}`}
          >
            <Grid3X3 size={16} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-1.5 rounded-md transition-colors ${viewMode === 'list' ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'}`}
          >
            <List size={16} />
          </button>
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="glass-input px-3 py-2 text-sm text-ghost-white bg-transparent rounded-lg border border-steel-slate/30"
        >
          {sortOptions.map((opt) => (
            <option key={opt} value={opt} className="bg-deep-navy">{opt}</option>
          ))}
        </select>
      </motion.div>

      {/* Category tabs */}
      <motion.div variants={fadeUp} className="flex flex-wrap gap-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
              selectedCategory === cat
                ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30'
                : 'bg-steel-slate/20 text-muted-silver hover:text-ghost-white border border-transparent'
            }`}
          >
            {cat}
          </button>
        ))}
      </motion.div>

      {/* Results count */}
      <div className="text-sm text-muted-silver">
        Showing <span className="text-ghost-white font-medium">{sortedProducts.length}</span> products
      </div>

      {/* Product Grid / List */}
      {viewMode === 'grid' ? (
        <motion.div variants={fadeUp} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {sortedProducts.map((product) => (
            <Card key={product.id} variant="interactive" className="flex flex-col">
              {/* Product image placeholder */}
              <div className="h-36 rounded-xl bg-steel-slate/30 flex items-center justify-center mb-4 relative">
                <ShoppingCart size={32} className="text-muted-silver/30" />
                <button
                  onClick={(e) => { e.preventDefault(); toggleWishlist(product.id); }}
                  className="absolute top-2 right-2 p-1.5 rounded-full bg-deep-navy/60 hover:bg-deep-navy/80 transition-colors"
                >
                  <Heart
                    size={16}
                    className={wishlist.includes(product.id) ? 'text-coral-flame fill-coral-flame' : 'text-muted-silver'}
                  />
                </button>
                {!product.inStock && (
                  <Badge variant="solid" color="coral" size="sm" className="absolute top-2 left-2">
                    Out of Stock
                  </Badge>
                )}
              </div>

              {/* Product info */}
              <div className="flex-1 flex flex-col">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="soft" color="cyan" size="sm">{product.category}</Badge>
                  <span className="text-[10px] text-muted-silver font-mono">{product.sku}</span>
                </div>
                <h3 className="text-sm font-semibold text-ghost-white leading-snug mb-1 line-clamp-2">
                  {product.name}
                </h3>
                <p className="text-xs text-muted-silver mb-2">{product.brand}</p>

                <div className="flex items-center gap-1 mb-3">
                  <Star size={12} className="text-amber-glow fill-amber-glow" />
                  <span className="text-xs text-ghost-white font-medium">{product.rating}</span>
                  <span className="text-[10px] text-muted-silver">({product.reviews})</span>
                </div>

                <div className="mt-auto">
                  <div className="flex items-end justify-between mb-3">
                    <div>
                      <p className="text-lg font-bold text-ghost-white">₹{product.price.toLocaleString()}</p>
                      <p className="text-[10px] text-muted-silver">{product.unit}</p>
                    </div>
                  </div>
                  <Link to={`/user/catalog/${product.sku}`}>
                    <Button variant="secondary" size="sm" className="w-full">
                      View Details
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </motion.div>
      ) : (
        <motion.div variants={fadeUp} className="space-y-3">
          {sortedProducts.map((product) => (
            <Link key={product.id} to={`/user/catalog/${product.sku}`}>
              <Card variant="interactive" className="flex items-center gap-4">
                <div className="w-20 h-20 rounded-xl bg-steel-slate/30 flex items-center justify-center flex-shrink-0">
                  <ShoppingCart size={24} className="text-muted-silver/30" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="soft" color="cyan" size="sm">{product.category}</Badge>
                    <span className="text-[10px] text-muted-silver font-mono">{product.sku}</span>
                    {!product.inStock && <Badge variant="solid" color="coral" size="sm">Out of Stock</Badge>}
                  </div>
                  <h3 className="text-sm font-semibold text-ghost-white truncate">{product.name}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-muted-silver">{product.brand}</span>
                    <span className="flex items-center gap-1">
                      <Star size={10} className="text-amber-glow fill-amber-glow" />
                      <span className="text-xs text-ghost-white">{product.rating}</span>
                    </span>
                  </div>
                </div>
                <div className="text-right flex items-center gap-4">
                  <div>
                    <p className="text-lg font-bold text-ghost-white">₹{product.price.toLocaleString()}</p>
                    <p className="text-[10px] text-muted-silver">{product.unit}</p>
                  </div>
                  <button
                    onClick={(e) => { e.preventDefault(); toggleWishlist(product.id); }}
                    className="p-2 rounded-lg hover:bg-steel-slate/30 transition-colors"
                  >
                    <Heart
                      size={18}
                      className={wishlist.includes(product.id) ? 'text-coral-flame fill-coral-flame' : 'text-muted-silver'}
                    />
                  </button>
                </div>
              </Card>
            </Link>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}
