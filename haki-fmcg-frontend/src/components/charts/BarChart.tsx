import {
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Card, CardHeader, CardTitle } from '@/components/ui';

interface BarChartProps {
  title: string;
  data: Record<string, unknown>[];
  bars: { dataKey: string; color: string; name: string }[];
  xDataKey?: string;
  height?: number;
}

export function BarChart({ title, data, bars, xDataKey = 'month', height = 250 }: BarChartProps) {
  return (
    <Card variant="glass">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(30,38,66,0.6)" vertical={false} />
          <XAxis
            dataKey={xDataKey}
            tick={{ fill: '#8892B0', fontSize: 12 }}
            axisLine={{ stroke: '#1E2642' }}
            tickLine={false}
          />
          <YAxis tick={{ fill: '#8892B0', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              background: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#F8FAFC',
              fontSize: '12px',
              boxShadow: '0 8px 20px rgba(0, 0, 0, 0.35)',
            }}
            itemStyle={{ color: '#FFFFFF', fontWeight: 600, fontSize: '12px' }}
            labelStyle={{ color: '#94A3B8', fontWeight: 600, fontSize: '11px' }}
          />
          <Legend
            wrapperStyle={{ fontSize: '12px', color: '#8892B0' }}
          />
          {bars.map((bar) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              fill={bar.color}
              name={bar.name}
              radius={[4, 4, 0, 0]}
              barSize={28}
            />
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </Card>
  );
}
