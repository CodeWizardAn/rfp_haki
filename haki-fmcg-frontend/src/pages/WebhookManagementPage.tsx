import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Webhook,
  Plus,
  Trash2,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Copy,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface WebhookConfig {
  id: string;
  name: string;
  url: string;
  events: string[];
  secret: string;
  active: boolean;
  lastDelivery: string;
  lastStatus: 'success' | 'failed' | 'pending';
  failCount: number;
  createdAt: string;
}

interface DeliveryLog {
  id: string;
  webhookId: string;
  event: string;
  status: number;
  duration: string;
  ts: string;
  payload: string;
}

/* ─── data ─── */
const ALL_EVENTS = [
  'rfp.created', 'rfp.updated', 'rfp.status_changed',
  'bid.created', 'bid.submitted', 'bid.approved', 'bid.rejected',
  'vendor.registered', 'vendor.compliance_updated',
  'pipeline.completed', 'pipeline.failed',
  'agent.execution_completed', 'agent.error',
];

const initialWebhooks: WebhookConfig[] = [
  {
    id: 'wh-001', name: 'ERP Integration', url: 'https://erp.haki.com/webhooks/procurement',
    events: ['rfp.created', 'bid.approved', 'pipeline.completed'],
    secret: 'whsec_abc123def456', active: true,
    lastDelivery: '2 min ago', lastStatus: 'success', failCount: 0, createdAt: '2024-01-15',
  },
  {
    id: 'wh-002', name: 'Slack Notifications', url: 'https://hooks.slack.com/services/T123/B456/xyz',
    events: ['rfp.status_changed', 'bid.rejected', 'pipeline.failed', 'agent.error'],
    secret: 'whsec_ghi789jkl012', active: true,
    lastDelivery: '15 min ago', lastStatus: 'success', failCount: 0, createdAt: '2024-02-10',
  },
  {
    id: 'wh-003', name: 'Vendor Portal Sync', url: 'https://vendors.haki.com/api/sync',
    events: ['vendor.registered', 'vendor.compliance_updated'],
    secret: 'whsec_mno345pqr678', active: false,
    lastDelivery: '3 days ago', lastStatus: 'failed', failCount: 5, createdAt: '2024-03-01',
  },
];

const deliveryLogs: DeliveryLog[] = [
  { id: 'dl-1', webhookId: 'wh-001', event: 'bid.approved', status: 200, duration: '142ms', ts: '2 min ago', payload: '{"bid_id":"BID-2024-089","status":"approved"}' },
  { id: 'dl-2', webhookId: 'wh-002', event: 'rfp.status_changed', status: 200, duration: '98ms', ts: '15 min ago', payload: '{"rfp_id":"RFP-2024-089","new_status":"processing"}' },
  { id: 'dl-3', webhookId: 'wh-001', event: 'pipeline.completed', status: 200, duration: '156ms', ts: '1 hr ago', payload: '{"pipeline_id":"PL-442","status":"completed"}' },
  { id: 'dl-4', webhookId: 'wh-003', event: 'vendor.compliance_updated', status: 500, duration: '2.1s', ts: '3 days ago', payload: '{"vendor_id":"VND-012","error":"timeout"}' },
  { id: 'dl-5', webhookId: 'wh-003', event: 'vendor.registered', status: 500, duration: '3.2s', ts: '3 days ago', payload: '{"vendor_id":"VND-013","error":"connection_refused"}' },
];

export default function WebhookManagementPage() {
  const [webhooks, setWebhooks] = useState(initialWebhooks);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showSecret, setShowSecret] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState<string | null>(null);

  /* form state */
  const [formName, setFormName] = useState('');
  const [formUrl, setFormUrl] = useState('');
  const [formEvents, setFormEvents] = useState<string[]>([]);

  const toggleActive = (id: string) => {
    setWebhooks((p) => p.map((w) => (w.id === id ? { ...w, active: !w.active } : w)));
  };

  const deleteWebhook = (id: string) => {
    setWebhooks((p) => p.filter((w) => w.id !== id));
  };

  const testWebhook = (id: string) => {
    setTesting(id);
    setTimeout(() => setTesting(null), 1500);
  };

  const handleCreate = () => {
    if (!formName || !formUrl) return;
    const newWh: WebhookConfig = {
      id: `wh-${Date.now()}`, name: formName, url: formUrl,
      events: formEvents, secret: `whsec_${Math.random().toString(36).slice(2, 14)}`,
      active: true, lastDelivery: '—', lastStatus: 'pending', failCount: 0,
      createdAt: new Date().toISOString().split('T')[0] ?? '',
    };
    setWebhooks((p) => [...p, newWh]);
    setFormName(''); setFormUrl(''); setFormEvents([]); setShowCreate(false);
  };

  const toggleFormEvent = (e: string) => {
    setFormEvents((p) => (p.includes(e) ? p.filter((x) => x !== e) : [...p, e]));
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/settings" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Webhook Management</h1>
            <p className="text-body text-muted-silver">Configure event subscriptions & delivery endpoints</p>
          </div>
        </div>
        <Button leftIcon={<Plus size={14} />} onClick={() => setShowCreate(true)}>Add Webhook</Button>
      </div>

      {/* Create Form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <Card variant="glass" className="space-y-4 p-4">
              <h3 className="text-sm font-semibold text-ghost-white">New Webhook</h3>
              <div className="grid md:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-muted-silver block mb-1">Name</label>
                  <input value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="e.g. ERP Sync" className="glass-input w-full rounded-lg px-3 py-2 text-sm text-ghost-white" />
                </div>
                <div>
                  <label className="text-xs text-muted-silver block mb-1">Endpoint URL</label>
                  <input value={formUrl} onChange={(e) => setFormUrl(e.target.value)} placeholder="https://..." className="glass-input w-full rounded-lg px-3 py-2 text-sm text-ghost-white" />
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-silver block mb-2">Events</label>
                <div className="flex flex-wrap gap-1.5">
                  {ALL_EVENTS.map((e) => (
                    <button key={e} onClick={() => toggleFormEvent(e)} className={`px-2 py-1 rounded-md text-[10px] font-medium transition-colors border ${formEvents.includes(e) ? 'border-electric-cyan/40 bg-electric-cyan/10 text-electric-cyan' : 'border-steel-slate/20 text-muted-silver hover:border-steel-slate/40'}`}>
                      {e}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleCreate}>Create Webhook</Button>
                <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Webhooks List */}
      <div className="space-y-3">
        {webhooks.map((wh) => {
          const logs = deliveryLogs.filter((l) => l.webhookId === wh.id);
          const isExpanded = expanded === wh.id;
          return (
            <Card key={wh.id} variant="glass" className="overflow-hidden">
              <div className="p-4 flex items-start gap-4">
                {/* Icon */}
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${wh.active ? 'bg-neon-emerald/10' : 'bg-steel-slate/15'}`}>
                  <Webhook size={16} className={wh.active ? 'text-neon-emerald' : 'text-muted-silver'} />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-semibold text-ghost-white">{wh.name}</span>
                    <Badge variant={wh.active ? 'success' : 'default'} size="sm">{wh.active ? 'Active' : 'Inactive'}</Badge>
                    {wh.failCount > 0 && <Badge variant="danger" size="sm">{wh.failCount} fails</Badge>}
                  </div>
                  <p className="text-xs text-muted-silver font-mono truncate">{wh.url}</p>
                  <div className="flex items-center gap-3 mt-1.5 text-[10px] text-muted-silver">
                    <span className="flex items-center gap-1">
                      <Clock size={10} /> Last: {wh.lastDelivery}
                    </span>
                    <span className="flex items-center gap-1">
                      {wh.lastStatus === 'success' && <><CheckCircle2 size={10} className="text-neon-emerald" /> 200</>}
                      {wh.lastStatus === 'failed' && <><XCircle size={10} className="text-coral-flame" /> 500</>}
                      {wh.lastStatus === 'pending' && <><Clock size={10} /> Pending</>}
                    </span>
                    <span>Events: {wh.events.length}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                  <button onClick={() => testWebhook(wh.id)} className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors" title="Test">
                    {testing === wh.id ? <RefreshCw size={14} className="text-electric-cyan animate-spin" /> : <Play size={14} className="text-muted-silver" />}
                  </button>
                  <button onClick={() => toggleActive(wh.id)} className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors" title="Toggle">
                    {wh.active ? <CheckCircle2 size={14} className="text-neon-emerald" /> : <XCircle size={14} className="text-muted-silver" />}
                  </button>
                  <button onClick={() => deleteWebhook(wh.id)} className="p-1.5 rounded-lg hover:bg-coral-flame/10 transition-colors" title="Delete">
                    <Trash2 size={14} className="text-coral-flame" />
                  </button>
                  <button onClick={() => setExpanded(isExpanded ? null : wh.id)} className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors">
                    {isExpanded ? <ChevronUp size={14} className="text-muted-silver" /> : <ChevronDown size={14} className="text-muted-silver" />}
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-steel-slate/10">
                    <div className="p-4 space-y-4">
                      {/* Secret */}
                      <div>
                        <span className="text-xs text-muted-silver block mb-1">Secret</span>
                        <div className="flex items-center gap-2">
                          <code className="text-xs font-mono text-ghost-white bg-steel-slate/15 px-2 py-1 rounded">
                            {showSecret[wh.id] ? wh.secret : '•'.repeat(24)}
                          </code>
                          <button onClick={() => setShowSecret((p) => ({ ...p, [wh.id]: !p[wh.id] }))} className="text-muted-silver hover:text-ghost-white">
                            {showSecret[wh.id] ? <EyeOff size={12} /> : <Eye size={12} />}
                          </button>
                          <button onClick={() => navigator.clipboard.writeText(wh.secret)} className="text-muted-silver hover:text-ghost-white">
                            <Copy size={12} />
                          </button>
                        </div>
                      </div>

                      {/* Subscribed Events */}
                      <div>
                        <span className="text-xs text-muted-silver block mb-1">Subscribed Events</span>
                        <div className="flex flex-wrap gap-1">
                          {wh.events.map((e) => (
                            <Badge key={e} variant="soft" color="cyan" size="sm">{e}</Badge>
                          ))}
                        </div>
                      </div>

                      {/* Delivery Logs */}
                      {logs.length > 0 && (
                        <div>
                          <span className="text-xs text-muted-silver block mb-1">Recent Deliveries</span>
                          <div className="space-y-1">
                            {logs.map((l) => (
                              <div key={l.id} className="flex items-center gap-3 py-1.5 text-xs border-b border-steel-slate/8 last:border-0">
                                <span className={`font-mono font-semibold ${l.status < 300 ? 'text-neon-emerald' : 'text-coral-flame'}`}>{l.status}</span>
                                <span className="text-muted-silver">{l.event}</span>
                                <span className="text-muted-silver ml-auto">{l.duration}</span>
                                <span className="text-muted-silver">{l.ts}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
