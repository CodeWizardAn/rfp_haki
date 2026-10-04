import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, Activity, Heart, Cpu, HardDrive, Wifi, XCircle, RefreshCw } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface HealthItem { agent: string; status: 'healthy' | 'degraded' | 'down'; uptime: string; cpu: number; memory: number; lastPing: string; tasks: number; errors24h: number; }

const initialHealthData: HealthItem[] = [
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
  const [data, setData] = useState<HealthItem[]>(initialHealthData);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const navigate = useNavigate();

  const handleRefreshAll = () => {
    setIsRefreshing(true);
    toast.loading('Polling telemetry from all agent nodes...', { duration: 1000 });
    setTimeout(() => {
      setData((prev) =>
        prev.map((item) => ({
          ...item,
          lastPing: 'Just now',
          cpu: Math.max(10, Math.min(90, Math.round(item.cpu + (Math.random() * 10 - 5)))),
        }))
      );
      setIsRefreshing(false);
      toast.success('Agent telemetry refreshed successfully');
    }, 1000);
  };

  const handleRestart = (agentName: string) => {
    toast.loading(`Restarting container for ${agentName}...`, { duration: 1500 });
    setTimeout(() => {
      setData((prev) =>
        prev.map((item) =>
          item.agent === agentName
            ? { ...item, status: 'healthy', cpu: 15, memory: 35, errors24h: 0, lastPing: '1s ago' }
            : item
        )
      );
      toast.success(`${agentName} restarted and verified healthy!`);
    }, 1500);
  };

  const handleDiagnose = (agentName: string) => {
    toast(`Running diagnostics on ${agentName}... CPU throttling resolved, memory garbage collected.`, {
      icon: '🩺',
    });
    setData((prev) =>
      prev.map((item) =>
        item.agent === agentName
          ? { ...item, status: 'healthy', cpu: 42, memory: 55 }
          : item
      )
    );
  };
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/agents" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Agent Health Check</h1><p className="text-body text-muted-silver">Real-time health status and resource monitoring</p></div>
        </div>
        <button
          onClick={handleRefreshAll}
          disabled={isRefreshing}
          className="flex items-center gap-2 text-sm text-electric-cyan hover:text-electric-cyan/80 cursor-pointer disabled:opacity-50 transition-opacity"
        >
          <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
          Refresh All
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { l: 'Overall Health', v: '95%', icon: Heart, c: 'text-neon-emerald' },
          { l: 'Agents Online', v: `${data.filter((h) => h.status !== 'down').length}/${data.length}`, icon: Wifi, c: 'text-electric-cyan' },
          { l: 'Active Tasks', v: data.reduce((a, h) => a + h.tasks, 0).toString(), icon: Activity, c: 'text-amber-glow' },
          { l: 'Errors (24h)', v: data.reduce((a, h) => a + h.errors24h, 0).toString(), icon: XCircle, c: 'text-coral-flame' },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-4">
            <s.icon size={16} className={`${s.c} mb-2`} />
            <span className="text-xl font-bold text-ghost-white">{s.v}</span>
            <span className="text-xs text-muted-silver block mt-1">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {data.map((h) => {
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

              <div className="flex gap-3 pt-1">
                <button
                  onClick={() => handleRestart(h.agent)}
                  className="text-xs text-electric-cyan hover:underline cursor-pointer font-medium"
                >
                  Restart
                </button>
                <button
                  onClick={() => navigate('/agents')}
                  className="text-xs text-muted-silver hover:underline cursor-pointer"
                >
                  View Logs
                </button>
                {h.status !== 'healthy' && (
                  <button
                    onClick={() => handleDiagnose(h.agent)}
                    className="text-xs text-amber-glow hover:underline cursor-pointer font-medium"
                  >
                    Diagnose
                  </button>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
