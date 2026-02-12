import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, FolderTree, ChevronRight, ChevronDown, Package, Hash } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface Category { id: string; name: string; count: number; children?: Category[]; }

const tree: Category[] = [
  { id: 'power', name: 'Power Cables', count: 48, children: [
    { id: 'xlpe', name: 'XLPE Insulated', count: 22, children: [
      { id: 'xlpe-lt', name: 'LT (≤1.1kV)', count: 8 },
      { id: 'xlpe-ht', name: 'HT (3.3-33kV)', count: 10 },
      { id: 'xlpe-ehv', name: 'EHV (66-220kV)', count: 4 },
    ]},
    { id: 'pvc-power', name: 'PVC Insulated', count: 14 },
    { id: 'armoured', name: 'Armoured', count: 12 },
  ]},
  { id: 'control', name: 'Control Cables', count: 32, children: [
    { id: 'multicore', name: 'Multicore', count: 18 },
    { id: 'screened', name: 'Screened', count: 14 },
  ]},
  { id: 'instrument', name: 'Instrumentation Cables', count: 24, children: [
    { id: 'paired', name: 'Paired', count: 12 },
    { id: 'triads', name: 'Triads', count: 8 },
    { id: 'multi-pair', name: 'Multi-Pair', count: 4 },
  ]},
  { id: 'fire', name: 'Fire Resistant', count: 18, children: [
    { id: 'fr-ls', name: 'FR-LSH', count: 10 },
    { id: 'fr-xlpe', name: 'FR-XLPE', count: 8 },
  ]},
  { id: 'specialty', name: 'Specialty Cables', count: 12, children: [
    { id: 'solar', name: 'Solar', count: 4 },
    { id: 'marine', name: 'Marine', count: 4 },
    { id: 'mining', name: 'Mining', count: 4 },
  ]},
];

function TreeNode({ cat, depth = 0 }: { cat: Category; depth?: number }) {
  const [open, setOpen] = useState(depth === 0);
  const hasChildren = cat.children && cat.children.length > 0;

  return (
    <div>
      <button onClick={() => hasChildren && setOpen(!open)} className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-steel-slate/10 transition-colors text-left`} style={{ paddingLeft: `${depth * 20 + 12}px` }}>
        {hasChildren ? (open ? <ChevronDown size={12} className="text-muted-silver" /> : <ChevronRight size={12} className="text-muted-silver" />) : <span className="w-3" />}
        {hasChildren ? <FolderTree size={14} className="text-electric-cyan" /> : <Package size={14} className="text-muted-silver" />}
        <span className="text-sm text-ghost-white flex-1">{cat.name}</span>
        <Badge variant="soft" color="cyan" size="sm"><Hash size={8} className="inline" />{cat.count}</Badge>
      </button>
      {open && hasChildren && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
          {cat.children?.map((c) => <TreeNode key={c.id} cat={c} depth={depth + 1} />)}
        </motion.div>
      )}
    </div>
  );
}

export default function CategoryNavigatorPage() {
  const total = tree.reduce((a, c) => a + c.count, 0);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/products" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Category Navigator</h1><p className="text-body text-muted-silver">Browse product hierarchy — {total} total products</p></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card variant="glass" className="p-4">
            <div className="space-y-0.5">
              {tree.map((cat) => <TreeNode key={cat.id} cat={cat} />)}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card variant="glass" className="p-4">
            <h3 className="text-xs font-semibold text-muted-silver mb-3">CATEGORY DISTRIBUTION</h3>
            <div className="space-y-2">
              {tree.map((cat) => (
                <div key={cat.id}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-ghost-white">{cat.name}</span>
                    <span className="text-muted-silver">{cat.count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-steel-slate/20 overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${(cat.count / total) * 100}%` }} transition={{ duration: 0.6 }} className="h-full rounded-full bg-electric-cyan" />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card variant="glass" className="p-4">
            <h3 className="text-xs font-semibold text-muted-silver mb-3">QUICK STATS</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-muted-silver">Total Categories</span><span className="text-ghost-white">{tree.length}</span></div>
              <div className="flex justify-between"><span className="text-muted-silver">Sub-categories</span><span className="text-ghost-white">{tree.reduce((a, c) => a + (c.children?.length ?? 0), 0)}</span></div>
              <div className="flex justify-between"><span className="text-muted-silver">Total Products</span><span className="text-ghost-white">{total}</span></div>
              <div className="flex justify-between"><span className="text-muted-silver">Largest Category</span><span className="text-electric-cyan">Power Cables</span></div>
            </div>
          </Card>
        </div>
      </div>
    </motion.div>
  );
}
