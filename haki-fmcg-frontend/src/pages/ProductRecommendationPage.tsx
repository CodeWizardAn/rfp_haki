import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Lightbulb, TrendingUp, Star, ShoppingCart, ShieldCheck, ChevronRight, Loader2 } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface Recommendation {
  sku: string;
  name: string;
  category: string;
  matchScore: number;
  reason: string;
  price: number;
  priceUnit: string;
  savings?: number;
  brand?: string;
}

const defaultTabs = [
  'Top Recommendations',
  'Cost-Effective Alternatives',
  'Frequently Bought Together',
  'Critical & Fire Safety'
] as const;

const fallbackRecommendations: Record<string, Recommendation[]> = {
  'Top Recommendations': [
    { sku: 'POL-PVC-2.5-R', name: 'Polycab Optima Plus PVC Wire 2.5 sq mm', category: 'PVC Insulated Wire', matchScore: 96, reason: 'Top IS 694 & IS 8130 compliant ETP copper wire; optimal conductivity', price: 28, priceUnit: '/m', brand: 'Polycab' },
    { sku: 'HAV-XLPE-4C-16', name: 'Havells XLPE Armoured Power Cable 4 Core 16 sq mm', category: 'XLPE Armoured Cable', matchScore: 94, reason: 'Heavy duty power distribution with steel wire armouring & IS 7098 compliance', price: 890, priceUnit: '/m', brand: 'Havells' },
    { sku: 'KEI-FLX-3C-2.5', name: 'KEI Conflame Flexible Copper Cable 3 Core 2.5 sq mm', category: 'Flexible Cable', matchScore: 91, reason: 'Class 5 highly flexible annealed copper with flame-retardant PVC sheath', price: 68, priceUnit: '/m', brand: 'KEI' },
    { sku: 'FIN-PVC-4.0-R', name: 'Finolex Industrial PVC Cable 4.0 sq mm', category: 'PVC Insulated Wire', matchScore: 89, reason: 'High temperature resistant Class 2 stranded conductor for motor feeders', price: 46, priceUnit: '/m', brand: 'Finolex' },
    { sku: 'CAB-001', name: 'XLPE Insulated HV Cable 33kV 3×185mm²', category: 'HV Cables', matchScore: 95, reason: 'High voltage XLPE cable for primary substations & IEC 60502 compliance', price: 4250, priceUnit: '/m', brand: 'Polycab' },
  ],
  'Cost-Effective Alternatives': [
    { sku: 'ALU-XLPE-185', name: 'Aluminium XLPE Power Cable 185mm² 3.5 Core', category: 'Power Cables', matchScore: 86, reason: 'High electrical capacity equivalent at 38% material cost reduction', price: 1450, priceUnit: '/m', savings: 850, brand: 'KEI' },
    { sku: 'ALU-XLPE-240', name: 'Aluminium XLPE Power Cable 240mm² 3 Core', category: 'Power Cables', matchScore: 88, reason: 'Same continuous current rating with significant bulk procurement savings', price: 1720, priceUnit: '/m', savings: 1100, brand: 'Polycab' },
    { sku: 'POL-PVC-1.5-R', name: 'Polycab Optima Plus PVC Wire 1.5 sq mm', category: 'PVC Insulated Wire', matchScore: 82, reason: 'Value-engineered gauge for low-draw lighting circuits meeting IS 694', price: 19, priceUnit: '/m', savings: 9, brand: 'Polycab' },
  ],
  'Frequently Bought Together': [
    { sku: 'ACC-TERM-240', name: 'Heat Shrink Termination Kit 11kV/33kV', category: 'Accessories', matchScore: 0, reason: 'Essential termination accessory for XLPE armoured cables', price: 4800, priceUnit: '/kit', brand: 'Raychem' },
    { sku: 'ACC-JOINT-240', name: 'Straight Through Jointing Kit 1.1kV-11kV', category: 'Accessories', matchScore: 0, reason: 'Resin-filled jointing kit for underground cable runs', price: 6400, priceUnit: '/kit', brand: '3M' },
    { sku: 'ACC-LUG-240', name: 'Heavy Duty Copper Compression Lugs (Pack of 10)', category: 'Accessories', matchScore: 0, reason: 'High conductivity ETP copper lugs compliant with IS 8309', price: 1350, priceUnit: '/pack', brand: 'Dowells' },
    { sku: 'ACC-GLAND-01', name: 'Double Compression Weatherproof Brass Cable Glands (Pack 5)', category: 'Accessories', matchScore: 0, reason: 'IP66 rated mechanical retention & earth continuity for armoured cables', price: 1950, priceUnit: '/pack', brand: 'Comet' },
  ],
  'Critical & Fire Safety': [
    { sku: 'RRK-FRLS-1.5-R', name: 'RR Kabel Superex FR-LSH Fire Survival Wire 1.5 sq mm', category: 'Fire Resistant', matchScore: 94, reason: 'Low smoke zero halogen; ideal for hospitals, data centers & public safety', price: 32, priceUnit: '/m', brand: 'RR Kabel' },
    { sku: 'CAB-003', name: 'Armoured Power Cable 11kV 3×95mm²', category: 'MV Cables', matchScore: 92, reason: 'Medium voltage armoured cable with galvanized steel wire protection', price: 2150, priceUnit: '/m', brand: 'Havells' },
  ]
};

export default function ProductRecommendationPage() {
  const [tabs, setTabs] = useState<string[]>([...defaultTabs]);
  const [activeTab, setActiveTab] = useState<string>(defaultTabs[0]);
  const [recommendationsData, setRecommendationsData] = useState<Record<string, Recommendation[]>>(fallbackRecommendations);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const fetchRecommendations = async () => {
      try {
        const token = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${baseUrl}/api/v1/products/recommendations`, { headers });
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const json = await res.json();
        const payload = json?.data ?? json;

        if (isMounted && payload?.recommendations) {
          setRecommendationsData(payload.recommendations);
          if (payload.tabs && Array.isArray(payload.tabs) && payload.tabs.length > 0) {
            setTabs(payload.tabs);
            if (!payload.tabs.includes(activeTab)) {
              setActiveTab(payload.tabs[0]);
            }
          }
        }
      } catch (err) {
        console.warn('[ProductRecommendationPage] Using built-in dynamic catalog recommendations:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchRecommendations();
    return () => { isMounted = false; };
  }, []);

  const items = recommendationsData[activeTab] ?? fallbackRecommendations[activeTab] ?? [];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/products" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
          <ArrowLeft size={18} className="text-muted-silver" />
        </Link>
        <div>
          <h1 className="text-h1 text-ghost-white">Product Recommendations</h1>
          <p className="text-body text-muted-silver">AI-powered OEM product suggestions, cost-effective alternatives & accessories</p>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className={`px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-colors ${
              activeTab === t
                ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30'
                : 'text-muted-silver hover:text-ghost-white border border-transparent hover:bg-steel-slate/10'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="p-12 text-center flex flex-col items-center justify-center gap-3 text-muted-silver">
          <Loader2 className="animate-spin text-electric-cyan" size={28} />
          <p className="text-sm">Fetching real-time product recommendations from catalog...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="p-12 text-center text-muted-silver border border-steel-slate/15 rounded-xl">
          <p>No recommendations currently available for this category.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item, i) => (
            <motion.div key={item.sku} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
              <Link to={`/products/${item.sku}`}>
                <Card variant="glass" className="p-4 flex items-center gap-4 hover:bg-steel-slate/10 hover:border-electric-cyan/30 transition-all group">
                  <div className="w-12 h-12 rounded-xl bg-electric-cyan/10 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
                    {activeTab.includes('Top') || activeTab.includes('RFP') ? (
                      <Star size={20} className="text-electric-cyan" />
                    ) : activeTab.includes('Together') || activeTab.includes('Accessory') ? (
                      <ShoppingCart size={20} className="text-amber-glow" />
                    ) : activeTab.includes('Safety') ? (
                      <ShieldCheck size={20} className="text-neon-emerald" />
                    ) : (
                      <TrendingUp size={20} className="text-neon-emerald" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-ghost-white group-hover:text-electric-cyan transition-colors">{item.name}</h3>
                      {item.brand && (
                        <span className="text-[10px] text-muted-silver border border-steel-slate/20 rounded px-1.5 py-0.5">
                          {item.brand}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-silver mt-0.5 flex items-center gap-1">
                      <Lightbulb size={12} className="text-amber-glow flex-shrink-0" />
                      <span>{item.reason}</span>
                    </p>
                    <div className="flex flex-wrap gap-2 mt-1.5">
                      <Badge variant="soft" color="cyan" size="sm">{item.sku}</Badge>
                      <Badge variant="soft" color="teal" size="sm">{item.category}</Badge>
                      {item.matchScore > 0 && (
                        <Badge variant="soft" color={item.matchScore >= 90 ? 'emerald' : 'cyan'} size="sm">
                          {item.matchScore}% Match Score
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="text-sm font-bold text-ghost-white">
                      ₹{item.price.toLocaleString('en-IN')}
                      <span className="text-[10px] text-muted-silver font-normal">{item.priceUnit}</span>
                    </span>
                    {item.savings && (
                      <span className="text-[10px] text-neon-emerald block font-medium">
                        Save ₹{item.savings.toLocaleString('en-IN')}{item.priceUnit}
                      </span>
                    )}
                  </div>
                  <ChevronRight size={16} className="text-muted-silver/30 group-hover:text-electric-cyan group-hover:translate-x-0.5 transition-all" />
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
