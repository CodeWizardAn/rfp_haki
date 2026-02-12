import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { Card, CardHeader, CardTitle } from '@/components/ui';

interface TrendChartProps {
  title: string;
  data: { date: string; value: number }[];
  color?: string;
  height?: number;
}

export function TrendChart({ title, data, color = '#00D4FF', height = 250 }: TrendChartProps) {
  return (
    <Card variant="glass">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id={`gradient-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,38,66,0.6)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#8892B0', fontSize: 12 }}
            axisLine={{ stroke: '#1E2642' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#8892B0', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: 'rgba(18, 24, 51, 0.9)',
              border: '1px solid rgba(0, 212, 255, 0.2)',
              borderRadius: '12px',
              backdropFilter: 'blur(12px)',
              color: '#E8ECF4',
              fontSize: '13px',
            }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#gradient-${color.replace('#', '')})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
