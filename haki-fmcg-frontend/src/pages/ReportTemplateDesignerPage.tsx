import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, FileText, Plus, Pencil, Copy, Trash2, Download, Layout, BarChart3, Table } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface ReportTemplate { id: string; name: string; description: string; sections: { name: string; type: 'chart' | 'table' | 'kpi' | 'text' }[]; format: 'PDF' | 'Excel' | 'Both'; schedule: string; lastGenerated?: string; }

const initialTemplates: ReportTemplate[] = [
  { id: 'rt-1', name: 'Monthly Procurement Report', description: 'Executive summary of procurement activities, bid outcomes, and spend analysis', sections: [{ name: 'KPI Summary', type: 'kpi' }, { name: 'Bid Performance Chart', type: 'chart' }, { name: 'Spend Breakdown', type: 'chart' }, { name: 'Vendor Rankings', type: 'table' }, { name: 'RFP Status Summary', type: 'table' }], format: 'Both', schedule: 'Monthly (1st)', lastGenerated: '2026-02-01' },
  { id: 'rt-2', name: 'Weekly Pipeline Digest', description: 'Pipeline throughput and agent performance overview', sections: [{ name: 'Pipeline Stats', type: 'kpi' }, { name: 'Throughput Chart', type: 'chart' }, { name: 'Agent Activity', type: 'table' }], format: 'PDF', schedule: 'Weekly (Mon)', lastGenerated: '2026-02-03' },
  { id: 'rt-3', name: 'Vendor Compliance Audit', description: 'Certificate status and compliance gaps across all vendors', sections: [{ name: 'Compliance Overview', type: 'kpi' }, { name: 'Certificate Status', type: 'table' }, { name: 'Expiry Timeline', type: 'chart' }, { name: 'Action Items', type: 'text' }], format: 'PDF', schedule: 'Quarterly', lastGenerated: '2026-01-01' },
  { id: 'rt-4', name: 'Cost Savings Tracker', description: 'Tracks achieved savings vs targets across all procurement categories', sections: [{ name: 'Savings KPIs', type: 'kpi' }, { name: 'Category Savings', type: 'chart' }, { name: 'Vendor Negotiation Results', type: 'table' }], format: 'Excel', schedule: 'Monthly (15th)' },
];

const typeIcon: Record<string, typeof BarChart3> = { chart: BarChart3, table: Table, kpi: Layout, text: FileText };
const typeColor: Record<string, string> = { chart: 'text-electric-cyan', table: 'text-neon-emerald', kpi: 'text-amber-glow', text: 'text-muted-silver' };

export default function ReportTemplateDesignerPage() {
  const [items, setItems] = useState<ReportTemplate[]>(initialTemplates);
  const [selected, setSelected] = useState<string | null>('rt-1');

  const tpl = items.find((t) => t.id === selected);

  const handleNewTemplate = () => {
    const newId = `rt-${Date.now().toString().slice(-4)}`;
    const newTpl: ReportTemplate = {
      id: newId,
      name: `Custom Analytics Report #${items.length + 1}`,
      description: 'Automated executive summary tailored for quarterly stakeholder review.',
      sections: [{ name: 'Executive Overview', type: 'kpi' }, { name: 'Price Trends', type: 'chart' }, { name: 'Tender Outcomes', type: 'table' }],
      format: 'PDF',
      schedule: 'Monthly (End)',
      lastGenerated: 'Never',
    };
    setItems((prev) => [newTpl, ...prev]);
    setSelected(newId);
    toast.success(`Created report template: ${newTpl.name}`);
  };

  const handleDuplicate = (template: ReportTemplate) => {
    const copyId = `rt-${Date.now().toString().slice(-4)}`;
    const copy: ReportTemplate = {
      ...template,
      id: copyId,
      name: `${template.name} (Copy)`,
      lastGenerated: undefined,
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
    toast.success(`Deleted report template "${name}"`);
  };

  const handleGenerateNow = (template: ReportTemplate) => {
    toast.loading(`Compiling and generating ${template.name}...`, { duration: 1500 });
    setTimeout(() => {
      setItems((prev) =>
        prev.map((t) =>
          t.id === template.id
            ? { ...t, lastGenerated: new Date().toISOString().split('T')[0] }
            : t
        )
      );
      toast.success(`${template.name} (${template.format}) compiled and ready for download!`);
    }, 1500);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/analytics" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Report Template Designer</h1><p className="text-body text-muted-silver">Design and schedule automated reports</p></div>
        </div>
        <button
          onClick={handleNewTemplate}
          className="flex items-center gap-2 bg-electric-cyan/20 text-electric-cyan px-4 py-2 rounded-lg hover:bg-electric-cyan/30 cursor-pointer transition-colors text-sm font-medium"
        >
          <Plus size={14} />New Template
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-2">
          {items.map((t) => (
            <Card key={t.id} variant="glass" className={`p-4 cursor-pointer transition-all ${selected === t.id ? 'ring-1 ring-electric-cyan/40' : 'hover:bg-steel-slate/5'}`} onClick={() => setSelected(t.id)}>
              <h3 className="text-sm font-semibold text-ghost-white mb-1">{t.name}</h3>
              <p className="text-[10px] text-muted-silver mb-2 line-clamp-2">{t.description}</p>
              <div className="flex gap-2 text-[10px]">
                <Badge variant="soft" color="cyan" size="sm">{t.format}</Badge>
                <Badge variant="soft" color="teal" size="sm">{t.schedule}</Badge>
                <span className="text-muted-silver">{t.sections.length} sections</span>
              </div>
            </Card>
          ))}
        </div>

        <div className="lg:col-span-2">
          {tpl ? (
            <Card variant="glass" className="p-6 space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-ghost-white">{tpl.name}</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => toast(`Editing parameters for ${tpl.name}`, { icon: '✏️' })}
                    title="Edit Template"
                    className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver hover:text-ghost-white cursor-pointer transition-colors"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => handleDuplicate(tpl)}
                    title="Duplicate Template"
                    className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver hover:text-ghost-white cursor-pointer transition-colors"
                  >
                    <Copy size={14} />
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

              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="p-2 bg-deep-navy/40 rounded-lg"><span className="text-muted-silver block">Format</span><span className="text-ghost-white">{tpl.format}</span></div>
                <div className="p-2 bg-deep-navy/40 rounded-lg"><span className="text-muted-silver block">Schedule</span><span className="text-ghost-white">{tpl.schedule}</span></div>
                <div className="p-2 bg-deep-navy/40 rounded-lg"><span className="text-muted-silver block">Last Generated</span><span className="text-ghost-white">{tpl.lastGenerated ?? 'Never'}</span></div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-muted-silver mb-2">REPORT SECTIONS</h4>
                <div className="space-y-1">
                  {tpl.sections.map((s, i) => {
                    const Icon = typeIcon[s.type] ?? FileText;
                    return (
                      <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-deep-navy/40">
                        <span className="w-6 h-6 rounded bg-steel-slate/20 flex items-center justify-center text-[10px] text-muted-silver font-bold">{i + 1}</span>
                        <Icon size={14} className={typeColor[s.type] ?? 'text-muted-silver'} />
                        <span className="text-sm text-ghost-white flex-1">{s.name}</span>
                        <Badge variant="soft" color="cyan" size="sm">{s.type}</Badge>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => handleGenerateNow(tpl)}
                  className="flex items-center gap-2 bg-neon-emerald/20 text-neon-emerald px-4 py-2 rounded-lg hover:bg-neon-emerald/30 cursor-pointer text-sm font-medium transition-colors"
                >
                  <Download size={14} />Generate Now
                </button>
                <button
                  onClick={() => toast(`Editing layout for ${tpl.name}`, { icon: '📐' })}
                  className="flex items-center gap-2 bg-steel-slate/20 text-ghost-white px-4 py-2 rounded-lg hover:bg-steel-slate/30 cursor-pointer text-sm font-medium transition-colors"
                >
                  <Pencil size={14} />Edit Template
                </button>
              </div>
            </Card>
          ) : (
            <Card variant="glass" className="p-12 flex flex-col items-center justify-center text-center">
              <Layout size={32} className="text-muted-silver/30 mb-3" />
              <p className="text-sm text-muted-silver">Select a template to view or edit</p>
            </Card>
          )}
        </div>
      </div>
    </motion.div>
  );
}
