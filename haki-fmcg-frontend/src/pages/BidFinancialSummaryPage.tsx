import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, IndianRupee, TrendingUp, PieChart, BarChart3, Package, Percent } from 'lucide-react';
import { Card } from '@/components/ui';
import { PieChart as RPieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const costBreakdown = [
  { name: 'Material Cost', value: 62, color: '#00D4FF' },
  { name: 'Manufacturing', value: 15, color: '#00E68A' },
  { name: 'Logistics', value: 8, color: '#FFB224' },
  { name: 'Margin', value: 12, color: '#7C3AED' },
  { name: 'Taxes & Duties', value: 3, color: '#F472B6' },
];

const itemCosts = [
  { name: 'XLPE-240', material: 7650000, margin: 918000, total: 9335400 },
  { name: 'FR-25', material: 2016000, margin: 201600, total: 2419200 },
  { name: 'ARM-120', material: 2610000, margin: 391500, total: 3314250 },
  { name: 'TERM-240', material: 54000, margin: 10800, total: 77760 },
];

const summary = {
  totalRevenue: 15146610,
  totalCost: 12365400,
  grossProfit: 2781210,
  profitMargin: 18.4,
  taxLiability: 2726390,
  netTotal: 17873000,
};

const fmt = (n: number) => `₹${(n / 100000).toFixed(1)}L`;

export default function BidFinancialSummaryPage() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/bids" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Financial Summary</h1><p className="text-body text-muted-silver">BID-2026-0044 — Complete financial breakdown</p></div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { l: 'Total Revenue', v: fmt(summary.totalRevenue), icon: IndianRupee, c: 'text-electric-cyan' },
          { l: 'Gross Profit', v: fmt(summary.grossProfit), icon: TrendingUp, c: 'text-neon-emerald' },
          { l: 'Profit Margin', v: `${summary.profitMargin}%`, icon: Percent, c: 'text-amber-glow' },
          { l: 'Net Total (incl. GST)', v: fmt(summary.netTotal), icon: BarChart3, c: 'text-violet-pulse' },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-4">
            <s.icon size={16} className={`${s.c} mb-2`} />
            <span className="text-lg font-bold text-ghost-white">{s.v}</span>
            <span className="text-xs text-muted-silver block mt-1">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card variant="glass" className="p-5">
          <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><PieChart size={14} className="text-electric-cyan" />Cost Breakdown</h3>
          <ResponsiveContainer width="100%" height={220}>
            <RPieChart>
              <Pie data={costBreakdown} cx="50%" cy="50%" innerRadius={50} outerRadius={85} dataKey="value" strokeWidth={0}>
                {costBreakdown.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#121833', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '8px', color: '#E8ECF4', fontSize: 12 }} formatter={(value) => typeof value === 'number' ? `${value}%` : ''} />
            </RPieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 mt-2 justify-center">
            {costBreakdown.map((c) => (
              <span key={c.name} className="flex items-center gap-1 text-[10px] text-muted-silver"><span className="w-2 h-2 rounded-full" style={{ background: c.color }} />{c.name} ({c.value}%)</span>
            ))}
          </div>
        </Card>

        <Card variant="glass" className="p-5">
          <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><BarChart3 size={14} className="text-neon-emerald" />Item-wise Revenue</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={itemCosts}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2642" />
              <XAxis dataKey="name" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} />
              <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickFormatter={(v: number) => `₹${(v / 100000).toFixed(0)}L`} />
              <Tooltip contentStyle={{ background: '#121833', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '8px', color: '#E8ECF4', fontSize: 12 }} formatter={(value) => typeof value === 'number' ? fmt(value) : ''} />
              <Bar dataKey="material" fill="#00D4FF" radius={[4, 4, 0, 0]} name="Material" />
              <Bar dataKey="margin" fill="#7C3AED" radius={[4, 4, 0, 0]} name="Margin" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card variant="glass" className="p-5">
        <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><Package size={14} className="text-amber-glow" />Line Item Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-steel-slate/20">
                {['Item', 'Material Cost', 'Margin', 'GST (18%)', 'Total'].map((h) => (
                  <th key={h} className="px-4 py-2 text-left text-muted-silver font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {itemCosts.map((it) => (
                <tr key={it.name} className="border-b border-steel-slate/10">
                  <td className="px-4 py-3 text-ghost-white font-semibold">{it.name}</td>
                  <td className="px-4 py-3 text-ghost-white">{fmt(it.material)}</td>
                  <td className="px-4 py-3 text-neon-emerald">{fmt(it.margin)}</td>
                  <td className="px-4 py-3 text-amber-glow">{fmt(Math.round(it.total * 0.18))}</td>
                  <td className="px-4 py-3 text-ghost-white font-bold">{fmt(it.total)}</td>
                </tr>
              ))}
              <tr className="border-t-2 border-electric-cyan/20 font-bold">
                <td className="px-4 py-3 text-ghost-white">TOTAL</td>
                <td className="px-4 py-3 text-ghost-white">{fmt(itemCosts.reduce((a, i) => a + i.material, 0))}</td>
                <td className="px-4 py-3 text-neon-emerald">{fmt(itemCosts.reduce((a, i) => a + i.margin, 0))}</td>
                <td className="px-4 py-3 text-amber-glow">{fmt(summary.taxLiability)}</td>
                <td className="px-4 py-3 text-electric-cyan">{fmt(summary.netTotal)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
