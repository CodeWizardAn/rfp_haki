import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Brain, TrendingUp, Target, AlertTriangle } from 'lucide-react';
import { Card, Badge } from '@/components/ui';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart } from 'recharts';

const forecasts = [
  { month: 'Mar', actual: null, predicted: 18, lower: 15, upper: 21 },
  { month: 'Apr', actual: null, predicted: 22, lower: 18, upper: 26 },
  { month: 'May', actual: null, predicted: 25, lower: 20, upper: 30 },
  { month: 'Jun', actual: null, predicted: 28, lower: 22, upper: 34 },
];

const historicalData = [
  { month: 'Sep', bidCount: 12, winRate: 42, avgValue: 85 },
  { month: 'Oct', bidCount: 15, winRate: 47, avgValue: 92 },
  { month: 'Nov', bidCount: 14, winRate: 44, avgValue: 88 },
  { month: 'Dec', bidCount: 18, winRate: 51, avgValue: 95 },
  { month: 'Jan', bidCount: 20, winRate: 48, avgValue: 102 },
  { month: 'Feb', bidCount: 22, winRate: 53, avgValue: 110 },
];

const predictions = [
  { metric: 'Expected RFPs (Q2)', value: '45-55', confidence: 82, trend: 'up' as const },
  { metric: 'Projected Win Rate', value: '54-58%', confidence: 75, trend: 'up' as const },
  { metric: 'Avg Bid Value (Q2)', value: '₹1.2-1.5Cr', confidence: 68, trend: 'up' as const },
  { metric: 'Expected Revenue', value: '₹28-35Cr', confidence: 71, trend: 'up' as const },
];

export default function PredictiveAnalyticsPage() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/analytics" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Predictive Analytics</h1><p className="text-body text-muted-silver">AI-powered forecasts and trend predictions</p></div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {predictions.map((p) => (
          <Card key={p.metric} variant="glass" className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Target size={14} className="text-electric-cyan" />
              <Badge variant="soft" color={p.confidence >= 80 ? 'emerald' : p.confidence >= 70 ? 'amber' : 'coral'} size="sm">{p.confidence}% conf</Badge>
            </div>
            <span className="text-lg font-bold text-ghost-white">{p.value}</span>
            <span className="text-xs text-muted-silver block mt-1">{p.metric}</span>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card variant="glass" className="p-5">
          <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><Brain size={14} className="text-violet-pulse" />Bid Volume Forecast</h3>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={[...historicalData.map((d) => ({ month: d.month, actual: d.bidCount, predicted: null, lower: null, upper: null })), ...forecasts]}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2642" />
              <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} />
              <YAxis tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} />
              <Tooltip contentStyle={{ background: '#121833', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '8px', color: '#E8ECF4', fontSize: 12 }} />
              <Area type="monotone" dataKey="upper" stroke="none" fill="#00D4FF" fillOpacity={0.05} />
              <Area type="monotone" dataKey="lower" stroke="none" fill="#0A0E27" fillOpacity={1} />
              <Line type="monotone" dataKey="actual" stroke="#00D4FF" strokeWidth={2} dot={{ fill: '#00D4FF', r: 4 }} connectNulls={false} />
              <Line type="monotone" dataKey="predicted" stroke="#7C3AED" strokeWidth={2} strokeDasharray="5 5" dot={{ fill: '#7C3AED', r: 4 }} connectNulls={false} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2 justify-center text-[10px] text-muted-silver">
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-electric-cyan" />Actual</span>
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-violet-pulse border-dashed" />Predicted</span>
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-electric-cyan/20" />Confidence Band</span>
          </div>
        </Card>

        <Card variant="glass" className="p-5">
          <h3 className="text-sm font-semibold text-ghost-white mb-4 flex items-center gap-2"><TrendingUp size={14} className="text-neon-emerald" />Win Rate Trend</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2642" />
              <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} />
              <YAxis tick={{ fill: '#8892B0', fontSize: 11 }} axisLine={false} domain={[30, 60]} />
              <Tooltip contentStyle={{ background: '#121833', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '8px', color: '#E8ECF4', fontSize: 12 }} formatter={(value) => typeof value === 'number' ? `${value}%` : ''} />
              <Line type="monotone" dataKey="winRate" stroke="#00E68A" strokeWidth={2} dot={{ fill: '#00E68A', r: 4 }} name="Win Rate" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card variant="glass" className="p-5">
        <h3 className="text-sm font-semibold text-ghost-white mb-3 flex items-center gap-2"><AlertTriangle size={14} className="text-amber-glow" />Risk Indicators</h3>
        <div className="grid grid-cols-3 gap-4">
          {[
            { risk: 'Vendor Concentration', level: 'Medium', desc: '60% of bids rely on top 3 vendors', color: 'amber' as const },
            { risk: 'Price Volatility', level: 'High', desc: 'Copper prices up 12% in 3 months', color: 'coral' as const },
            { risk: 'Compliance Gaps', level: 'Low', desc: '2 vendor certs expiring in 30 days', color: 'emerald' as const },
          ].map((r) => (
            <div key={r.risk} className="p-3 bg-deep-navy/40 rounded-lg">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-ghost-white">{r.risk}</span>
                <Badge variant="soft" color={r.color} size="sm">{r.level}</Badge>
              </div>
              <p className="text-[10px] text-muted-silver">{r.desc}</p>
            </div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}
