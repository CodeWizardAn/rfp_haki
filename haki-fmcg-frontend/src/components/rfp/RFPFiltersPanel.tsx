import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SlidersHorizontal, X, Save, RotateCcw } from 'lucide-react';
import { Button, Badge } from '@/components/ui';

interface FilterState {
  statuses: string[];
  priorities: string[];
  dateRange: { from: string; to: string };
  budgetMin: number;
  budgetMax: number;
  sources: string[];
  tags: string[];
}

const defaultFilters: FilterState = {
  statuses: [],
  priorities: [],
  dateRange: { from: '', to: '' },
  budgetMin: 0,
  budgetMax: 50000000,
  sources: [],
  tags: [],
};

const statusOptions = ['draft', 'extracting', 'matching', 'pricing', 'review', 'submitted', 'awarded', 'closed'];
const priorityOptions = ['critical', 'high', 'medium', 'low'];
const sourceOptions = ['pdf_upload', 'url_scan', 'manual'];
const tagOptions = ['wire', 'cable', 'xlpe', 'lt-cable', 'ht-cable', 'industrial', 'domestic', 'zone-east', 'zone-west', 'zone-north', 'zone-south'];

export default function RFPFiltersPanel({
  open,
  onClose,
  onApply,
}: {
  open: boolean;
  onClose: () => void;
  onApply: (filters: FilterState) => void;
}) {
  const [filters, setFilters] = useState<FilterState>(defaultFilters);
  const [tagInput, setTagInput] = useState('');

  const toggleItem = (key: 'statuses' | 'priorities' | 'sources', value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: prev[key].includes(value)
        ? prev[key].filter((v) => v !== value)
        : [...prev[key], value],
    }));
  };

  const addTag = (tag: string) => {
    if (tag && !filters.tags.includes(tag)) {
      setFilters((prev) => ({ ...prev, tags: [...prev.tags, tag] }));
    }
    setTagInput('');
  };

  const removeTag = (tag: string) => {
    setFilters((prev) => ({ ...prev, tags: prev.tags.filter((t) => t !== tag) }));
  };

  const activeCount = [
    filters.statuses.length,
    filters.priorities.length,
    filters.dateRange.from || filters.dateRange.to ? 1 : 0,
    filters.budgetMin > 0 || filters.budgetMax < 50000000 ? 1 : 0,
    filters.sources.length,
    filters.tags.length,
  ].reduce((a, b) => a + b, 0);

  const filteredTagSuggestions = tagOptions.filter(
    (t) => t.includes(tagInput.toLowerCase()) && !filters.tags.includes(t),
  );

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-deep-navy/60 backdrop-blur-sm z-40"
            onClick={onClose}
          />
          {/* Slide-in Panel */}
          <motion.aside
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed top-0 right-0 h-full w-full max-w-sm bg-midnight-blue border-l border-steel-slate/30 z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-steel-slate/30">
              <div className="flex items-center gap-2">
                <SlidersHorizontal size={18} className="text-electric-cyan" />
                <h3 className="text-lg font-semibold text-ghost-white">Filters</h3>
                {activeCount > 0 && (
                  <Badge variant="solid" color="cyan" size="sm">{activeCount}</Badge>
                )}
              </div>
              <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-steel-slate/20 text-muted-silver transition-colors">
                <X size={18} />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
              {/* Status */}
              <div>
                <p className="text-xs text-muted-silver uppercase tracking-wider mb-2">Status</p>
                <div className="flex flex-wrap gap-1.5">
                  {statusOptions.map((s) => (
                    <button
                      key={s}
                      onClick={() => toggleItem('statuses', s)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-all ${
                        filters.statuses.includes(s)
                          ? 'bg-electric-cyan/20 text-electric-cyan ring-1 ring-electric-cyan/40'
                          : 'bg-steel-slate/15 text-muted-silver hover:bg-steel-slate/25'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Priority */}
              <div>
                <p className="text-xs text-muted-silver uppercase tracking-wider mb-2">Priority</p>
                <div className="flex flex-wrap gap-1.5">
                  {priorityOptions.map((p) => {
                    const colors: Record<string, string> = {
                      critical: 'bg-coral-flame/20 text-coral-flame ring-coral-flame/40',
                      high: 'bg-amber-glow/20 text-amber-glow ring-amber-glow/40',
                      medium: 'bg-electric-cyan/20 text-electric-cyan ring-electric-cyan/40',
                      low: 'bg-neon-emerald/20 text-neon-emerald ring-neon-emerald/40',
                    };
                    return (
                      <button
                        key={p}
                        onClick={() => toggleItem('priorities', p)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-all ${
                          filters.priorities.includes(p)
                            ? `${colors[p]} ring-1`
                            : 'bg-steel-slate/15 text-muted-silver hover:bg-steel-slate/25'
                        }`}
                      >
                        {p}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Date Range */}
              <div>
                <p className="text-xs text-muted-silver uppercase tracking-wider mb-2">Deadline Range</p>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="date"
                    value={filters.dateRange.from}
                    onChange={(e) => setFilters((p) => ({ ...p, dateRange: { ...p.dateRange, from: e.target.value } }))}
                    className="px-3 py-2 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm focus:outline-none focus:border-electric-cyan/50"
                  />
                  <input
                    type="date"
                    value={filters.dateRange.to}
                    onChange={(e) => setFilters((p) => ({ ...p, dateRange: { ...p.dateRange, to: e.target.value } }))}
                    className="px-3 py-2 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm focus:outline-none focus:border-electric-cyan/50"
                  />
                </div>
              </div>

              {/* Budget Range */}
              <div>
                <p className="text-xs text-muted-silver uppercase tracking-wider mb-2">Budget Range</p>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs text-muted-silver">
                    <span>₹{(filters.budgetMin / 100000).toFixed(0)}L</span>
                    <span>₹{(filters.budgetMax / 100000).toFixed(0)}L</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={50000000}
                    step={500000}
                    value={filters.budgetMax}
                    onChange={(e) => setFilters((p) => ({ ...p, budgetMax: Number(e.target.value) }))}
                    className="w-full accent-electric-cyan"
                  />
                </div>
              </div>

              {/* Source Type */}
              <div>
                <p className="text-xs text-muted-silver uppercase tracking-wider mb-2">Source Type</p>
                <div className="flex flex-wrap gap-1.5">
                  {sourceOptions.map((s) => (
                    <button
                      key={s}
                      onClick={() => toggleItem('sources', s)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                        filters.sources.includes(s)
                          ? 'bg-violet-pulse/20 text-violet-pulse ring-1 ring-violet-pulse/40'
                          : 'bg-steel-slate/15 text-muted-silver hover:bg-steel-slate/25'
                      }`}
                    >
                      {s === 'pdf_upload' ? 'PDF Upload' : s === 'url_scan' ? 'URL Scan' : 'Manual'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div>
                <p className="text-xs text-muted-silver uppercase tracking-wider mb-2">Tags</p>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {filters.tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-electric-cyan/15 text-electric-cyan text-xs"
                    >
                      {tag}
                      <button onClick={() => removeTag(tag)} className="hover:text-ghost-white">
                        <X size={10} />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="relative">
                  <input
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addTag(tagInput)}
                    placeholder="Type to add tags…"
                    className="w-full px-3 py-2 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50"
                  />
                  {tagInput && filteredTagSuggestions.length > 0 && (
                    <div className="absolute z-10 top-full mt-1 w-full bg-deep-navy border border-steel-slate/30 rounded-lg max-h-32 overflow-y-auto">
                      {filteredTagSuggestions.map((tag) => (
                        <button
                          key={tag}
                          onClick={() => addTag(tag)}
                          className="w-full text-left px-3 py-1.5 text-xs text-muted-silver hover:text-ghost-white hover:bg-steel-slate/15 transition-colors"
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-5 py-4 border-t border-steel-slate/30 flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                leftIcon={<RotateCcw size={12} />}
                onClick={() => setFilters(defaultFilters)}
                className="mr-auto"
              >
                Clear All
              </Button>
              <Button variant="secondary" size="sm" leftIcon={<Save size={12} />}>Save Preset</Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => { onApply(filters); onClose(); }}
              >
                Apply Filters
              </Button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
