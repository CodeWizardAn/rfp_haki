import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  GitCompareArrows,
  Check,
  X,
  Minus,
  AlertTriangle,
} from 'lucide-react';
import { Card, Badge } from '@/components/ui';
import { formatCompactCurrency } from '@/utils/formatters';

interface CompareRFP {
  id: string;
  title: string;
  status: string;
  priority: string;
  deadline: string;
  budget: number;
  vendors: number;
  matchScore: number;
  requirements: number;
  source: string;
  category: string;
  stages: number;
  totalStages: number;
  specs: Record<string, string>;
}

const mockRFPs: CompareRFP[] = [
  {
    id: 'RFP-2026-0001',
    title: 'Power Cable Supply — Phase 1',
    status: 'pricing',
    priority: 'high',
    deadline: '2026-02-15',
    budget: 25000000,
    vendors: 3,
    matchScore: 87,
    requirements: 24,
    source: 'pdf_upload',
    category: 'HT Cables',
    stages: 6,
    totalStages: 8,
    specs: {
      'Voltage Rating': '11kV',
      'Conductor Material': 'Copper',
      'Insulation': 'XLPE',
      'Armour': 'Steel Wire',
      'Core Count': '3-Core',
      'Standard': 'IS 7098',
      'Length': '2,500m',
      'Testing': 'Routine + Type',
    },
  },
  {
    id: 'RFP-2026-0005',
    title: 'Power Cable Supply — Phase 2',
    status: 'matching',
    priority: 'medium',
    deadline: '2026-03-01',
    budget: 18000000,
    vendors: 2,
    matchScore: 72,
    requirements: 18,
    source: 'pdf_upload',
    category: 'HT Cables',
    stages: 4,
    totalStages: 8,
    specs: {
      'Voltage Rating': '11kV',
      'Conductor Material': 'Aluminium',
      'Insulation': 'XLPE',
      'Armour': 'Strip Armour',
      'Core Count': '3-Core',
      'Standard': 'IS 7098',
      'Length': '1,800m',
      'Testing': 'Routine Only',
    },
  },
  {
    id: 'RFP-2026-0009',
    title: 'LT Wiring — Factory Expansion',
    status: 'draft',
    priority: 'low',
    deadline: '2026-04-15',
    budget: 8500000,
    vendors: 5,
    matchScore: 91,
    requirements: 12,
    source: 'manual',
    category: 'LT Cables',
    stages: 2,
    totalStages: 8,
    specs: {
      'Voltage Rating': '1.1kV',
      'Conductor Material': 'Copper',
      'Insulation': 'PVC',
      'Armour': 'None',
      'Core Count': 'Multi-core',
      'Standard': 'IS 1554',
      'Length': '5,000m',
      'Testing': 'Routine Only',
    },
  },
];

const statusColors: Record<string, string> = {
  draft: 'silver',
  extracting: 'cyan',
  matching: 'cyan',
  pricing: 'amber',
  review: 'violet',
  completed: 'emerald',
  won: 'emerald',
  lost: 'coral',
};

const priorityColors: Record<string, string> = {
  critical: 'coral',
  high: 'amber',
  medium: 'cyan',
  low: 'silver',
};

export default function RFPComparePage() {
  const [selected, setSelected] = useState<string[]>([mockRFPs[0]!.id, mockRFPs[1]!.id]);
  const compared = mockRFPs.filter((r) => selected.includes(r.id));

  const toggleSelection = (id: string) => {
    if (selected.includes(id)) {
      if (selected.length > 2) setSelected(selected.filter((s) => s !== id));
    } else if (selected.length < 3) {
      setSelected([...selected, id]);
    }
  };

  const allSpecKeys = Array.from(new Set(compared.flatMap((r) => Object.keys(r.specs))));

  const isDifferent = (key: string) => {
    const vals = compared.map((r) => r.specs[key]);
    return new Set(vals).size > 1;
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/rfps" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div className="p-2 rounded-xl bg-violet-pulse/10">
            <GitCompareArrows size={24} className="text-violet-pulse" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Compare RFPs</h1>
            <p className="text-body text-muted-silver">Side-by-side comparison of {compared.length} RFPs</p>
          </div>
        </div>
      </div>

      {/* Selector Bar */}
      <div className="flex gap-2 flex-wrap">
        {mockRFPs.map((rfp) => (
          <button
            key={rfp.id}
            onClick={() => toggleSelection(rfp.id)}
            className={`px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
              selected.includes(rfp.id)
                ? 'bg-electric-cyan/10 border-electric-cyan/40 text-electric-cyan'
                : 'bg-steel-slate/10 border-steel-slate/20 text-muted-silver hover:border-steel-slate/40'
            }`}
          >
            <span className="font-mono">{rfp.id}</span>
            <span className="ml-2 opacity-60">{rfp.title.slice(0, 30)}</span>
          </button>
        ))}
        <span className="text-xs text-muted-silver self-center ml-2">Select 2-3 to compare</span>
      </div>

      {/* Comparison Table */}
      <Card variant="glass" className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-steel-slate/20">
              <th className="py-3 px-4 text-left text-xs font-semibold text-muted-silver uppercase tracking-wider w-40">
                Field
              </th>
              {compared.map((rfp) => (
                <th key={rfp.id} className="py-3 px-4 text-left min-w-[200px]">
                  <span className="text-xs font-mono text-electric-cyan">{rfp.id}</span>
                  <p className="text-xs text-ghost-white mt-0.5 truncate">{rfp.title}</p>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Basic Fields */}
            {([
              { label: 'Status', key: 'status', render: (r: CompareRFP) => <Badge variant="soft" color={(statusColors[r.status] || 'silver') as any} size="sm">{r.status}</Badge> },
              { label: 'Priority', key: 'priority', render: (r: CompareRFP) => <Badge variant="soft" color={(priorityColors[r.priority] || 'silver') as any} size="sm">{r.priority}</Badge> },
              { label: 'Deadline', key: 'deadline', render: (r: CompareRFP) => <span className="text-ghost-white">{r.deadline}</span> },
              { label: 'Budget', key: 'budget', render: (r: CompareRFP) => <span className="text-ghost-white font-bold">{formatCompactCurrency(r.budget)}</span> },
              { label: 'Vendors', key: 'vendors', render: (r: CompareRFP) => <span className="text-ghost-white">{r.vendors}</span> },
              { label: 'Match Score', key: 'matchScore', render: (r: CompareRFP) => (
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-steel-slate/20 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${r.matchScore >= 80 ? 'bg-neon-emerald' : r.matchScore >= 60 ? 'bg-amber-glow' : 'bg-coral-flame'}`} style={{ width: `${r.matchScore}%` }} />
                  </div>
                  <span className="text-ghost-white text-xs">{r.matchScore}%</span>
                </div>
              ) },
              { label: 'Requirements', key: 'requirements', render: (r: CompareRFP) => <span className="text-ghost-white">{r.requirements}</span> },
              { label: 'Source', key: 'source', render: (r: CompareRFP) => <Badge variant="outline" color="cyan" size="sm">{r.source.replace('_', ' ')}</Badge> },
              { label: 'Category', key: 'category', render: (r: CompareRFP) => <span className="text-ghost-white">{r.category}</span> },
              { label: 'Progress', key: 'stages', render: (r: CompareRFP) => (
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-steel-slate/20 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-electric-cyan" style={{ width: `${(r.stages / r.totalStages) * 100}%` }} />
                  </div>
                  <span className="text-xs text-muted-silver">{r.stages}/{r.totalStages}</span>
                </div>
              ) },
            ] as { label: string; key: string; render: (r: CompareRFP) => React.ReactNode }[]).map((field) => {
              const vals = compared.map((r) => String((r as any)[field.key]));
              const diff = new Set(vals).size > 1;
              return (
                <tr key={field.label} className={`border-b border-steel-slate/10 ${diff ? 'bg-amber-glow/5' : ''}`}>
                  <td className="py-3 px-4 text-xs font-medium text-muted-silver">
                    {field.label}
                    {diff && <AlertTriangle size={10} className="text-amber-glow ml-1 inline" />}
                  </td>
                  {compared.map((rfp) => (
                    <td key={rfp.id} className="py-3 px-4">{field.render(rfp)}</td>
                  ))}
                </tr>
              );
            })}

            {/* Specs Section Header */}
            <tr className="bg-steel-slate/10">
              <td colSpan={compared.length + 1} className="py-2 px-4">
                <span className="text-xs font-semibold text-electric-cyan uppercase tracking-wider">Technical Specifications</span>
              </td>
            </tr>
            {allSpecKeys.map((key) => {
              const diff = isDifferent(key);
              return (
                <tr key={key} className={`border-b border-steel-slate/10 ${diff ? 'bg-amber-glow/5' : ''}`}>
                  <td className="py-3 px-4 text-xs font-medium text-muted-silver">
                    {key}
                    {diff && <AlertTriangle size={10} className="text-amber-glow ml-1 inline" />}
                  </td>
                  {compared.map((rfp) => {
                    const val = rfp.specs[key];
                    const others = compared.filter((r) => r.id !== rfp.id).map((r) => r.specs[key]);
                    const matches = others.every((o) => o === val);
                    return (
                      <td key={rfp.id} className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className={`text-sm ${diff ? 'text-ghost-white font-semibold' : 'text-muted-silver'}`}>
                            {val || '—'}
                          </span>
                          {diff && (
                            matches
                              ? <Check size={12} className="text-neon-emerald" />
                              : <Minus size={12} className="text-amber-glow" />
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {/* Summary */}
      <div className="flex gap-4 flex-wrap">
        <Card variant="glass" className="flex-1 min-w-[200px]">
          <div className="flex items-center gap-2 mb-2">
            <Check size={14} className="text-neon-emerald" />
            <span className="text-xs font-semibold text-ghost-white">Similarities</span>
          </div>
          <p className="text-xs text-muted-silver">
            {allSpecKeys.filter((k) => !isDifferent(k)).length} of {allSpecKeys.length} specs match across all selected RFPs.
          </p>
        </Card>
        <Card variant="glass" className="flex-1 min-w-[200px]">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-amber-glow" />
            <span className="text-xs font-semibold text-ghost-white">Differences</span>
          </div>
          <p className="text-xs text-muted-silver">
            {allSpecKeys.filter((k) => isDifferent(k)).length} spec differences found. Highlighted rows show mismatches.
          </p>
        </Card>
        <Card variant="glass" className="flex-1 min-w-[200px]">
          <div className="flex items-center gap-2 mb-2">
            <X size={14} className="text-coral-flame" />
            <span className="text-xs font-semibold text-ghost-white">Duplicate Risk</span>
          </div>
          <p className="text-xs text-muted-silver">
            {allSpecKeys.filter((k) => !isDifferent(k)).length >= allSpecKeys.length * 0.7
              ? 'High similarity — potential duplicate detected.'
              : 'Low similarity — distinct RFPs.'}
          </p>
        </Card>
      </div>
    </motion.div>
  );
}
