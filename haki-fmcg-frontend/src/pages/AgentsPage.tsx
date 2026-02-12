import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  Play,
  ScrollText,
  Activity,
  Clock,
  CheckCircle2,

  Globe,
  Database,
  Banknote,
  Zap,
  ChevronRight,
  ExternalLink,

  MessageSquare,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { AgentPerformancePanel } from '@/components/agents';
import { useAgentStatuses, useAgentConversations, useStartAgentWorkflow } from '@/hooks/useApi';

/* ───── Agent definitions ───── */
const agents = [
  {
    id: 'master',
    name: 'Master Agent',
    color: '#7C3AED',
    icon: <Zap size={20} />,
    status: 'ready' as const,
    description: 'Orchestrates all agents and consolidates responses',
    metrics: { conversations: 142, avgTime: '1.2s', successRate: 99.1 },
    sparkline: [20, 25, 22, 30, 28, 35, 32, 40, 38, 42],
  },
  {
    id: 'sales',
    name: 'Sales Agent',
    color: '#00D4FF',
    icon: <Globe size={20} />,
    status: 'ready' as const,
    description: 'Scans URLs, extracts RFPs, identifies opportunities',
    metrics: { rfpsScanned: 87, urlsMonitored: 12, successRate: 94.2 },
    sparkline: [15, 18, 12, 20, 22, 19, 25, 28, 24, 30],
  },
  {
    id: 'technical',
    name: 'Technical Agent',
    color: '#14B8A6',
    icon: <Database size={20} />,
    status: 'ready' as const,
    description: 'Analyzes specs, matches products, loads datasheets',
    metrics: { productsAnalyzed: 234, avgMatchScore: 89, datasheets: 8 },
    sparkline: [30, 28, 35, 40, 38, 42, 45, 40, 48, 50],
  },
  {
    id: 'pricing',
    name: 'Pricing Agent',
    color: '#FFB224',
    icon: <Banknote size={20} />,
    status: 'ready' as const,
    description: 'Calculates quotes with GST, discounts, test costs',
    metrics: { quotesGenerated: 96, avgTurnaround: '3.4s', accuracy: 97.8 },
    sparkline: [10, 15, 12, 18, 20, 22, 25, 28, 30, 32],
  },
];

/* ───── Mock workflow conversations ───── */
const mockConversations = [
  {
    id: 'CONV_20260206_001',
    rfpId: 'RFP-2026-0001',
    status: 'completed',
    agents: ['master', 'sales', 'technical', 'pricing'],
    duration: '21.4s',
    timestamp: '2026-02-06 14:32:10',
    steps: 5,
  },
  {
    id: 'CONV_20260206_002',
    rfpId: 'RFP-2026-0002',
    status: 'running',
    agents: ['master', 'technical', 'pricing'],
    duration: '8.2s',
    timestamp: '2026-02-06 15:01:44',
    steps: 3,
  },
  {
    id: 'CONV_20260205_003',
    rfpId: 'RFP-2026-0003',
    status: 'failed',
    agents: ['master', 'sales'],
    duration: '4.1s',
    timestamp: '2026-02-05 10:20:30',
    steps: 2,
  },
];

/* ───── Mock workflow steps for live view ───── */
const mockWorkflowSteps = [
  { agent: 'master', action: 'Started orchestration for RFP-2026-0001', status: 'completed', duration: '0.2s', color: '#7C3AED' },
  { agent: 'sales', action: 'Extracted 5 requirements from PDF document (3 pages)', status: 'completed', duration: '4.5s', color: '#00D4FF' },
  { agent: 'master', action: 'Prepared technical + pricing summaries', status: 'completed', duration: '0.8s', color: '#7C3AED' },
  { agent: 'technical', action: 'Matched 5 requirements → 14 products across 5 OEMs', status: 'completed', duration: '12.3s', color: '#14B8A6' },
  { agent: 'pricing', action: 'Calculated pricing for 5 line items (₹55.6L + GST)', status: 'completed', duration: '3.8s', color: '#FFB224' },
  { agent: 'master', action: 'Consolidated final response with scope of supply table', status: 'completed', duration: '0.4s', color: '#7C3AED' },
];

const statusColor = (s: string) =>
  s === 'completed' ? 'emerald' : s === 'running' ? 'cyan' : 'coral';

const statusDotColor = (s: string) =>
  s === 'ready' ? 'bg-neon-emerald' : s === 'busy' ? 'bg-amber-glow' : 'bg-coral-flame';

/* ═══════════════════════════════════════════════════ */
export default function AgentsPage() {
  /* ── Backend hooks ── */
  const { data: apiStatuses } = useAgentStatuses();
  const { data: apiConversations } = useAgentConversations();
  const startWorkflowMutation = useStartAgentWorkflow();

  /* Merge agent statuses from backend */
  const mergedAgents = useMemo(() => {
    if (!apiStatuses) return agents;
    const statuses = Array.isArray(apiStatuses) ? apiStatuses : (apiStatuses as { data?: unknown[] })?.data;
    if (!statuses?.length) return agents;
    return agents.map((a) => {
      const apiAgent = (statuses as Record<string, unknown>[]).find((s) => (s.id || s.type) === a.id);
      if (!apiAgent) return a;
      return { ...a, status: (apiAgent.status as typeof a.status) || a.status };
    });
  }, [apiStatuses]);

  /* Merge conversations from backend */
  const mergedConversations = useMemo(() => {
    if (!apiConversations) return mockConversations;
    const convs = Array.isArray(apiConversations) ? apiConversations : (apiConversations as { data?: unknown[] })?.data;
    if (!convs?.length) return mockConversations;
    return convs as typeof mockConversations;
  }, [apiConversations]);

  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [showWorkflow, setShowWorkflow] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  // Animated flow particles
  const [flowPhase, setFlowPhase] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setFlowPhase((p) => (p + 1) % 4), 2000);
    return () => clearInterval(t);
  }, []);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-violet-pulse/10">
            <Bot size={24} className="text-violet-pulse" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">AI Agent Control Room</h1>
            <p className="text-body text-muted-silver">Monitor, orchestrate, and analyze agent workflows</p>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button variant="secondary" leftIcon={<ScrollText size={14} />} onClick={() => setShowLogs(!showLogs)}>
            Logs
          </Button>
          <Button variant="primary" leftIcon={<Play size={14} />} onClick={() => setShowWorkflow(true)}>
            Run Workflow
          </Button>
        </div>
      </div>

      {/* ── Agent Status Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {mergedAgents.map((agent) => (
          <motion.div
            key={agent.id}
            whileHover={{ y: -2 }}
            onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
            className="cursor-pointer"
          >
            <Card
              variant="glass"
              className={`relative overflow-hidden transition-all ${
                selectedAgent === agent.id ? 'ring-2' : ''
              }`}
              style={{
                borderColor: selectedAgent === agent.id ? agent.color + '60' : undefined,
                boxShadow: selectedAgent === agent.id ? `0 0 20px ${agent.color}15` : undefined,
              }}
            >
              {/* Accent bar */}
              <div className="absolute top-0 left-0 right-0 h-1" style={{ backgroundColor: agent.color }} />

              <div className="flex items-start justify-between mb-3 pt-1">
                <div className="flex items-center gap-2">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{ backgroundColor: agent.color + '15' }}
                  >
                    <span style={{ color: agent.color }}>{agent.icon}</span>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ghost-white">{agent.name}</p>
                    <div className="flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${statusDotColor(agent.status)}`} />
                      <span className="text-xs text-muted-silver capitalize">{agent.status}</span>
                    </div>
                  </div>
                </div>
                <ChevronRight size={14} className="text-muted-silver" />
              </div>

              <p className="text-xs text-muted-silver mb-3">{agent.description}</p>

              {/* Mini sparkline */}
              <div className="flex items-end gap-0.5 h-8 mb-3">
                {agent.sparkline.map((v, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-t-sm transition-all"
                    style={{
                      height: `${(v / 50) * 100}%`,
                      backgroundColor: agent.color + (i === agent.sparkline.length - 1 ? 'CC' : '40'),
                    }}
                  />
                ))}
              </div>

              {/* Key metrics */}
              <div className="grid grid-cols-3 gap-2 text-center">
                {Object.entries(agent.metrics).slice(0, 3).map(([key, val]) => (
                  <div key={key}>
                    <p className="text-xs font-bold text-ghost-white">{typeof val === 'number' && val > 100 ? val.toLocaleString() : val}{typeof val === 'number' && key.includes('Rate') || key === 'accuracy' || key === 'avgMatchScore' ? '%' : ''}</p>
                    <p className="text-[10px] text-muted-silver capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</p>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* ── Agent Communication Flow ── */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Agent Communication Flow
            <Badge variant="soft" color="emerald" size="sm">
              <Activity size={10} className="mr-1" /> Active
            </Badge>
          </CardTitle>
        </CardHeader>
        <div className="relative py-8 px-4 min-h-[200px]">
          {/* Simplified flow visualization */}
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {/* Master -> Sales */}
            <FlowNode label="Master" color="#7C3AED" active={flowPhase === 0} />
            <FlowArrow active={flowPhase === 0} />
            <FlowNode label="Sales" color="#00D4FF" active={flowPhase === 1} />
            <FlowArrow active={flowPhase === 1} />
            <FlowNode label="Technical" color="#14B8A6" active={flowPhase === 2} />
            <FlowArrow active={flowPhase === 2} />
            <FlowNode label="Pricing" color="#FFB224" active={flowPhase === 3} />
            <FlowArrow active={flowPhase === 3} reverse />
            <FlowNode label="Master" color="#7C3AED" active={flowPhase === 0} subtitle="Consolidate" />
          </div>
          {/* Legend */}
          <div className="flex items-center justify-center gap-4 mt-6 text-xs text-muted-silver">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-neon-emerald" /> Active</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-electric-cyan animate-pulse" /> Processing</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-steel-slate/50" /> Idle</span>
          </div>
        </div>
      </Card>

      {/* ── Recent Workflows ── */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle>Recent Workflows</CardTitle>
          <Button variant="ghost" size="sm">View All →</Button>
        </CardHeader>
        <div className="space-y-3">
          {mergedConversations.map((conv) => (
            <div
              key={conv.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-steel-slate/10 hover:bg-steel-slate/15 transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-4">
                <Badge variant="soft" color={statusColor(conv.status)}>{conv.status}</Badge>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-ghost-white font-mono">{conv.id}</p>
                    <span className="text-xs text-muted-silver">·</span>
                    <p className="text-sm text-electric-cyan">{conv.rfpId}</p>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-muted-silver">{conv.timestamp}</span>
                    <span className="text-xs text-muted-silver">·</span>
                    <span className="text-xs text-muted-silver">{conv.steps} steps</span>
                    <span className="text-xs text-muted-silver">·</span>
                    <div className="flex gap-1">
                      {conv.agents.map((a) => {
                        const ag = mergedAgents.find((x) => x.id === a);
                        return ag ? (
                          <span
                            key={a}
                            className="w-4 h-4 rounded-full flex items-center justify-center"
                            style={{ backgroundColor: ag.color + '30' }}
                            title={ag.name}
                          >
                            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: ag.color }} />
                          </span>
                        ) : null;
                      })}
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 mt-2 sm:mt-0">
                <div className="flex items-center gap-1 text-xs text-muted-silver">
                  <Clock size={10} /> {conv.duration}
                </div>
                <Button variant="ghost" size="xs" leftIcon={<ExternalLink size={10} />}>View</Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* ── Workflow Live View (Toggle) ── */}
      <AnimatePresence>
        {showLogs && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card variant="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare size={16} className="text-electric-cyan" />
                  Workflow Timeline — CONV_20260206_001
                </CardTitle>
              </CardHeader>
              <div className="space-y-0">
                {mockWorkflowSteps.map((step, i) => (
                  <div key={i} className="relative flex items-start gap-4 pb-5 last:pb-0">
                    {i < mockWorkflowSteps.length - 1 && (
                      <div className="absolute left-[15px] top-9 bottom-0 w-px" style={{ backgroundColor: step.color + '30' }} />
                    )}
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ring-2 ring-deep-navy"
                      style={{ backgroundColor: step.color + '20' }}
                    >
                      <Bot size={14} style={{ color: step.color }} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-ghost-white capitalize">{step.agent} Agent</span>
                        <Badge variant="soft" color="emerald" size="sm">{step.status}</Badge>
                        <span className="text-xs text-muted-silver ml-auto">{step.duration}</span>
                      </div>
                      <p className="text-sm text-muted-silver mt-1">{step.action}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Agent Performance Metrics ── */}
      <AgentPerformancePanel />

      {/* ── Run Workflow Modal ── */}
      <AnimatePresence>
        {showWorkflow && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-deep-navy/70 backdrop-blur-sm z-40"
              onClick={() => setShowWorkflow(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg bg-midnight-blue border border-steel-slate/30 rounded-2xl shadow-2xl"
            >
              <div className="px-6 py-5 border-b border-steel-slate/30">
                <h3 className="text-lg font-semibold text-ghost-white">Run Agent Workflow</h3>
                <p className="text-xs text-muted-silver mt-1">Configure agents and start processing</p>
              </div>
              <div className="px-6 py-5 space-y-4">
                {/* Input */}
                <div>
                  <label className="text-xs text-muted-silver uppercase tracking-wider mb-2 block">RFP Input</label>
                  <textarea
                    rows={3}
                    placeholder="Paste RFP text or upload a file…"
                    className="w-full px-3 py-2 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50 resize-none"
                  />
                </div>
                {/* Agent selection */}
                <div>
                  <label className="text-xs text-muted-silver uppercase tracking-wider mb-2 block">Agents</label>
                  <div className="grid grid-cols-2 gap-2">
                    {mergedAgents.map((a) => (
                      <div
                        key={a.id}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg border border-steel-slate/30 hover:border-electric-cyan/30 transition-colors cursor-pointer"
                      >
                        <div className="w-3 h-3 rounded border-2 border-electric-cyan bg-electric-cyan flex items-center justify-center">
                          <CheckCircle2 size={8} className="text-deep-navy" />
                        </div>
                        <span className="text-sm" style={{ color: a.color }}>{a.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
                {/* Workflow template */}
                <div>
                  <label className="text-xs text-muted-silver uppercase tracking-wider mb-2 block">Template</label>
                  <div className="flex gap-2">
                    <button className="flex-1 px-3 py-2 rounded-lg bg-electric-cyan/10 border border-electric-cyan/30 text-electric-cyan text-sm font-medium">
                      Quick Quote
                    </button>
                    <button className="flex-1 px-3 py-2 rounded-lg border border-steel-slate/30 text-muted-silver text-sm hover:border-steel-slate/50 transition-colors">
                      Full Analysis
                    </button>
                    <button className="flex-1 px-3 py-2 rounded-lg border border-steel-slate/30 text-muted-silver text-sm hover:border-steel-slate/50 transition-colors">
                      Custom
                    </button>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 border-t border-steel-slate/30 flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowWorkflow(false)}>Cancel</Button>
                <Button variant="primary" leftIcon={<Play size={14} />} onClick={() => { startWorkflowMutation.mutate(1); setShowWorkflow(false); }}>
                  Start Workflow
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ───── sub-components ───── */

function FlowNode({ label, color, active, subtitle }: { label: string; color: string; active: boolean; subtitle?: string }) {
  return (
    <motion.div
      className="flex flex-col items-center gap-1"
      animate={active ? { scale: [1, 1.08, 1] } : {}}
      transition={{ duration: 0.8, repeat: active ? Infinity : 0 }}
    >
      <div
        className={`w-14 h-14 rounded-xl flex items-center justify-center border-2 transition-all ${
          active ? 'shadow-lg' : ''
        }`}
        style={{
          backgroundColor: color + '15',
          borderColor: active ? color : color + '30',
          boxShadow: active ? `0 0 20px ${color}30` : undefined,
        }}
      >
        <Bot size={18} style={{ color }} />
      </div>
      <span className="text-xs text-ghost-white font-medium">{label}</span>
      {subtitle && <span className="text-[10px] text-muted-silver">{subtitle}</span>}
    </motion.div>
  );
}

function FlowArrow({ active, reverse }: { active: boolean; reverse?: boolean }) {
  return (
    <div className={`flex items-center ${reverse ? 'rotate-180' : ''}`}>
      <motion.div
        className="h-0.5 w-8 rounded-full"
        style={{ backgroundColor: active ? '#00D4FF' : '#1E2642' }}
        animate={active ? { opacity: [0.4, 1, 0.4] } : {}}
        transition={{ duration: 1, repeat: Infinity }}
      />
      <div
        className="w-0 h-0 border-t-[4px] border-t-transparent border-b-[4px] border-b-transparent border-l-[6px]"
        style={{ borderLeftColor: active ? '#00D4FF' : '#1E2642' }}
      />
    </div>
  );
}
