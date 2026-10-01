import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Trophy,
  Star,
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowLeft,
  Download,
  Building2,
  Award,
  Medal,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';

interface RankedVendor {
  id: string;
  name: string;
  score: number;
  prevScore: number;
  rating: number;
  badge: string;
  bidsWon: number;
  bidsTotal: number;
  onTimeRate: number;
  qualityScore: number;
  trend: 'up' | 'down' | 'stable';
  category: string;
}

const vendors: RankedVendor[] = [
  { id: 'VND-001', name: 'Havells India Ltd', score: 92, prevScore: 89, rating: 4.7, badge: 'Gold', bidsWon: 24, bidsTotal: 35, onTimeRate: 96, qualityScore: 93, trend: 'up', category: 'OEM' },
  { id: 'VND-002', name: 'Polycab India Ltd', score: 91, prevScore: 91, rating: 4.6, badge: 'Gold', bidsWon: 22, bidsTotal: 30, onTimeRate: 94, qualityScore: 95, trend: 'stable', category: 'OEM' },
  { id: 'VND-003', name: 'KEI Industries Ltd', score: 86, prevScore: 84, rating: 4.3, badge: 'Silver', bidsWon: 18, bidsTotal: 28, onTimeRate: 90, qualityScore: 88, trend: 'up', category: 'OEM' },
  { id: 'VND-004', name: 'Finolex Cables Ltd', score: 84, prevScore: 86, rating: 4.2, badge: 'Silver', bidsWon: 15, bidsTotal: 25, onTimeRate: 88, qualityScore: 90, trend: 'down', category: 'OEM' },
  { id: 'VND-005', name: 'RR Kabel Ltd', score: 80, prevScore: 78, rating: 4.0, badge: 'Silver', bidsWon: 12, bidsTotal: 22, onTimeRate: 85, qualityScore: 86, trend: 'up', category: 'OEM' },
  { id: 'VND-006', name: 'Moglix Industrial Supply', score: 75, prevScore: 76, rating: 3.8, badge: 'Bronze', bidsWon: 8, bidsTotal: 18, onTimeRate: 82, qualityScore: 80, trend: 'down', category: 'Distributor' },
  { id: 'VND-007', name: 'IndiaMART Sellers', score: 68, prevScore: 65, rating: 3.5, badge: 'Bronze', bidsWon: 5, bidsTotal: 15, onTimeRate: 78, qualityScore: 74, trend: 'up', category: 'Marketplace' },
  { id: 'VND-008', name: 'Trade India Vendor', score: 62, prevScore: 64, rating: 3.2, badge: 'Bronze', bidsWon: 3, bidsTotal: 12, onTimeRate: 72, qualityScore: 70, trend: 'down', category: 'Marketplace' },
];

const badgeColors: Record<string, { color: string; bg: string; icon: React.ReactNode }> = {
  Gold:   { color: 'text-amber-glow', bg: 'bg-amber-glow/10', icon: <Trophy size={14} /> },
  Silver: { color: 'text-muted-silver', bg: 'bg-steel-slate/15', icon: <Medal size={14} /> },
  Bronze: { color: 'text-amber-glow/60', bg: 'bg-amber-glow/5', icon: <Award size={14} /> },
};

const trendIcon = (t: 'up' | 'down' | 'stable') =>
  t === 'up' ? <TrendingUp size={12} className="text-neon-emerald" /> :
  t === 'down' ? <TrendingDown size={12} className="text-coral-flame" /> :
  <Minus size={12} className="text-muted-silver" />;

export default function VendorRankingsPage() {
  const [timeRange, setTimeRange] = useState('90d');
  const [categoryFilter, setCategoryFilter] = useState('All');

  const categories = ['All', ...Array.from(new Set(vendors.map((v) => v.category)))];
  const filtered = categoryFilter === 'All' ? vendors : vendors.filter((v) => v.category === categoryFilter);

  const handleExportRankings = () => {
    const headers = 'Rank,Vendor ID,Name,Category,Score,Rating,Badge,Bids Won,Total Bids,On-Time Rate,Quality Score';
    const rows = filtered.map((v, i) =>
      `${i + 1},"${v.id}","${v.name}","${v.category}",${v.score},${v.rating},"${v.badge}",${v.bidsWon},${v.bidsTotal},${v.onTimeRate}%,${v.qualityScore}%`
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `haki_vendor_rankings_${timeRange}_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success(`Exported ${filtered.length} ranked vendors to CSV!`);
  };

  // Top 3 podium
  const top3 = filtered.slice(0, 3);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div className="p-2 rounded-xl bg-amber-glow/10">
            <Trophy size={24} className="text-amber-glow" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Vendor Rankings</h1>
            <p className="text-body text-muted-silver">Performance leaderboard across all vendors</p>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
            {['30d', '90d', '180d', '1y'].map((r) => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  timeRange === r ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
          <Button variant="secondary" leftIcon={<Download size={14} />} onClick={handleExportRankings}>
            Export
          </Button>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategoryFilter(cat)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
              categoryFilter === cat
                ? 'bg-electric-cyan/10 border-electric-cyan/40 text-electric-cyan'
                : 'bg-steel-slate/10 border-steel-slate/20 text-muted-silver hover:border-steel-slate/40'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Podium */}
      {top3.length >= 3 && (
        <div className="flex items-end justify-center gap-4 py-6">
          {[top3[1], top3[0], top3[2]].map((v, podiumIdx) => {
            if (!v) return null;
            const rank = podiumIdx === 0 ? 2 : podiumIdx === 1 ? 1 : 3;
            const heights = [120, 160, 100];
            const bc = badgeColors[v.badge] ?? badgeColors.Bronze;
            return (
              <motion.div
                key={v.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: podiumIdx * 0.15 }}
                className="flex flex-col items-center"
              >
                <Link to={`/vendors/${v.id}`} className="flex flex-col items-center group">
                  <div className={`w-14 h-14 rounded-2xl ${bc?.bg ?? ''} flex items-center justify-center mb-2 group-hover:scale-105 transition-transform`}>
                    <Building2 size={22} className={bc?.color ?? 'text-muted-silver'} />
                  </div>
                  <p className="text-sm font-semibold text-ghost-white text-center">{v.name.split(' ')[0]}</p>
                  <p className="text-2xl font-bold text-ghost-white">{v.score}</p>
                  <div className="flex items-center gap-1 my-1">
                    {trendIcon(v.trend)}
                    <span className="text-[10px] text-muted-silver">
                      {v.score > v.prevScore ? `+${v.score - v.prevScore}` : v.score < v.prevScore ? `${v.score - v.prevScore}` : '—'}
                    </span>
                  </div>
                </Link>
                <div
                  className={`w-24 rounded-t-xl flex items-center justify-center ${
                    rank === 1 ? 'bg-amber-glow/20' : rank === 2 ? 'bg-steel-slate/20' : 'bg-amber-glow/10'
                  }`}
                  style={{ height: heights[podiumIdx] }}
                >
                  <span className={`text-4xl font-black ${rank === 1 ? 'text-amber-glow' : 'text-muted-silver'}`}>
                    {rank}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Rankings Table */}
      <Card variant="glass" className="overflow-x-auto">
        <CardHeader><CardTitle>Full Rankings</CardTitle></CardHeader>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-steel-slate/20">
              <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase w-12">#</th>
              <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase">Vendor</th>
              <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Score</th>
              <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Trend</th>
              <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Rating</th>
              <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Win Rate</th>
              <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">On-Time</th>
              <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Quality</th>
              <th className="py-2 px-4 text-center text-xs font-semibold text-muted-silver uppercase">Badge</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((v, idx) => {
              const bc = badgeColors[v.badge] || badgeColors.Bronze;
              const winRate = Math.round((v.bidsWon / v.bidsTotal) * 100);
              return (
                <motion.tr
                  key={v.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.03 }}
                  className="border-b border-steel-slate/10 hover:bg-steel-slate/10 transition-colors cursor-pointer"
                >
                  <td className="py-3 px-4">
                    <span className={`text-sm font-bold ${idx < 3 ? 'text-amber-glow' : 'text-muted-silver'}`}>{idx + 1}</span>
                  </td>
                  <td className="py-3 px-4">
                    <Link to={`/vendors/${v.id}`} className="flex items-center gap-2 hover:text-electric-cyan transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-steel-slate/20 flex items-center justify-center flex-shrink-0">
                        <Building2 size={14} className="text-muted-silver" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-ghost-white">{v.name}</p>
                        <p className="text-[10px] text-muted-silver">{v.category}</p>
                      </div>
                    </Link>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-sm font-bold text-ghost-white">{v.score}</span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {trendIcon(v.trend)}
                      <span className={`text-xs ${
                        v.trend === 'up' ? 'text-neon-emerald' : v.trend === 'down' ? 'text-coral-flame' : 'text-muted-silver'
                      }`}>
                        {v.score > v.prevScore ? `+${v.score - v.prevScore}` : v.score < v.prevScore ? `${v.score - v.prevScore}` : '—'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <Star size={11} className="text-amber-glow fill-amber-glow" />
                      <span className="text-xs text-ghost-white">{v.rating}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-xs text-ghost-white">{winRate}%</span>
                    <span className="text-[10px] text-muted-silver ml-1">({v.bidsWon}/{v.bidsTotal})</span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <div className="w-12 h-1.5 bg-steel-slate/20 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${v.onTimeRate >= 90 ? 'bg-neon-emerald' : v.onTimeRate >= 80 ? 'bg-amber-glow' : 'bg-coral-flame'}`} style={{ width: `${v.onTimeRate}%` }} />
                      </div>
                      <span className="text-xs text-muted-silver">{v.onTimeRate}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="text-xs text-muted-silver">{v.qualityScore}%</span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <Badge variant="soft" color={v.badge === 'Gold' ? 'amber' : v.badge === 'Silver' ? 'silver' : 'teal'} size="sm">
                      <span className="mr-1">{bc?.icon}</span>{v.badge}
                    </Badge>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </motion.div>
  );
}
