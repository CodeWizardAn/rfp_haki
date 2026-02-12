import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Bot,
  Save,
  RotateCcw,
  ChevronDown,
  ChevronRight,
  ToggleLeft,
  ToggleRight,
  Clock,
  RefreshCw,
  Zap,
  AlertTriangle,
  Brain,
  Network,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface AgentConfig {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  timeout: number;
  retries: number;
  fallback: 'skip' | 'default' | 'queue';
  model: string;
  temperature: number;
  maxTokens: number;
  priority: number;
}

/* ─── mock data ─── */
const MODELS = ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'claude-3-sonnet', 'claude-3-haiku', 'gemini-1.5-pro'];

const FALLBACK_OPTIONS = [
  { value: 'skip', label: 'Skip Agent', desc: 'Continue workflow without this agent' },
  { value: 'default', label: 'Use Defaults', desc: 'Return default/cached response' },
  { value: 'queue', label: 'Queue & Retry', desc: 'Queue task for background retry' },
];

const initialConfigs: AgentConfig[] = [
  { id: 'sales', name: 'Sales Agent', description: 'Product matching, pricing recommendations, and OEM identification', enabled: true, timeout: 30, retries: 3, fallback: 'default', model: 'gpt-4o', temperature: 0.3, maxTokens: 4096, priority: 1 },
  { id: 'technical', name: 'Technical Agent', description: 'Specification analysis, compliance verification, and engineering calculations', enabled: true, timeout: 45, retries: 2, fallback: 'queue', model: 'gpt-4o', temperature: 0.1, maxTokens: 8192, priority: 2 },
  { id: 'pricing', name: 'Pricing Agent', description: 'Cost estimation, margin optimization, and competitive pricing analysis', enabled: true, timeout: 30, retries: 3, fallback: 'default', model: 'gpt-4o-mini', temperature: 0.2, maxTokens: 4096, priority: 3 },
  { id: 'master', name: 'Master Agent', description: 'Orchestrates all agents, consolidates results, and generates final response', enabled: true, timeout: 60, retries: 1, fallback: 'skip', model: 'gpt-4o', temperature: 0.2, maxTokens: 16384, priority: 0 },
];

const PROTOCOLS = [
  { id: 'sequential', label: 'Sequential', desc: 'Agents run one after another in priority order', active: false },
  { id: 'parallel', label: 'Parallel', desc: 'Independent agents run simultaneously', active: true },
  { id: 'hybrid', label: 'Hybrid', desc: 'Parallel where possible, sequential for dependencies', active: false },
];

export default function AgentConfigPage() {
  const [configs, setConfigs] = useState(initialConfigs);
  const [expanded, setExpanded] = useState<string[]>(['sales']);
  const [protocol, setProtocol] = useState('parallel');
  const [saved, setSaved] = useState(false);

  const toggleExpand = (id: string) => setExpanded((p) => p.includes(id) ? p.filter((i) => i !== id) : [...p, id]);

  const updateConfig = (id: string, field: keyof AgentConfig, value: string | number | boolean) => {
    setConfigs((prev) => prev.map((c) => c.id === id ? { ...c, [field]: value } : c));
    setSaved(false);
  };

  const toggleEnabled = (id: string) => updateConfig(id, 'enabled', !configs.find((c) => c.id === id)!.enabled);

  const save = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };
  const resetAll = () => { setConfigs(initialConfigs); setProtocol('parallel'); };

  const SliderField = ({ label, value, min, max, step, unit, onChange }: { label: string; value: number; min: number; max: number; step: number; unit: string; onChange: (v: number) => void }) => (
    <div>
      <div className="flex justify-between text-[10px] mb-1">
        <span className="text-muted-silver">{label}</span>
        <span className="text-ghost-white font-mono">{value}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full h-1 rounded-full bg-steel-slate/25 appearance-none accent-electric-cyan cursor-pointer" />
    </div>
  );

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/agents" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
          <ArrowLeft size={18} className="text-muted-silver" />
        </Link>
        <div className="flex-1">
          <h1 className="text-h1 text-ghost-white">Agent Configuration</h1>
          <p className="text-body text-muted-silver">Configure agent behavior, models, and communication</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" leftIcon={<RotateCcw size={14} />} onClick={resetAll}>Reset</Button>
          <Button size="sm" leftIcon={saved ? <Zap size={14} /> : <Save size={14} />} onClick={save}>{saved ? 'Saved!' : 'Save Config'}</Button>
        </div>
      </div>

      {/* Communication Protocol */}
      <Card variant="glass" className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Network size={14} className="text-electric-cyan" />
          <h3 className="text-sm font-semibold text-ghost-white">Communication Protocol</h3>
        </div>
        <div className="grid md:grid-cols-3 gap-2">
          {PROTOCOLS.map((p) => (
            <button
              key={p.id}
              onClick={() => setProtocol(p.id)}
              className={`p-3 rounded-lg border text-left transition-all
                ${protocol === p.id ? 'border-electric-cyan/40 bg-electric-cyan/8' : 'border-steel-slate/15 hover:border-steel-slate/30'}`}
            >
              <span className={`text-xs font-semibold ${protocol === p.id ? 'text-electric-cyan' : 'text-ghost-white'}`}>{p.label}</span>
              <p className="text-[10px] text-muted-silver mt-0.5">{p.desc}</p>
            </button>
          ))}
        </div>
      </Card>

      {/* Agent Cards */}
      <div className="space-y-2">
        {configs.sort((a, b) => a.priority - b.priority).map((agent) => {
          const isExpanded = expanded.includes(agent.id);
          return (
            <Card key={agent.id} variant="glass" className={`overflow-hidden transition-all ${!agent.enabled ? 'opacity-50' : ''}`}>
              {/* Header */}
              <button onClick={() => toggleExpand(agent.id)} className="w-full flex items-center gap-3 p-4 hover:bg-steel-slate/5 transition-colors text-left">
                <Bot size={16} className={agent.enabled ? 'text-electric-cyan' : 'text-muted-silver/40'} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-ghost-white">{agent.name}</span>
                    <Badge variant="soft" color={agent.enabled ? 'cyan' : 'silver'} size="sm">{agent.enabled ? 'Active' : 'Disabled'}</Badge>
                    <Badge variant="outline" size="sm">{agent.model}</Badge>
                  </div>
                  <p className="text-[10px] text-muted-silver mt-0.5">{agent.description}</p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="text-right hidden md:block">
                    <span className="text-[10px] text-muted-silver flex items-center gap-1"><Clock size={9} />{agent.timeout}s timeout</span>
                    <span className="text-[10px] text-muted-silver flex items-center gap-1"><RefreshCw size={9} />{agent.retries} retries</span>
                  </div>
                  <button onClick={(e) => { e.stopPropagation(); toggleEnabled(agent.id); }}>
                    {agent.enabled ? <ToggleRight size={22} className="text-neon-emerald" /> : <ToggleLeft size={22} className="text-muted-silver/40" />}
                  </button>
                  {isExpanded ? <ChevronDown size={14} className="text-muted-silver" /> : <ChevronRight size={14} className="text-muted-silver" />}
                </div>
              </button>

              {/* Expanded Settings */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden">
                    <div className="px-4 pb-4 pt-0 space-y-4 border-t border-steel-slate/10">
                      {/* Execution Settings */}
                      <div className="grid md:grid-cols-3 gap-3 pt-3">
                        <SliderField label="Timeout" value={agent.timeout} min={5} max={120} step={5} unit="s" onChange={(v) => updateConfig(agent.id, 'timeout', v)} />
                        <SliderField label="Max Retries" value={agent.retries} min={0} max={5} step={1} unit="" onChange={(v) => updateConfig(agent.id, 'retries', v)} />
                        <div>
                          <label className="text-[10px] text-muted-silver block mb-1">Priority</label>
                          <input type="number" value={agent.priority} min={0} max={10} onChange={(e) => updateConfig(agent.id, 'priority', Number(e.target.value))} className="glass-input w-full rounded-lg px-2 py-1 text-xs text-ghost-white font-mono" />
                        </div>
                      </div>

                      {/* Model Settings */}
                      <div>
                        <div className="flex items-center gap-1.5 mb-2">
                          <Brain size={12} className="text-violet-pulse" />
                          <span className="text-[10px] text-muted-silver font-medium uppercase tracking-wider">Model Parameters</span>
                        </div>
                        <div className="grid md:grid-cols-3 gap-3">
                          <div>
                            <label className="text-[10px] text-muted-silver block mb-1">Model</label>
                            <select value={agent.model} onChange={(e) => updateConfig(agent.id, 'model', e.target.value)} className="glass-input w-full rounded-lg px-2 py-1.5 text-xs text-ghost-white">
                              {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
                            </select>
                          </div>
                          <SliderField label="Temperature" value={agent.temperature} min={0} max={1} step={0.1} unit="" onChange={(v) => updateConfig(agent.id, 'temperature', v)} />
                          <SliderField label="Max Tokens" value={agent.maxTokens} min={1024} max={32768} step={1024} unit="" onChange={(v) => updateConfig(agent.id, 'maxTokens', v)} />
                        </div>
                      </div>

                      {/* Fallback Behavior */}
                      <div>
                        <div className="flex items-center gap-1.5 mb-2">
                          <AlertTriangle size={12} className="text-amber-glow" />
                          <span className="text-[10px] text-muted-silver font-medium uppercase tracking-wider">Fallback Behavior</span>
                        </div>
                        <div className="grid md:grid-cols-3 gap-2">
                          {FALLBACK_OPTIONS.map((opt) => (
                            <button
                              key={opt.value}
                              onClick={() => updateConfig(agent.id, 'fallback', opt.value)}
                              className={`p-2 rounded-lg border text-left transition-all text-xs
                                ${agent.fallback === opt.value ? 'border-electric-cyan/40 bg-electric-cyan/8 text-electric-cyan' : 'border-steel-slate/15 text-muted-silver hover:border-steel-slate/30'}`}
                            >
                              <span className="font-semibold block">{opt.label}</span>
                              <span className="text-[9px] opacity-70">{opt.desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>
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
