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
              background: 'rgba(18, 24, 51, 0.9)',
              border: '1px solid rgba(0, 212, 255, 0.2)',
              borderRadius: '12px',
              color: '#E8ECF4',
              fontSize: '13px',
            }}
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
