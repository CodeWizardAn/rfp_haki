import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  Clock,
  CheckCircle2,
  Cpu,
  Activity,
  ChevronDown,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';

/* ─── agent execution times ─── */
const agentTimes = [
  { agent: 'Sales', avg: 2.4, p95: 4.1, color: '#00D4FF' },
  { agent: 'Pricing', avg: 3.1, p95: 5.8, color: '#00E68A' },
  { agent: 'Technical', avg: 4.7, p95: 8.2, color: '#FFB224' },
  { agent: 'Master', avg: 1.8, p95: 3.0, color: '#7C3AED' },
];

/* ─── success rate over 7 days ─── */
const successTrend = [
  { day: 'Mon', sales: 96, pricing: 92, technical: 88, master: 100 },
  { day: 'Tue', sales: 94, pricing: 95, technical: 90, master: 98 },
  { day: 'Wed', sales: 100, pricing: 88, technical: 85, master: 100 },
  { day: 'Thu', sales: 92, pricing: 94, technical: 92, master: 96 },
  { day: 'Fri', sales: 98, pricing: 96, technical: 94, master: 100 },
  { day: 'Sat', sales: 100, pricing: 98, technical: 96, master: 100 },
  { day: 'Sun', sales: 96, pricing: 92, technical: 90, master: 100 },
];

/* ─── last 20 executions ─── */
interface Execution {
  id: string;
  agent: string;
  status: 'success' | 'failed' | 'timeout';
  duration: string;
  timestamp: string;
  task: string;
}

const recentExecutions: Execution[] = [
  { id: 'EX-20', agent: 'Sales', status: 'success', duration: '2.1s', timestamp: '2 min ago', task: 'Product matching for RFP-2025-178' },
  { id: 'EX-19', agent: 'Pricing', status: 'success', duration: '3.4s', timestamp: '5 min ago', task: 'Price optimization batch #42' },
  { id: 'EX-18', agent: 'Technical', status: 'failed', duration: '8.2s', timestamp: '8 min ago', task: 'Spec comparison RFP-2025-177' },
  { id: 'EX-17', agent: 'Master', status: 'success', duration: '1.6s', timestamp: '12 min ago', task: 'Orchestrate pipeline run #891' },
  { id: 'EX-16', agent: 'Sales', status: 'success', duration: '2.8s', timestamp: '15 min ago', task: 'Vendor scoring update' },
  { id: 'EX-15', agent: 'Pricing', status: 'timeout', duration: '30.0s', timestamp: '18 min ago', task: 'Bulk price recalculation' },
  { id: 'EX-14', agent: 'Technical', status: 'success', duration: '5.1s', timestamp: '22 min ago', task: 'Compliance check RFP-2025-176' },
  { id: 'EX-13', agent: 'Master', status: 'success', duration: '1.2s', timestamp: '25 min ago', task: 'Orchestrate pipeline run #890' },
  { id: 'EX-12', agent: 'Sales', status: 'success', duration: '1.9s', timestamp: '30 min ago', task: 'Product matching for RFP-2025-175' },
  { id: 'EX-11', agent: 'Pricing', status: 'success', duration: '2.7s', timestamp: '35 min ago', task: 'Dynamic pricing update' },
];

const glassTooltip = {
  contentStyle: {
    background: 'rgba(18,24,51,0.92)',
    border: '1px solid rgba(0,212,255,0.15)',
    borderRadius: 10,
    color: '#E8ECF4',
    fontSize: 12,
  },
  cursor: { stroke: 'rgba(0,212,255,0.25)' },
};

const statusConfig = {
  success: { color: 'text-neon-emerald', bg: 'bg-neon-emerald/10', label: 'Success' },
  failed:  { color: 'text-coral-flame', bg: 'bg-coral-flame/10', label: 'Failed' },
  timeout: { color: 'text-amber-glow', bg: 'bg-amber-glow/10', label: 'Timeout' },
};

const agentColors: Record<string, string> = {
  Sales: 'text-electric-cyan',
  Pricing: 'text-neon-emerald',
  Technical: 'text-amber-glow',
  Master: 'text-violet-pulse',
};

export default function AgentPerformancePanel() {
  const [showAll, setShowAll] = useState(false);
  const visibleExecs = showAll ? recentExecutions : recentExecutions.slice(0, 5);

  const successRate = Math.round(
    (recentExecutions.filter((e) => e.status === 'success').length / recentExecutions.length) * 100
  );

  return (
    <div className="space-y-4">
      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Avg Response', value: '3.0s', icon: Clock, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10' },
          { label: 'Success Rate', value: `${successRate}%`, icon: CheckCircle2, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10' },
          { label: 'Active Agents', value: '4/4', icon: Cpu, color: 'text-violet-pulse', bg: 'bg-violet-pulse/10' },
          { label: 'Total Runs', value: '891', icon: Activity, color: 'text-amber-glow', bg: 'bg-amber-glow/10' },
        ].map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-card rounded-xl p-3 flex items-center gap-3"
            >
              <div className={`w-9 h-9 rounded-lg ${s.bg} flex items-center justify-center`}>
                <Icon size={16} className={s.color} />
              </div>
              <div>
                <p className="text-lg font-bold text-ghost-white leading-none">{s.value}</p>
                <p className="text-[10px] text-muted-silver">{s.label}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Execution Time by Agent */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Avg Execution Time by Agent</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={agentTimes} barSize={20}>
                <XAxis dataKey="agent" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} unit="s" />
                <Tooltip {...glassTooltip} />
                <Bar dataKey="avg" radius={[4, 4, 0, 0]}>
                  {agentTimes.map((d) => (
                    <motion.rect key={d.agent} fill={d.color} />
                  ))}
                </Bar>
                <Bar dataKey="p95" radius={[4, 4, 0, 0]} opacity={0.3}>
                  {agentTimes.map((d) => (
                    <motion.rect key={d.agent} fill={d.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            <span className="flex items-center gap-1 text-[10px] text-muted-silver">
              <span className="w-2 h-2 rounded-full bg-electric-cyan" />Avg
            </span>
            <span className="flex items-center gap-1 text-[10px] text-muted-silver">
              <span className="w-2 h-2 rounded-full bg-electric-cyan/30" />P95
            </span>
          </div>
        </Card>

        {/* Success Rate Trend */}
        <Card variant="glass">
          <CardHeader><CardTitle className="text-sm">Success Rate Trend (7 days)</CardTitle></CardHeader>
          <div className="px-4 pb-4 h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={successTrend}>
                <XAxis dataKey="day" tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892B0', fontSize: 10 }} axisLine={false} tickLine={false} domain={[80, 100]} unit="%" />
                <Tooltip {...glassTooltip} />
                <Line type="monotone" dataKey="sales" stroke="#00D4FF" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="pricing" stroke="#00E68A" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="technical" stroke="#FFB224" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="master" stroke="#7C3AED" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 pb-3">
            {agentTimes.map((a) => (
              <span key={a.agent} className="flex items-center gap-1 text-[10px] text-muted-silver">
                <span className="w-2 h-2 rounded-full" style={{ background: a.color }} />{a.agent}
              </span>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Executions Table */}
      <Card variant="glass">
        <CardHeader><CardTitle className="text-sm">Recent Executions</CardTitle></CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-steel-slate/20">
                <th className="py-2 px-3 text-left text-[10px] font-semibold text-muted-silver uppercase">Agent</th>
                <th className="py-2 px-3 text-left text-[10px] font-semibold text-muted-silver uppercase">Task</th>
                <th className="py-2 px-3 text-center text-[10px] font-semibold text-muted-silver uppercase">Status</th>
                <th className="py-2 px-3 text-center text-[10px] font-semibold text-muted-silver uppercase">Duration</th>
                <th className="py-2 px-3 text-right text-[10px] font-semibold text-muted-silver uppercase">Time</th>
              </tr>
            </thead>
            <tbody>
              {visibleExecs.map((ex, i) => {
                const sc = statusConfig[ex.status];
                return (
                  <motion.tr
                    key={ex.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    className="border-b border-steel-slate/10 hover:bg-steel-slate/10 transition-colors"
                  >
                    <td className="py-2 px-3">
                      <span className={`text-xs font-medium ${agentColors[ex.agent] || 'text-ghost-white'}`}>{ex.agent}</span>
                    </td>
                    <td className="py-2 px-3">
                      <span className="text-xs text-muted-silver truncate block max-w-[220px]">{ex.task}</span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <Badge variant="soft" color={ex.status === 'success' ? 'teal' : ex.status === 'failed' ? 'red' : 'amber'} size="sm">
                        {sc.label}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className="text-xs font-mono text-ghost-white">{ex.duration}</span>
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className="text-[10px] text-muted-silver">{ex.timestamp}</span>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {recentExecutions.length > 5 && (
          <button
            onClick={() => setShowAll((s) => !s)}
            className="w-full py-2 flex items-center justify-center gap-1 text-xs text-electric-cyan hover:text-electric-cyan/80 transition-colors"
          >
            {showAll ? 'Show Less' : `Show All ${recentExecutions.length}`}
            <ChevronDown size={12} className={`transition-transform ${showAll ? 'rotate-180' : ''}`} />
          </button>
        )}
      </Card>
    </div>
  );
}
