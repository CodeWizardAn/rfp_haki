import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Activity, Heart, Cpu, HardDrive, Wifi, XCircle, RefreshCw } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface HealthItem { agent: string; status: 'healthy' | 'degraded' | 'down'; uptime: string; cpu: number; memory: number; lastPing: string; tasks: number; errors24h: number; }

const healthData: HealthItem[] = [
  { agent: 'Master Agent', status: 'healthy', uptime: '14d 6h 32m', cpu: 12, memory: 34, lastPing: '2s ago', tasks: 3, errors24h: 0 },
  { agent: 'Sales Agent', status: 'healthy', uptime: '14d 6h 30m', cpu: 28, memory: 45, lastPing: '1s ago', tasks: 1, errors24h: 2 },
  { agent: 'Technical Agent', status: 'degraded', uptime: '2d 4h 12m', cpu: 78, memory: 82, lastPing: '5s ago', tasks: 4, errors24h: 8 },
  { agent: 'Pricing Agent', status: 'healthy', uptime: '14d 6h 28m', cpu: 15, memory: 29, lastPing: '1s ago', tasks: 2, errors24h: 1 },
];

const sColor: Record<string, { text: string; bg: string; badge: 'emerald' | 'amber' | 'coral' }> = {
  healthy: { text: 'text-neon-emerald', bg: 'bg-neon-emerald', badge: 'emerald' },
  degraded: { text: 'text-amber-glow', bg: 'bg-amber-glow', badge: 'amber' },
  down: { text: 'text-coral-flame', bg: 'bg-coral-flame', badge: 'coral' },
};

function Bar({ value, max = 100, color }: { value: number; max?: number; color: string }) {
  return (
    <div className="h-2 rounded-full bg-steel-slate/20 overflow-hidden w-full">
      <motion.div initial={{ width: 0 }} animate={{ width: `${(value / max) * 100}%` }} transition={{ duration: 0.6 }} className={`h-full rounded-full ${color}`} />
    </div>
  );
}

export default function AgentHealthCheckPage() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/agents" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Agent Health Check</h1><p className="text-body text-muted-silver">Real-time health status and resource monitoring</p></div>
        </div>
        <button className="flex items-center gap-2 text-sm text-electric-cyan hover:text-electric-cyan/80"><RefreshCw size={14} />Refresh All</button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { l: 'Overall Health', v: '95%', icon: Heart, c: 'text-neon-emerald' },
          { l: 'Agents Online', v: `${healthData.filter((h) => h.status !== 'down').length}/${healthData.length}`, icon: Wifi, c: 'text-electric-cyan' },
          { l: 'Active Tasks', v: healthData.reduce((a, h) => a + h.tasks, 0).toString(), icon: Activity, c: 'text-amber-glow' },
          { l: 'Errors (24h)', v: healthData.reduce((a, h) => a + h.errors24h, 0).toString(), icon: XCircle, c: 'text-coral-flame' },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-4">
            <s.icon size={16} className={`${s.c} mb-2`} />
            <span className="text-xl font-bold text-ghost-white">{s.v}</span>
            <span className="text-xs text-muted-silver block mt-1">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {healthData.map((h) => {
          const sc = (sColor[h.status] ?? sColor['degraded'])!;
          return (
            <Card key={h.agent} variant="glass" className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${sc.bg} ${h.status === 'healthy' ? 'animate-pulse' : ''}`} />
                  <h3 className="text-sm font-semibold text-ghost-white">{h.agent}</h3>
                </div>
                <Badge variant="soft" color={sc.badge}>{h.status}</Badge>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div><span className="text-muted-silver block mb-1"><Cpu size={10} className="inline mr-1" />CPU</span><Bar value={h.cpu} color={h.cpu > 70 ? 'bg-coral-flame' : 'bg-electric-cyan'} /><span className="text-ghost-white">{h.cpu}%</span></div>
                <div><span className="text-muted-silver block mb-1"><HardDrive size={10} className="inline mr-1" />Memory</span><Bar value={h.memory} color={h.memory > 70 ? 'bg-coral-flame' : 'bg-neon-emerald'} /><span className="text-ghost-white">{h.memory}%</span></div>
              </div>

              <div className="grid grid-cols-4 gap-2 text-[10px] text-muted-silver">
                <div><span className="block text-ghost-white">{h.uptime}</span>Uptime</div>
                <div><span className="block text-ghost-white">{h.lastPing}</span>Last Ping</div>
                <div><span className="block text-ghost-white">{h.tasks}</span>Active Tasks</div>
                <div><span className={`block ${h.errors24h > 5 ? 'text-coral-flame' : 'text-ghost-white'}`}>{h.errors24h}</span>Errors (24h)</div>
              </div>

              <div className="flex gap-2">
                <button className="text-[10px] text-electric-cyan hover:underline">Restart</button>
                <button className="text-[10px] text-muted-silver hover:underline">View Logs</button>
                {h.status !== 'healthy' && <button className="text-[10px] text-amber-glow hover:underline">Diagnose</button>}
              </div>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
