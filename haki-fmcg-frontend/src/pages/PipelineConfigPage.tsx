import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, ToggleLeft, ToggleRight, Save, RotateCcw, Clock, RefreshCw, Layers, Zap } from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

interface StageConfig { id: string; name: string; enabled: boolean; timeout: number; retries: number; }

const initialStages: StageConfig[] = [
  { id: 'pdf_extraction', name: 'PDF Extraction', enabled: true, timeout: 30, retries: 2 },
  { id: 'term_matching', name: 'Term Matching', enabled: true, timeout: 60, retries: 3 },
  { id: 'vector_search', name: 'Vector Search', enabled: true, timeout: 45, retries: 2 },
  { id: 'spec_matching', name: 'Spec Matching', enabled: true, timeout: 60, retries: 2 },
  { id: 'pricing_calc', name: 'Pricing Calculation', enabled: true, timeout: 30, retries: 3 },
  { id: 'bid_generation', name: 'Bid Generation', enabled: true, timeout: 45, retries: 1 },
  { id: 'compliance_check', name: 'Compliance Check', enabled: true, timeout: 30, retries: 2 },
  { id: 'audit_logging', name: 'Audit & Analytics', enabled: true, timeout: 15, retries: 1 },
];

export default function PipelineConfigPage() {
  const [stages, setStages] = useState(initialStages);
  const [mode, setMode] = useState<'standard' | 'agent'>('standard');
  const [saved, setSaved] = useState(false);

  const toggle = (id: string) => setStages((p) => p.map((s) => s.id === id ? { ...s, enabled: !s.enabled } : s));
  const updateTimeout = (id: string, v: number) => setStages((p) => p.map((s) => s.id === id ? { ...s, timeout: v } : s));
  const updateRetries = (id: string, v: number) => setStages((p) => p.map((s) => s.id === id ? { ...s, retries: v } : s));
  const save = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/pipeline" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div className="flex-1"><h1 className="text-h1 text-ghost-white">Pipeline Configuration</h1><p className="text-body text-muted-silver">Configure stages, timeouts, and pipeline behavior</p></div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" leftIcon={<RotateCcw size={14} />} onClick={() => setStages(initialStages)}>Reset</Button>
          <Button size="sm" leftIcon={saved ? <Zap size={14} /> : <Save size={14} />} onClick={save}>{saved ? 'Saved!' : 'Save'}</Button>
        </div>
      </div>

      <Card variant="glass" className="p-4">
        <div className="flex items-center gap-2 mb-3"><Layers size={14} className="text-electric-cyan" /><h3 className="text-sm font-semibold text-ghost-white">Pipeline Mode</h3></div>
        <div className="grid md:grid-cols-2 gap-2">
          {([['standard', 'Standard (8-stage)', 'All stages run sequentially: PDF → Match → Price → Bid → Compliance'], ['agent', 'Agent-Driven (5-stage)', 'AI agents orchestrate: Sales → Technical → Pricing → Master → Consolidate']] as const).map(([id, label, desc]) => (
            <button key={id} onClick={() => setMode(id)} className={`p-3 rounded-lg border text-left transition-all ${mode === id ? 'border-electric-cyan/40 bg-electric-cyan/8' : 'border-steel-slate/15 hover:border-steel-slate/30'}`}>
              <span className={`text-xs font-semibold ${mode === id ? 'text-electric-cyan' : 'text-ghost-white'}`}>{label}</span>
              <p className="text-[10px] text-muted-silver mt-0.5">{desc}</p>
            </button>
          ))}
        </div>
      </Card>

      <div className="space-y-2">
        {stages.map((stage, idx) => (
          <Card key={stage.id} variant="glass" className={`p-4 transition-all ${!stage.enabled ? 'opacity-50' : ''}`}>
            <div className="flex items-center gap-4">
              <span className="w-6 h-6 rounded-full bg-steel-slate/20 flex items-center justify-center text-[10px] font-bold text-muted-silver">{idx + 1}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2"><span className="text-sm font-semibold text-ghost-white">{stage.name}</span><Badge variant={stage.enabled ? 'soft' : 'outline'} color={stage.enabled ? 'emerald' : 'silver'} size="sm">{stage.enabled ? 'Enabled' : 'Disabled'}</Badge></div>
                {stage.enabled && (
                  <div className="flex items-center gap-4 mt-2">
                    <div className="flex items-center gap-1.5"><Clock size={11} className="text-muted-silver" /><span className="text-[10px] text-muted-silver">Timeout:</span><input type="number" value={stage.timeout} onChange={(e) => updateTimeout(stage.id, Number(e.target.value))} className="glass-input w-14 rounded px-1.5 py-0.5 text-xs text-ghost-white font-mono text-center" /><span className="text-[10px] text-muted-silver">s</span></div>
                    <div className="flex items-center gap-1.5"><RefreshCw size={11} className="text-muted-silver" /><span className="text-[10px] text-muted-silver">Retries:</span><input type="number" value={stage.retries} min={0} max={5} onChange={(e) => updateRetries(stage.id, Number(e.target.value))} className="glass-input w-12 rounded px-1.5 py-0.5 text-xs text-ghost-white font-mono text-center" /></div>
                  </div>
                )}
              </div>
              <button onClick={() => toggle(stage.id)}>{stage.enabled ? <ToggleRight size={22} className="text-neon-emerald" /> : <ToggleLeft size={22} className="text-muted-silver/40" />}</button>
            </div>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}
