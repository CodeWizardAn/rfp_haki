import { motion } from 'framer-motion';
import {
  FileText,
  Clock,
  CheckCircle2,
  TrendingUp,
} from 'lucide-react';
import { Card } from '@/components/ui';

interface StatCard {
  label: string;
  value: string;
  change: string;
  changeType: 'up' | 'down';
  icon: React.ReactNode;
  color: string;
  sparkline: number[];
}

const stats: StatCard[] = [
  {
    label: 'Total RFPs',
    value: '247',
    change: '+12.3%',
    changeType: 'up',
    icon: <FileText size={16} />,
    color: 'text-electric-cyan',
    sparkline: [20, 25, 22, 30, 28, 35, 32, 38, 42, 47],
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
    value: '94.2%',
    change: '+2.1%',
    changeType: 'up',
    icon: <CheckCircle2 size={16} />,
    color: 'text-neon-emerald',
    sparkline: [88, 89, 90, 91, 90, 92, 93, 93, 94, 94],
  },
  {
    label: 'This Month',
    value: '38',
    change: '+8 vs prev',
    changeType: 'up',
    icon: <TrendingUp size={16} />,
    color: 'text-violet-pulse',
    sparkline: [4, 6, 3, 5, 7, 4, 6, 8, 5, 7],
  },
];

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 80;
  const h = 24;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(' ');

  const strokeColor =
    color === 'text-electric-cyan' ? '#00D4FF' :
    color === 'text-amber-glow' ? '#FFB224' :
    color === 'text-neon-emerald' ? '#00E68A' :
    '#7C3AED';

  return (
    <svg width={w} height={h} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function RFPStatsBar() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
        >
          <Card variant="glass">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={stat.color}>{stat.icon}</span>
                  <span className="text-xs text-muted-silver">{stat.label}</span>
                </div>
                <p className="text-xl font-bold text-ghost-white">{stat.value}</p>
                <span className={`text-[10px] font-medium ${
                  stat.changeType === 'up' ? 'text-neon-emerald' : 'text-neon-emerald'
                }`}>
                  {stat.change}
                </span>
              </div>
              <MiniSparkline data={stat.sparkline} color={stat.color} />
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
