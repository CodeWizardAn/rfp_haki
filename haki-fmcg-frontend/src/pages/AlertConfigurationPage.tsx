import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Bell, BellOff, Plus, Trash2, AlertTriangle, TrendingDown, Activity } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface AlertRule { id: number; name: string; metric: string; condition: 'above' | 'below' | 'change'; threshold: number; unit: string; severity: 'critical' | 'warning' | 'info'; enabled: boolean; channel: string; lastTriggered?: string; }

const alertRules: AlertRule[] = [
  { id: 1, name: 'Pipeline Failure Rate', metric: 'pipeline.failure_rate', condition: 'above', threshold: 10, unit: '%', severity: 'critical', enabled: true, channel: 'Email + SMS', lastTriggered: '2h ago' },
  { id: 2, name: 'Bid Win Rate Drop', metric: 'bids.win_rate', condition: 'below', threshold: 40, unit: '%', severity: 'warning', enabled: true, channel: 'Email', lastTriggered: '3d ago' },
  { id: 3, name: 'Agent Response Time', metric: 'agents.avg_response_time', condition: 'above', threshold: 60, unit: 's', severity: 'warning', enabled: true, channel: 'Dashboard' },
  { id: 4, name: 'Revenue MoM Change', metric: 'revenue.mom_change', condition: 'change', threshold: -15, unit: '%', severity: 'critical', enabled: false, channel: 'Email + Slack' },
  { id: 5, name: 'Vendor Compliance Gap', metric: 'vendors.cert_expiring', condition: 'above', threshold: 3, unit: 'vendors', severity: 'info', enabled: true, channel: 'Dashboard', lastTriggered: '1w ago' },
  { id: 6, name: 'System CPU Usage', metric: 'system.cpu', condition: 'above', threshold: 85, unit: '%', severity: 'critical', enabled: true, channel: 'Email + SMS', lastTriggered: '5d ago' },
];

const sevCfg: Record<string, { color: 'coral' | 'amber' | 'cyan'; icon: typeof AlertTriangle }> = {
  critical: { color: 'coral', icon: AlertTriangle },
  warning: { color: 'amber', icon: TrendingDown },
  info: { color: 'cyan', icon: Activity },
};

export default function AlertConfigurationPage() {
  const [rules, setRules] = useState(alertRules);
  const toggleRule = (id: number) => setRules((p) => p.map((r) => r.id === id ? { ...r, enabled: !r.enabled } : r));

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/analytics" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Alert Configuration</h1><p className="text-body text-muted-silver">Manage thresholds and notification rules</p></div>
        </div>
        <button className="flex items-center gap-2 bg-electric-cyan/20 text-electric-cyan px-4 py-2 rounded-lg hover:bg-electric-cyan/30 text-sm font-medium"><Plus size={14} />New Alert</button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { l: 'Active Alerts', v: rules.filter((r) => r.enabled).length, icon: Bell, c: 'text-neon-emerald' },
          { l: 'Critical Rules', v: rules.filter((r) => r.severity === 'critical').length, icon: AlertTriangle, c: 'text-coral-flame' },
          { l: 'Disabled', v: rules.filter((r) => !r.enabled).length, icon: BellOff, c: 'text-muted-silver' },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-4 text-center">
            <s.icon size={18} className={`${s.c} mx-auto mb-2`} />
            <span className="text-2xl font-bold text-ghost-white">{s.v}</span>
            <span className="text-xs text-muted-silver block mt-1">{s.l}</span>
          </Card>
        ))}
      </div>

      <div className="space-y-3">
        {rules.map((rule) => {
          const cfg = (sevCfg[rule.severity] ?? sevCfg['info'])!;
          return (
            <Card key={rule.id} variant="glass" className={`p-4 ${!rule.enabled ? 'opacity-50' : ''}`}>
              <div className="flex items-center gap-4">
                <button onClick={() => toggleRule(rule.id)} className={`w-10 h-5 rounded-full transition-colors relative ${rule.enabled ? 'bg-neon-emerald' : 'bg-steel-slate/30'}`}>
                  <span className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform ${rule.enabled ? 'left-5.5 translate-x-0' : 'left-0.5'}`} style={{ left: rule.enabled ? '22px' : '2px' }} />
                </button>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-ghost-white">{rule.name}</h3>
                    <Badge variant="soft" color={cfg.color} size="sm">{rule.severity}</Badge>
                  </div>
                  <p className="text-xs text-muted-silver">
                    When <span className="text-electric-cyan font-mono">{rule.metric}</span> is {rule.condition} <span className="text-amber-glow font-bold">{rule.threshold}{rule.unit}</span>
                    {' → '}<span className="text-ghost-white">{rule.channel}</span>
                  </p>
                </div>
                {rule.lastTriggered && <span className="text-[10px] text-muted-silver">Last: {rule.lastTriggered}</span>}
                <button className="p-2 hover:bg-coral-flame/10 rounded-lg text-coral-flame/40 hover:text-coral-flame"><Trash2 size={14} /></button>
              </div>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
