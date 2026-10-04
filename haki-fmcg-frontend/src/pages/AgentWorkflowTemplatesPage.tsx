import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, Copy, Play, Save, FileText, Trash2, Plus, Settings } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface WorkflowTemplate {
  id: string; name: string; description: string; stages: string[]; agentMode: 'standard' | 'agent-driven'; created: string; uses: number;
}

const initialTemplates: WorkflowTemplate[] = [
  { id: 'wt-1', name: 'Standard RFP Processing', description: 'Full 8-stage pipeline for complete RFP analysis', stages: ['PDF Extraction', 'Terms Matching', 'Product Matching', 'Spec Comparison', 'Pricing', 'Compliance', 'Bid Assembly', 'Review'], agentMode: 'standard', created: '2026-01-10', uses: 34 },
  { id: 'wt-2', name: 'Quick Quote', description: 'Fast 3-stage pricing-focused workflow', stages: ['PDF Extraction', 'Product Matching', 'Pricing'], agentMode: 'standard', created: '2026-01-15', uses: 18 },
  { id: 'wt-3', name: 'Agent-Driven Full', description: 'AI agents autonomously handle end-to-end', stages: ['Sales Scan', 'Technical Match', 'Pricing Gen', 'Master Review', 'Delivery'], agentMode: 'agent-driven', created: '2026-01-22', uses: 12 },
  { id: 'wt-4', name: 'Compliance-First', description: 'Prioritizes compliance checking before pricing', stages: ['PDF Extraction', 'Compliance', 'Terms Matching', 'Product Matching', 'Pricing', 'Bid Assembly'], agentMode: 'standard', created: '2026-02-01', uses: 7 },
];

export default function AgentWorkflowTemplatesPage() {
  const [items, setItems] = useState<WorkflowTemplate[]>(initialTemplates);
  const [selected, setSelected] = useState<string | null>('wt-1');
  const navigate = useNavigate();

  const tpl = items.find((t) => t.id === selected);

  const handleCreateNew = () => {
    const newId = `wt-${Date.now().toString().slice(-4)}`;
    const newTpl: WorkflowTemplate = {
      id: newId,
      name: `Custom Agent Workflow ${items.length + 1}`,
      description: 'Custom multi-agent pipeline configured for tender processing.',
      stages: ['Document Parsing', 'Technical Matching', 'Price Calibration', 'Compliance Sign-off'],
      agentMode: 'agent-driven',
      created: new Date().toISOString().split('T')[0] ?? '',
      uses: 0,
    };
    setItems((prev) => [newTpl, ...prev]);
    setSelected(newId);
    toast.success(`Created new template: ${newTpl.name}`);
  };

  const handleDuplicate = (template: WorkflowTemplate) => {
    const copyId = `wt-${Date.now().toString().slice(-4)}`;
    const copy: WorkflowTemplate = {
      ...template,
      id: copyId,
      name: `${template.name} (Copy)`,
      uses: 0,
      created: new Date().toISOString().split('T')[0] ?? '',
    };
    setItems((prev) => [copy, ...prev]);
    setSelected(copyId);
    toast.success(`Duplicated "${template.name}"`);
  };

  const handleDelete = (id: string, name: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
    if (selected === id) {
      setSelected(items.find((t) => t.id !== id)?.id || null);
    }
    toast.success(`Deleted template "${name}"`);
  };

  const handleRun = (template: WorkflowTemplate) => {
    toast.loading(`Launching workflow "${template.name}"...`, { duration: 1200 });
    setTimeout(() => {
      setItems((prev) =>
        prev.map((t) => (t.id === template.id ? { ...t, uses: t.uses + 1 } : t))
      );
      toast.success(`Workflow pipeline active with ${template.stages.length} stages!`);
      navigate('/pipeline');
    }, 1200);
  };

  const handleSave = (template: WorkflowTemplate) => {
    toast.success(`Saved changes to "${template.name}"`);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/agents" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Workflow Templates</h1><p className="text-body text-muted-silver">Create and manage reusable agent workflow templates</p></div>
        </div>
        <button
          onClick={handleCreateNew}
          className="flex items-center gap-2 bg-electric-cyan/20 text-electric-cyan px-4 py-2 rounded-lg hover:bg-electric-cyan/30 cursor-pointer transition-colors text-sm font-medium"
        >
          <Plus size={14} />New Template
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2">
          {items.map((t) => (
            <Card key={t.id} variant="glass" className={`p-4 cursor-pointer transition-all ${selected === t.id ? 'ring-1 ring-electric-cyan/40' : 'hover:bg-steel-slate/5'}`} onClick={() => setSelected(t.id)}>
              <div className="flex items-start justify-between mb-1">
                <h3 className="text-sm font-semibold text-ghost-white">{t.name}</h3>
                <Badge variant="soft" color={t.agentMode === 'agent-driven' ? 'violet' : 'cyan'} size="sm">{t.agentMode}</Badge>
              </div>
              <p className="text-xs text-muted-silver mb-2">{t.description}</p>
              <div className="flex gap-3 text-[10px] text-muted-silver">
                <span><FileText size={10} className="inline mr-0.5" />{t.stages.length} stages</span>
                <span><Play size={10} className="inline mr-0.5" />{t.uses} uses</span>
                <span>{t.created}</span>
              </div>
            </Card>
          ))}
        </div>

        <div className="lg:col-span-2">
          {tpl ? (
            <Card variant="glass" className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-ghost-white">{tpl.name}</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDuplicate(tpl)}
                    title="Duplicate Template"
                    className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver hover:text-ghost-white cursor-pointer transition-colors"
                  >
                    <Copy size={14} />
                  </button>
                  <button
                    onClick={() => toast(`Editing parameters for ${tpl.name}`, { icon: '⚙️' })}
                    title="Template Settings"
                    className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver hover:text-ghost-white cursor-pointer transition-colors"
                  >
                    <Settings size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(tpl.id, tpl.name)}
                    title="Delete Template"
                    className="p-2 rounded-lg hover:bg-coral-flame/10 text-coral-flame cursor-pointer transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <p className="text-sm text-muted-silver">{tpl.description}</p>
              <div>
                <h4 className="text-xs font-semibold text-muted-silver mb-2">PIPELINE STAGES</h4>
                <div className="space-y-1">
                  {tpl.stages.map((s, i) => (
                    <div key={s} className="flex items-center gap-3 p-2 rounded-lg bg-deep-navy/40">
                      <span className="w-6 h-6 rounded-full bg-electric-cyan/10 text-electric-cyan text-xs flex items-center justify-center font-bold">{i + 1}</span>
                      <span className="text-sm text-ghost-white">{s}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => handleRun(tpl)}
                  className="flex items-center gap-2 bg-neon-emerald/20 text-neon-emerald px-4 py-2 rounded-lg hover:bg-neon-emerald/30 cursor-pointer text-sm font-medium transition-colors"
                >
                  <Play size={14} />Run Template
                </button>
                <button
                  onClick={() => handleSave(tpl)}
                  className="flex items-center gap-2 bg-steel-slate/20 text-ghost-white px-4 py-2 rounded-lg hover:bg-steel-slate/30 cursor-pointer text-sm font-medium transition-colors"
                >
                  <Save size={14} />Save Changes
                </button>
              </div>
            </Card>
          ) : (
            <Card variant="glass" className="p-12 flex flex-col items-center justify-center text-center">
              <FileText size={32} className="text-muted-silver/30 mb-3" />
              <p className="text-sm text-muted-silver">Select a template to view details</p>
            </Card>
          )}
        </div>
      </div>
    </motion.div>
  );
}
