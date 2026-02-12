import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import {
  ArrowLeft,
  Plus,
  X,
  Trophy,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';

/* ─── types ─── */
interface VendorMetrics {
  id: string;
  name: string;
  color: string;
  overall: number;
  delivery: number;
  quality: number;
  response: number;
  compliance: number;
  price: number;
  bidsWon: number;
  avgLeadTime: string;
  defectRate: string;
  onTimeRate: string;
  certifications: string[];
}

/* ─── data ─── */
const allVendors: VendorMetrics[] = [
  { id: 'v1', name: 'Finolex', color: '#3B82F6', overall: 95, delivery: 98, quality: 92, response: 89, compliance: 97, price: 85, bidsWon: 24, avgLeadTime: '4.2 wks', defectRate: '0.3%', onTimeRate: '98%', certifications: ['ISO 9001', 'ISO 14001', 'BIS', 'NABL'] },
  { id: 'v2', name: 'Havells', color: '#EF4444', overall: 88, delivery: 85, quality: 90, response: 92, compliance: 94, price: 78, bidsWon: 18, avgLeadTime: '5.1 wks', defectRate: '0.8%', onTimeRate: '92%', certifications: ['ISO 9001', 'BIS', 'ISI'] },
  { id: 'v3', name: 'Polycab', color: '#F97316', overall: 91, delivery: 90, quality: 94, response: 86, compliance: 92, price: 88, bidsWon: 21, avgLeadTime: '4.8 wks', defectRate: '0.5%', onTimeRate: '95%', certifications: ['ISO 9001', 'ISO 14001', 'BIS'] },
  { id: 'v4', name: 'KEI', color: '#22C55E', overall: 82, delivery: 78, quality: 86, response: 80, compliance: 88, price: 92, bidsWon: 12, avgLeadTime: '6.0 wks', defectRate: '1.2%', onTimeRate: '85%', certifications: ['ISO 9001', 'BIS'] },
  { id: 'v5', name: 'RR Kabel', color: '#A855F7', overall: 79, delivery: 82, quality: 80, response: 75, compliance: 85, price: 90, bidsWon: 9, avgLeadTime: '5.5 wks', defectRate: '1.5%', onTimeRate: '88%', certifications: ['ISO 9001', 'BIS'] },
];

const metrics = ['delivery', 'quality', 'response', 'compliance', 'price'] as const;
const metricLabels: Record<string, string> = { delivery: 'Delivery', quality: 'Quality', response: 'Response', compliance: 'Compliance', price: 'Price' };

const glassTooltip = {
  contentStyle: {
    background: 'rgba(18,24,51,0.92)',
    border: '1px solid rgba(0,212,255,0.15)',
    borderRadius: 10,
    color: '#E8ECF4',
    fontSize: 12,
  },
};

export default function VendorComparisonPage() {
  const [selected, setSelected] = useState<string[]>(['v1', 'v2', 'v3']);
  const [showPicker, setShowPicker] = useState(false);

  const vendors = allVendors.filter((v) => selected.includes(v.id));
  const available = allVendors.filter((v) => !selected.includes(v.id));

  const radarData = metrics.map((m) => {
    const row: Record<string, string | number> = { metric: metricLabels[m] ?? m };
    vendors.forEach((v) => { row[v.id] = v[m]; });
    return row;
  });

  const overallData = vendors.map((v) => ({ name: v.name, score: v.overall, color: v.color }));

  const addVendor = (id: string) => {
    if (selected.length < 5) {
      setSelected((p) => [...p, id]);
      setShowPicker(false);
    }
  };

  const removeVendor = (id: string) => {
    if (selected.length > 2) setSelected((p) => p.filter((x) => x !== id));
  };

  const best = (metric: typeof metrics[number]) => {
    let bestId = '';
    let bestVal = 0;
    vendors.forEach((v) => { if (v[metric] > bestVal) { bestVal = v[metric]; bestId = v.id; } });
    return bestId;
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Vendor Comparison</h1>
            <p className="text-body text-muted-silver">Side-by-side performance analysis</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-silver">{selected.length}/5 selected</span>
          {available.length > 0 && selected.length < 5 && (
            <div className="relative">
              <Button variant="secondary" size="sm" leftIcon={<Plus size={12} />} onClick={() => setShowPicker(!showPicker)}>Add</Button>
              {showPicker && (
                <div className="absolute right-0 mt-1 w-48 glass-card rounded-lg border border-steel-slate/20 py-1 z-20">
                  {available.map((v) => (
                    <button key={v.id} onClick={() => addVendor(v.id)} className="w-full text-left px-3 py-1.5 text-xs text-ghost-white hover:bg-steel-slate/15 transition-colors flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ background: v.color }} />
                      {v.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Selected Vendor Tags */}
      <div className="flex flex-wrap gap-2">
        {vendors.map((v) => (
          <motion.div
            key={v.id}
            layout
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="flex items-center gap-2 glass-card rounded-xl px-3 py-2"
          >
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: v.color }} />
            <span className="text-sm font-semibold text-ghost-white">{v.name}</span>
            <span className="text-xs text-muted-silver">Score: {v.overall}</span>
            {selected.length > 2 && (
              <button onClick={() => removeVendor(v.id)} className="p-0.5 rounded hover:bg-steel-slate/20 transition-colors">
                <X size={12} className="text-muted-silver" />
              </button>
            )}
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Radar Comparison */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Performance Radar</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(136,146,176,0.15)" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#8892B0', fontSize: 10 }} />
                <PolarRadiusAxis tick={{ fill: '#8892B0', fontSize: 8 }} domain={[60, 100]} />
                {vendors.map((v) => (
                  <Radar key={v.id} name={v.name} dataKey={v.id} stroke={v.color} fill={v.color} fillOpacity={0.08} strokeWidth={2} />
                ))}
                <Tooltip {...glassTooltip} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            {vendors.map((v) => (
              <div key={v.id} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: v.color }} />
                <span className="text-[10px] text-muted-silver">{v.name}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Overall Score */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Overall Score Comparison</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overallData} barSize={28}>
                <XAxis dataKey="name" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} domain={[60, 100]} />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="score" radius={[6, 6, 0, 0]}>
                  {overallData.map((d) => <Cell key={d.name} fill={d.color} fillOpacity={0.7} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Detailed Metrics Table */}
      <Card variant="glass">
        <CardHeader><CardTitle className="text-sm">Detailed Metrics Comparison</CardTitle></CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-steel-slate/15 text-muted-silver">
                <th className="text-left p-2.5 pl-4">Metric</th>
                {vendors.map((v) => (
                  <th key={v.id} className="text-center p-2.5">
                    <div className="flex items-center justify-center gap-1">
                      <span className="w-2 h-2 rounded-full" style={{ background: v.color }} />
                      {v.name}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Score Rows */}
              {metrics.map((m) => {
                const bestId = best(m);
                return (
                  <tr key={m} className="border-b border-steel-slate/8">
                    <td className="p-2.5 pl-4 text-ghost-white font-medium">{metricLabels[m]}</td>
                    {vendors.map((v) => (
                      <td key={v.id} className="text-center p-2.5">
                        <span className={`font-mono font-semibold ${v.id === bestId ? 'text-neon-emerald' : 'text-ghost-white'}`}>
                          {v[m]}
                        </span>
                        {v.id === bestId && <Trophy size={10} className="text-neon-emerald inline ml-1" />}
                      </td>
                    ))}
                  </tr>
                );
              })}
              {/* Stats */}
              <tr className="border-b border-steel-slate/8">
                <td className="p-2.5 pl-4 text-ghost-white font-medium">Bids Won</td>
                {vendors.map((v) => <td key={v.id} className="text-center p-2.5 text-ghost-white font-mono">{v.bidsWon}</td>)}
              </tr>
              <tr className="border-b border-steel-slate/8">
                <td className="p-2.5 pl-4 text-ghost-white font-medium">Avg Lead Time</td>
                {vendors.map((v) => <td key={v.id} className="text-center p-2.5 text-ghost-white">{v.avgLeadTime}</td>)}
              </tr>
              <tr className="border-b border-steel-slate/8">
                <td className="p-2.5 pl-4 text-ghost-white font-medium">Defect Rate</td>
                {vendors.map((v) => {
                  const val = parseFloat(v.defectRate);
                  return (
                    <td key={v.id} className={`text-center p-2.5 font-mono ${val <= 0.5 ? 'text-neon-emerald' : val <= 1 ? 'text-amber-glow' : 'text-coral-flame'}`}>
                      {v.defectRate}
                    </td>
                  );
                })}
              </tr>
              <tr className="border-b border-steel-slate/8">
                <td className="p-2.5 pl-4 text-ghost-white font-medium">On-Time Delivery</td>
                {vendors.map((v) => {
                  const val = parseInt(v.onTimeRate);
                  return (
                    <td key={v.id} className={`text-center p-2.5 font-mono ${val >= 95 ? 'text-neon-emerald' : val >= 90 ? 'text-amber-glow' : 'text-coral-flame'}`}>
                      {v.onTimeRate}
                    </td>
                  );
                })}
              </tr>
              {/* Certifications */}
              <tr>
                <td className="p-2.5 pl-4 text-ghost-white font-medium">Certifications</td>
                {vendors.map((v) => (
                  <td key={v.id} className="text-center p-2.5">
                    <div className="flex flex-wrap justify-center gap-1">
                      {v.certifications.map((c) => <Badge key={c} variant="soft" color="cyan" size="sm">{c}</Badge>)}
                    </div>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
