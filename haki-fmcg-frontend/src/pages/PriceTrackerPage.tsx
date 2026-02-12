import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown, IndianRupee, Package } from 'lucide-react';
import { Card, Badge } from '@/components/ui';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const products = [
  { sku: 'HAK-XLPE-240', name: 'XLPE 240mm²', currentPrice: 2450, change: 3.2, history: [
    { month: 'Sep', price: 2280 }, { month: 'Oct', price: 2310 }, { month: 'Nov', price: 2340 },
    { month: 'Dec', price: 2380 }, { month: 'Jan', price: 2420 }, { month: 'Feb', price: 2450 },
  ]},
  { sku: 'HAK-XLPE-400', name: 'XLPE 400mm²', currentPrice: 3120, change: 5.1, history: [
    { month: 'Sep', price: 2890 }, { month: 'Oct', price: 2920 }, { month: 'Nov', price: 2980 },
    { month: 'Dec', price: 3010 }, { month: 'Jan', price: 3060 }, { month: 'Feb', price: 3120 },
  ]},
  { sku: 'HAK-PVC-16', name: 'PVC Control 16-core', currentPrice: 890, change: -1.5, history: [
    { month: 'Sep', price: 920 }, { month: 'Oct', price: 910 }, { month: 'Nov', price: 905 },
    { month: 'Dec', price: 900 }, { month: 'Jan', price: 895 }, { month: 'Feb', price: 890 },
  ]},
  { sku: 'HAK-FR-25', name: 'FR Cable 25mm²', currentPrice: 1680, change: 8.4, history: [
    { month: 'Sep', price: 1480 }, { month: 'Oct', price: 1510 }, { month: 'Nov', price: 1560 },
    { month: 'Dec', price: 1590 }, { month: 'Jan', price: 1640 }, { month: 'Feb', price: 1680 },
  ]},
];

export default function PriceTrackerPage() {
  const [selected, setSelected] = useState(products[0]?.sku ?? '');
  const prod = products.find((p) => p.sku === selected) ?? products[0];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/products" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Price Tracker</h1><p className="text-body text-muted-silver">Historical pricing trends and forecasts</p></div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {products.map((p) => (
          <Card key={p.sku} variant="glass" className={`p-3 cursor-pointer transition-all ${selected === p.sku ? 'ring-1 ring-electric-cyan/40' : 'hover:bg-steel-slate/5'}`} onClick={() => setSelected(p.sku)}>
            <div className="flex items-center justify-between mb-1">
              <Package size={14} className="text-electric-cyan" />
              {p.change >= 0 ? <TrendingUp size={14} className="text-neon-emerald" /> : <TrendingDown size={14} className="text-coral-flame" />}
            </div>
            <h3 className="text-xs font-semibold text-ghost-white truncate">{p.name}</h3>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-sm font-bold text-ghost-white">₹{p.currentPrice.toLocaleString('en-IN')}</span>
              <span className={`text-[10px] ${p.change >= 0 ? 'text-neon-emerald' : 'text-coral-flame'}`}>{p.change >= 0 ? '+' : ''}{p.change}%</span>
            </div>
          </Card>
        ))}
      </div>

      {prod && (
        <Card variant="glass" className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-ghost-white">{prod.name}</h3>
              <p className="text-xs text-muted-silver">{prod.sku} · 6-month price history</p>
            </div>
            <div className="flex items-center gap-2">
              <IndianRupee size={14} className="text-electric-cyan" />
              <span className="text-xl font-bold text-ghost-white">₹{prod.currentPrice.toLocaleString('en-IN')}/m</span>
              <Badge variant="soft" color={prod.change >= 0 ? 'emerald' : 'coral'} size="sm">{prod.change >= 0 ? '+' : ''}{prod.change}%</Badge>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={prod.history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2642" />
              <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} />
              <YAxis tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} domain={['dataMin - 50', 'dataMax + 50']} />
              <Tooltip contentStyle={{ background: '#121833', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '8px', color: '#E8ECF4', fontSize: 12 }} />
              <Line type="monotone" dataKey="price" stroke="#00D4FF" strokeWidth={2} dot={{ fill: '#00D4FF', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-4 gap-4 mt-4 text-xs">
            {[
              { l: '6M Low', v: `₹${Math.min(...prod.history.map((h) => h.price)).toLocaleString('en-IN')}` },
              { l: '6M High', v: `₹${Math.max(...prod.history.map((h) => h.price)).toLocaleString('en-IN')}` },
              { l: '6M Avg', v: `₹${Math.round(prod.history.reduce((a, h) => a + h.price, 0) / prod.history.length).toLocaleString('en-IN')}` },
              { l: 'Volatility', v: prod.change > 5 ? 'High' : prod.change > 2 ? 'Medium' : 'Low' },
            ].map((s) => (
              <div key={s.l} className="text-center">
                <span className="text-muted-silver block">{s.l}</span>
                <span className="text-ghost-white font-semibold">{s.v}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </motion.div>
  );
}
