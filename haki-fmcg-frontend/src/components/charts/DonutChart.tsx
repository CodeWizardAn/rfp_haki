import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';
import { Card, CardHeader, CardTitle } from '@/components/ui';
import { formatCompactCurrency } from '@/utils/formatters';

interface DonutChartProps {
  title: string;
  data: { name: string; value: number; color: string }[];
  centerLabel?: string;
  centerValue?: string;
  height?: number;
}

export function DonutChart({ title, data, centerLabel, centerValue, height = 250 }: DonutChartProps) {
  return (
    <Card variant="glass">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <div className="relative">
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={90}
              paddingAngle={3}
              dataKey="value"
              animationBegin={0}
              animationDuration={800}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.color} stroke="transparent" />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: 'rgba(18, 24, 51, 0.9)',
                border: '1px solid rgba(0, 212, 255, 0.2)',
                borderRadius: '12px',
                color: '#E8ECF4',
                fontSize: '13px',
              }}
              formatter={(value: unknown) => formatCompactCurrency(Number(value))}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Center text */}
        {(centerLabel || centerValue) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            {centerValue && (
              <span className="text-xl font-bold text-ghost-white">{centerValue}</span>
            )}
            {centerLabel && (
              <span className="text-xs text-muted-silver">{centerLabel}</span>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-2 px-1">
        {data.map((entry, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-xs text-muted-silver">{entry.name}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
