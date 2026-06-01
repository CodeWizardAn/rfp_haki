import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Lightbulb, TrendingUp, Star, ShoppingCart, ChevronRight } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface Recommendation { sku: string; name: string; category: string; matchScore: number; reason: string; price: number; priceUnit: string; savings?: number; }

const tabs = ['For RFP-2026-0044', 'Frequently Bought Together', 'Cost-Effective Alternatives'] as const;

const recommendations: Record<string, Recommendation[]> = {
  'For RFP-2026-0044': [
    { sku: 'HAK-XLPE-240', name: 'XLPE Power Cable 240mm²', category: 'Power Cables', matchScore: 94, reason: 'Best match for voltage & current specs', price: 2450, priceUnit: '/m' },
    { sku: 'HAK-FR-25', name: 'Fire Resistant Cable 25mm²', category: 'Fire Resistant', matchScore: 91, reason: 'Meets FR-LSH requirement from clause 4.2', price: 1680, priceUnit: '/m' },
    { sku: 'HAK-ARM-120', name: 'Armoured Cable 120mm²', category: 'Armoured', matchScore: 82, reason: 'Suitable for underground installation', price: 1450, priceUnit: '/m' },
  ],
  'Frequently Bought Together': [
    { sku: 'HAK-TERM-240', name: 'Heat Shrink Termination Kit 240mm²', category: 'Accessories', matchScore: 0, reason: 'Usually ordered with XLPE-240', price: 4500, priceUnit: '/pc' },
    { sku: 'HAK-JNT-240', name: 'Straight Joint Kit 240mm²', category: 'Accessories', matchScore: 0, reason: 'Required for cable jointing', price: 6200, priceUnit: '/pc' },
    { sku: 'HAK-LUG-240', name: 'Compression Lugs 240mm² (Pack 10)', category: 'Accessories', matchScore: 0, reason: 'Copper compression type', price: 1200, priceUnit: '/pack' },
  ],
  'Cost-Effective Alternatives': [
    { sku: 'HAK-XLPE-185', name: 'XLPE Power Cable 185mm²', category: 'Power Cables', matchScore: 78, reason: 'Meets 80% specs at lower cost', price: 1890, priceUnit: '/m', savings: 560 },
    { sku: 'HAK-ALU-240', name: 'Aluminium XLPE 240mm²', category: 'Power Cables', matchScore: 88, reason: 'Same size, aluminium conductor', price: 1650, priceUnit: '/m', savings: 800 },
    { sku: 'HAK-PVC-240', name: 'PVC Power Cable 240mm²', category: 'Power Cables', matchScore: 72, reason: 'PVC insulation alternative', price: 1980, priceUnit: '/m', savings: 470 },
  ],
};

export default function ProductRecommendationPage() {
  const [activeTab, setActiveTab] = useState<string>(tabs[0]);
  const items = recommendations[activeTab] ?? [];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/products" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Product Recommendations</h1><p className="text-body text-muted-silver">AI-powered product suggestions and alternatives</p></div>
      </div>

      <div className="flex gap-2">
        {tabs.map((t) => (
          <button key={t} onClick={() => setActiveTab(t)} className={`px-4 py-2 rounded-lg text-sm transition-colors ${activeTab === t ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30' : 'text-muted-silver hover:text-ghost-white border border-transparent'}`}>{t}</button>
        ))}
      </div>

      <div className="space-y-3">
        {items.map((item, i) => (
          <motion.div key={item.sku} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Link to={`/products/${item.sku}`}>
              <Card variant="glass" className="p-4 flex items-center gap-4 hover:bg-steel-slate/5 transition-colors group">
                <div className="w-12 h-12 rounded-xl bg-electric-cyan/10 flex items-center justify-center flex-shrink-0">
                  {activeTab.includes('RFP') ? <Star size={20} className="text-electric-cyan" /> : activeTab.includes('Together') ? <ShoppingCart size={20} className="text-amber-glow" /> : <TrendingUp size={20} className="text-neon-emerald" />}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-ghost-white">{item.name}</h3>
                  <p className="text-xs text-muted-silver mt-0.5 flex items-center gap-1"><Lightbulb size={10} className="text-amber-glow" />{item.reason}</p>
                  <div className="flex gap-2 mt-1">
                    <Badge variant="soft" color="cyan" size="sm">{item.sku}</Badge>
                    <Badge variant="soft" color="teal" size="sm">{item.category}</Badge>
                    {item.matchScore > 0 && <Badge variant="soft" color={item.matchScore >= 85 ? 'emerald' : 'amber'} size="sm">{item.matchScore}% match</Badge>}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <span className="text-sm font-bold text-ghost-white">₹{item.price.toLocaleString('en-IN')}<span className="text-[10px] text-muted-silver font-normal">{item.priceUnit}</span></span>
                  {item.savings && <span className="text-[10px] text-neon-emerald block">Save ₹{item.savings.toLocaleString('en-IN')}{item.priceUnit}</span>}
                </div>
                <ChevronRight size={16} className="text-muted-silver/30 group-hover:text-electric-cyan transition-colors" />
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
