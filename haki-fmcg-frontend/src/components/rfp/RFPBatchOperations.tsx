import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Trash2, Download, ArrowRightCircle, X, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Button, Badge } from '@/components/ui';

type BatchAction = 'process' | 'status' | 'export' | 'delete';

interface BatchItem {
  id: string;
  title: string;
  status: 'pending' | 'running' | 'success' | 'error';
  message?: string;
}

export default function RFPBatchOperations({
  selectedIds,
  onClear,
}: {
  selectedIds: string[];
  onClear: () => void;
}) {
  const [action, setAction] = useState<BatchAction | null>(null);
  const [running, setRunning] = useState(false);
  const [items, setItems] = useState<BatchItem[]>([]);

  const startBatch = (batchAction: BatchAction) => {
    setAction(batchAction);
    const batchItems: BatchItem[] = selectedIds.map((id) => ({
      id,
      title: `RFP ${id}`,
      status: 'pending',
    }));
    setItems(batchItems);
    setRunning(true);

    // Simulate sequential processing
    batchItems.forEach((item, i) => {
      setTimeout(() => {
        setItems((prev) =>
          prev.map((p) => (p.id === item.id ? { ...p, status: 'running' } : p)),
        );
        setTimeout(() => {
          const success = Math.random() > 0.15; // 85% success rate
          setItems((prev) =>
            prev.map((p) =>
              p.id === item.id
                ? { ...p, status: success ? 'success' : 'error', message: success ? 'Completed' : 'Failed — timeout' }
                : p,
            ),
          );
          if (i === batchItems.length - 1) setRunning(false);
        }, 800 + Math.random() * 400);
      }, i * 1200);
    });
  };

  const completedCount = items.filter((i) => i.status === 'success').length;
  const errorCount = items.filter((i) => i.status === 'error').length;

  if (selectedIds.length === 0) return null;

  return (
    <>
      {/* Floating toolbar */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 20, opacity: 0 }}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 px-5 py-3 rounded-2xl bg-midnight-blue/95 border border-steel-slate/30 backdrop-blur-xl shadow-2xl"
      >
        <Badge variant="solid" color="cyan">{selectedIds.length} selected</Badge>
        <div className="h-5 w-px bg-steel-slate/30" />
        <Button variant="primary" size="sm" leftIcon={<Play size={12} />} onClick={() => startBatch('process')}>
          Process All
        </Button>
        <Button variant="secondary" size="sm" leftIcon={<ArrowRightCircle size={12} />} onClick={() => startBatch('status')}>
          Change Status
        </Button>
        <Button variant="secondary" size="sm" leftIcon={<Download size={12} />} onClick={() => startBatch('export')}>
          Export
        </Button>
        <Button variant="danger" size="sm" leftIcon={<Trash2 size={12} />} onClick={() => startBatch('delete')}>
          Delete
        </Button>
        <div className="h-5 w-px bg-steel-slate/30" />
        <button onClick={onClear} className="text-muted-silver hover:text-ghost-white transition-colors">
          <X size={16} />
        </button>
      </motion.div>

      {/* Progress Modal */}
      <AnimatePresence>
        {action && items.length > 0 && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-deep-navy/70 backdrop-blur-sm z-50"
              onClick={() => !running && setAction(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md bg-midnight-blue border border-steel-slate/30 rounded-2xl shadow-2xl"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-steel-slate/30">
                <div>
                  <h3 className="text-lg font-semibold text-ghost-white capitalize">Batch {action}</h3>
                  <p className="text-xs text-muted-silver mt-0.5">
                    {running ? 'Processing...' : `${completedCount} succeeded, ${errorCount} failed`}
                  </p>
                </div>
                {!running && (
                  <button onClick={() => setAction(null)} className="text-muted-silver hover:text-ghost-white">
                    <X size={18} />
                  </button>
                )}
              </div>

              {/* Progress bar */}
              <div className="px-5 py-3">
                <div className="w-full h-2 rounded-full bg-steel-slate/30">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-electric-cyan to-neon-emerald transition-all duration-500"
                    style={{
                      width: `${((completedCount + errorCount) / items.length) * 100}%`,
                    }}
                  />
                </div>
                <p className="text-xs text-muted-silver mt-1 text-right">
                  {completedCount + errorCount} / {items.length}
                </p>
              </div>

              {/* Items */}
              <div className="px-5 pb-5 max-h-64 overflow-y-auto space-y-2">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between py-2 px-3 rounded-lg bg-steel-slate/10"
                  >
                    <span className="text-sm text-ghost-white">{item.title}</span>
                    <div className="flex items-center gap-2">
                      {item.status === 'pending' && <span className="text-xs text-muted-silver">Waiting</span>}
                      {item.status === 'running' && <Loader2 size={14} className="text-electric-cyan animate-spin" />}
                      {item.status === 'success' && <CheckCircle2 size={14} className="text-neon-emerald" />}
                      {item.status === 'error' && (
                        <span className="flex items-center gap-1 text-xs text-coral-flame">
                          <XCircle size={14} /> {item.message}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Footer */}
              {!running && (
                <div className="px-5 py-3 border-t border-steel-slate/30 flex justify-end gap-2">
                  {errorCount > 0 && (
                    <Button variant="secondary" size="sm" onClick={() => startBatch(action)}>
                      Retry Failed
                    </Button>
                  )}
                  <Button variant="primary" size="sm" onClick={() => { setAction(null); onClear(); }}>
                    Done
                  </Button>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
