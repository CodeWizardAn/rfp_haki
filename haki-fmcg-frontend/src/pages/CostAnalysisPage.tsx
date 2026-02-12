import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, IndianRupee, TrendingDown, BarChart3, PieChart as PieIcon, Calculator } from 'lucide-react';
import { Card, Badge } from '@/components/ui';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell } from 'recharts';

const monthlyCosts = [
  { month: 'Sep', material: 85, logistics: 12, overhead: 8, total: 105 },
  { month: 'Oct', material: 92, logistics: 14, overhead: 8, total: 114 },
  { month: 'Nov', material: 88, logistics: 11, overhead: 9, total: 108 },
  { month: 'Dec', material: 95, logistics: 15, overhead: 9, total: 119 },
  { month: 'Jan', material: 102, logistics: 13, overhead: 10, total: 125 },
  { month: 'Feb', material: 110, logistics: 16, overhead: 10, total: 136 },
];

const categoryBreakdown = [
  { name: 'Power Cables', value: 45, color: '#00D4FF' },
  { name: 'Control Cables', value: 20, color: '#00E68A' },
  { name: 'Fire Resistant', value: 15, color: '#FFB224' },
  { name: 'Instrumentation', value: 12, color: '#7C3AED' },
  { name: 'Accessories', value: 8, color: '#F472B6' },
];

const savingsOpps = [
  { area: 'Bulk Purchase Consolidation', potential: '₹12.5L/quarter', impact: 'high' as const, desc: 'Combine XLPE orders across 3 RFPs for volume discount' },
  { area: 'Vendor Renegotiation', potential: '₹8.2L/quarter', impact: 'medium' as const, desc: 'Renegotiate with KEI Industries based on increased volume' },
  { area: 'Specification Optimization', potential: '₹5.4L/quarter', impact: 'medium' as const, desc: 'Replace over-specified cables where standard grade suffices' },
  { area: 'Logistics Optimization', potential: '₹3.1L/quarter', impact: 'low' as const, desc: 'Consolidate shipments to reduce per-unit freight cost' },
];

const impactColor: Record<string, 'coral' | 'amber' | 'cyan'> = { high: 'coral', medium: 'amber', low: 'cyan' };

export default function CostAnalysisPage() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/analytics" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Cost Analysis</h1><p className="text-body text-muted-silver">Procurement cost breakdown and savings opportunities</p></div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { l: 'Total Spend (6M)', v: '₹7.07Cr', icon: IndianRupee, c: 'text-electric-cyan' },
          { l: 'Avg Monthly', v: '₹1.18Cr', icon: Calculator, c: 'text-amber-glow' },
          { l: 'MoM Change', v: '+8.8%', icon: BarChart3, c: 'text-coral-flame' },
          { l: 'Savings Found', v: '₹29.2L/Qtr', icon: TrendingDown, c: 'text-neon-emerald' },
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
          <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><BarChart3 size={14} className="text-electric-cyan" />Monthly Cost Trend (₹ Lakhs)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={monthlyCosts}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2642" />
              <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} />
              <YAxis tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} />
              <Tooltip contentStyle={{ background: '#121833', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '8px', color: '#E8ECF4', fontSize: 12 }} />
              <Bar dataKey="material" stackId="a" fill="#00D4FF" name="Material" radius={[0, 0, 0, 0]} />
              <Bar dataKey="logistics" stackId="a" fill="#FFB224" name="Logistics" />
              <Bar dataKey="overhead" stackId="a" fill="#7C3AED" name="Overhead" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card variant="glass" className="p-5">
          <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><PieIcon size={14} className="text-neon-emerald" />Spend by Category</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={categoryBreakdown} cx="50%" cy="50%" innerRadius={50} outerRadius={85} dataKey="value" strokeWidth={0}>
                {categoryBreakdown.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#121833', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '8px', color: '#E8ECF4', fontSize: 12 }} formatter={(value) => typeof value === 'number' ? `${value}%` : ''} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 mt-2 justify-center">
            {categoryBreakdown.map((c) => (
              <span key={c.name} className="flex items-center gap-1 text-[10px] text-muted-silver"><span className="w-2 h-2 rounded-full" style={{ background: c.color }} />{c.name}</span>
            ))}
          </div>
        </Card>
      </div>

      <Card variant="glass" className="p-5">
        <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><TrendingDown size={14} className="text-neon-emerald" />Savings Opportunities</h3>
        <div className="space-y-3">
          {savingsOpps.map((opp, i) => (
            <motion.div key={opp.area} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-4 p-3 bg-deep-navy/40 rounded-lg">
              <Badge variant="soft" color={impactColor[opp.impact]} size="sm">{opp.impact}</Badge>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-ghost-white">{opp.area}</h4>
                <p className="text-[10px] text-muted-silver">{opp.desc}</p>
              </div>
              <span className="text-sm font-bold text-neon-emerald">{opp.potential}</span>
            </motion.div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}
