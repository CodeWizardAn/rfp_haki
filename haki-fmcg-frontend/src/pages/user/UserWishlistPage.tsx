import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Heart,
  Trash2,
  ShoppingCart,
  Receipt,
  Package,
  Star,
  X,
} from 'lucide-react';
import { Card, Badge, Button } from '@/components/ui';

const wishlistItems = [
  { id: 1, sku: 'CAB-001', name: 'FR PVC Insulated Copper Cable 1.5 sq mm', category: 'Cables & Wires', brand: 'Havells', price: 1250, unit: 'per 100m', rating: 4.5, inStock: true, addedOn: '2026-02-05' },
  { id: 2, sku: 'ELC-001', name: 'MCB 32A Single Pole', category: 'Electrical', brand: 'ABB', price: 385, unit: 'per unit', rating: 4.6, inStock: true, addedOn: '2026-02-03' },
  { id: 3, sku: 'SAF-001', name: 'Industrial Safety Helmet ISI Mark', category: 'Safety Equipment', brand: 'Karam', price: 680, unit: 'per unit', rating: 4.8, inStock: true, addedOn: '2026-01-28' },
  { id: 4, sku: 'FMCG-002', name: 'Industrial Hand Sanitizer 500ml', category: 'FMCG', brand: 'Dettol', price: 320, unit: 'per unit', rating: 4.0, inStock: false, addedOn: '2026-01-25' },
  { id: 5, sku: 'CAB-002', name: 'XLPE Power Cable 4 Core 16 sq mm', category: 'Cables & Wires', brand: 'Polycab', price: 8500, unit: 'per 100m', rating: 4.7, inStock: true, addedOn: '2026-01-20' },
];

export default function UserWishlistPage() {
  const [items, setItems] = useState(wishlistItems);

  const removeItem = (id: number) => {
    setItems(items.filter((item) => item.id !== id));
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ghost-white">Wishlist</h1>
          <p className="text-body text-muted-silver mt-1">{items.length} saved products</p>
        </div>
        {items.length > 0 && (
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" leftIcon={<Receipt size={16} />}>
              Quote All
            </Button>
            <Button variant="primary" size="sm" leftIcon={<ShoppingCart size={16} />}>
              Add All to Request
            </Button>
          </div>
        )}
      </div>

      {items.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-16">
          <Heart size={48} className="text-muted-silver/20 mb-4" />
          <h3 className="text-lg font-semibold text-ghost-white mb-1">Your wishlist is empty</h3>
          <p className="text-sm text-muted-silver mb-4">Browse the catalog and save products for later</p>
          <Link to="/user/catalog">
            <Button variant="primary" leftIcon={<Package size={16} />}>Browse Catalog</Button>
          </Link>
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <motion.div
              key={item.id}
              layout
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
            >
              <Card variant="interactive">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-xl bg-steel-slate/30 flex items-center justify-center flex-shrink-0">
                    <Package size={24} className="text-muted-silver/30" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <Badge variant="soft" color="cyan" size="sm">{item.category}</Badge>
                      <span className="text-[10px] text-muted-silver font-mono">{item.sku}</span>
                      {!item.inStock && <Badge variant="solid" color="coral" size="sm">Out of Stock</Badge>}
                    </div>
                    <Link to={`/user/catalog/${item.sku}`}>
                      <h3 className="text-sm font-semibold text-ghost-white hover:text-electric-cyan transition-colors truncate">
                        {item.name}
                      </h3>
                    </Link>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-silver">
                      <span>{item.brand}</span>
                      <span className="flex items-center gap-1">
                        <Star size={10} className="text-amber-glow fill-amber-glow" />
                        {item.rating}
                      </span>
                      <span>Added: {item.addedOn}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-lg font-bold text-ghost-white">₹{item.price.toLocaleString()}</p>
                      <p className="text-[10px] text-muted-silver">{item.unit}</p>
                    </div>
                    <div className="flex flex-col gap-1">
                      <Button variant="secondary" size="xs" leftIcon={<Receipt size={12} />}>Quote</Button>
                      <button
                        onClick={() => removeItem(item.id)}
                        className="p-1.5 rounded-lg text-muted-silver hover:text-coral-flame hover:bg-coral-flame/10 transition-colors text-center"
                        title="Remove"
                      >
                        <Trash2 size={14} className="mx-auto" />
                      </button>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
