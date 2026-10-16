import { motion } from 'framer-motion';
import {
  FileText,
  Clock,
  CheckCircle2,
  TrendingUp,
} from 'lucide-react';

interface StatCard {
  label: string;
  value: string;
  change: string;
  changeType: 'up' | 'down';
  icon: React.ReactNode;
  color: string;
  sparkline: number[];
}

interface RFPStatsBarProps {
  totalRFPs?: number;
  analyzedCount?: number;
}

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 92;
  const h = 28;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(' ');

  const strokeColor =
    color === 'text-electric-cyan' ? '#2563EB' :
    color === 'text-amber-glow' ? '#D97706' :
    color === 'text-neon-emerald' ? '#059669' :
    '#7C3AED';

  return (
    <svg width={w} height={h} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={strokeColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function RFPStatsBar({ totalRFPs = 23, analyzedCount = 13 }: RFPStatsBarProps) {
  const dynamicTotal = totalRFPs;
  const successPct = dynamicTotal > 0 ? ((analyzedCount / dynamicTotal) * 100).toFixed(1) : '94.2';
  const thisMonthCount = Math.min(dynamicTotal, Math.max(1, Math.round(dynamicTotal * 0.78)));

  const stats: StatCard[] = [
    {
      label: 'Total RFPs',
      value: dynamicTotal.toString(),
      change: '+12.3%',
      changeType: 'up',
      icon: <FileText size={16} />,
      color: 'text-electric-cyan',
      sparkline: [20, 25, 22, 30, 28, 35, 32, 38, 42, dynamicTotal],
    },
    {
      label: 'Avg Processing',
      value: '3.2 min',
      change: '-18.5%',
      changeType: 'down',
      icon: <Clock size={16} />,
      color: 'text-amber-glow',
      sparkline: [5.2, 4.8, 4.5, 4.1, 3.8, 3.6, 3.5, 3.4, 3.2, 3.2],
    },
    {
      label: 'Success Rate',
      value: `${successPct}%`,
      change: '+2.1%',
      changeType: 'up',
      icon: <CheckCircle2 size={16} />,
      color: 'text-neon-emerald',
      sparkline: [88, 89, 90, 91, 90, 92, 93, 93, 94, 94],
    },
    {
      label: 'This Month',
      value: thisMonthCount.toString(),
      change: '+8 vs prev',
      changeType: 'up',
      icon: <TrendingUp size={16} />,
      color: 'text-violet-pulse',
      sparkline: [4, 6, 3, 5, 7, 4, 6, 8, 5, thisMonthCount],
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
        >
          <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-2xs hover:shadow-xs transition-all">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className={`p-1.5 rounded-lg bg-slate-50 border border-slate-100 ${stat.color}`}>
                    {stat.icon}
                  </span>
                  <span className="text-xs font-semibold text-slate-700">{stat.label}</span>
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight pt-1">{stat.value}</p>
                <div className="pt-0.5">
                  <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-md inline-flex items-center gap-0.5">
                    {stat.change}
                  </span>
                </div>
              </div>
              <div className="pt-2">
                <MiniSparkline data={stat.sparkline} color={stat.color} />
              </div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
