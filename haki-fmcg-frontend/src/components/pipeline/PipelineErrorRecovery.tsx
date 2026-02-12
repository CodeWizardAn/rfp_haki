import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  SkipForward,
  XOctagon,
  Lightbulb,
  Copy,
  Clock,
  Bug,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

interface PipelineError {
  id: string;
  stage: string;
  type: string;
  message: string;
  stackTrace: string;
  timestamp: string;
  retries: number;
  maxRetries: number;
  suggestedFix: string;
  severity: 'critical' | 'warning' | 'info';
}

const demoErrors: PipelineError[] = [
  {
    id: 'ERR-001',
    stage: 'PDF Extraction',
    type: 'FileParseError',
    message: 'Failed to parse PDF: corrupt header at byte 0x4F2A in RFP-2025-156.pdf',
    stackTrace: `Traceback (most recent call last):
  File "pdf_extraction/pdf_text_extractor.py", line 142, in extract_text
    doc = fitz.open(filepath)
  File "fitz/__init__.py", line 315, in open
    raise RuntimeError("cannot open broken document")
RuntimeError: cannot open broken document`,
    timestamp: '2 min ago',
    retries: 1,
    maxRetries: 3,
    suggestedFix: 'Re-download the PDF or use OCR fallback mode. The file may have been truncated during upload.',
    severity: 'critical',
  },
  {
    id: 'ERR-002',
    stage: 'Terms Matching',
    type: 'TimeoutError',
    message: 'Vector similarity search timed out after 30s — ChromaDB collection "rfp_terms" too large',
    stackTrace: `Traceback (most recent call last):
  File "pdf_extraction/rfp_terms_matcher.py", line 89, in match_terms
    results = collection.query(query_embeddings=[emb], n_results=50)
  File "chromadb/api/models/Collection.py", line 301, in query
    raise TimeoutError("Query exceeded 30s limit")
TimeoutError: Query exceeded 30s limit`,
    timestamp: '5 min ago',
    retries: 0,
    maxRetries: 3,
    suggestedFix: 'Reduce n_results from 50 to 20, or enable batched querying in pipeline config.',
    severity: 'warning',
  },
  {
    id: 'ERR-003',
    stage: 'Price Optimization',
    type: 'DataValidationError',
    message: 'Missing required field "unit_price" for 3 line items in bid response',
    stackTrace: `Traceback (most recent call last):
  File "price_optimization.py", line 67, in optimize_prices
    assert all(item.get('unit_price') for item in items)
AssertionError: Missing unit_price in items[2], items[5], items[8]`,
    timestamp: '12 min ago',
    retries: 2,
    maxRetries: 3,
    suggestedFix: 'Run the "Fill Missing Prices" enrichment step before optimization, or set default prices from catalog.',
    severity: 'info',
  },
];

const severityConfig = {
  critical: { color: 'text-coral-flame', bg: 'bg-coral-flame/10', border: 'border-coral-flame/30', label: 'Critical' },
  warning:  { color: 'text-amber-glow', bg: 'bg-amber-glow/10', border: 'border-amber-glow/30', label: 'Warning' },
  info:     { color: 'text-electric-cyan', bg: 'bg-electric-cyan/10', border: 'border-electric-cyan/30', label: 'Info' },
};

export default function PipelineErrorRecovery() {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [actions, setActions] = useState<Record<string, string>>({});

  const handleAction = (errId: string, action: string) => {
    setActions((a) => ({ ...a, [errId]: action }));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <Bug size={16} className="text-coral-flame" />
        <h3 className="text-sm font-semibold text-ghost-white">Error Recovery</h3>
        <Badge variant="solid" color="red" size="sm">{demoErrors.length}</Badge>
      </div>

      {demoErrors.map((err) => {
        const sev = severityConfig[err.severity];
        const isExpanded = expanded === err.id;
        const actionTaken = actions[err.id];
        return (
          <motion.div
            key={err.id}
            layout
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card variant="glass" className={`border ${actionTaken ? 'border-steel-slate/15 opacity-60' : sev.border}`}>
              {/* Header */}
              <button
                className="w-full flex items-start gap-3 p-3 text-left"
                onClick={() => setExpanded(isExpanded ? null : err.id)}
              >
                <div className={`w-8 h-8 rounded-lg ${sev.bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                  <AlertTriangle size={14} className={sev.color} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-ghost-white">{err.stage}</span>
                    <Badge variant="soft" color={err.severity === 'critical' ? 'red' : err.severity === 'warning' ? 'amber' : 'cyan'} size="sm">
                      {sev.label}
                    </Badge>
                    <span className="text-[10px] text-muted-silver font-mono">{err.type}</span>
                    {actionTaken && (
                      <Badge variant="solid" color="teal" size="sm">{actionTaken}</Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-silver mt-0.5 truncate">{err.message}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="flex items-center gap-1 text-[10px] text-muted-silver">
                      <Clock size={10} />{err.timestamp}
                    </span>
                    <span className="text-[10px] text-muted-silver">
                      Retries: {err.retries}/{err.maxRetries}
                    </span>
                  </div>
                </div>
                {isExpanded ? <ChevronUp size={14} className="text-muted-silver mt-1" /> : <ChevronDown size={14} className="text-muted-silver mt-1" />}
              </button>

              {/* Expandable Detail */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="px-3 pb-3 space-y-3">
                      {/* Stack trace */}
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-[10px] font-semibold text-muted-silver uppercase tracking-wider">Stack Trace</p>
                          <button
                            onClick={() => navigator.clipboard.writeText(err.stackTrace)}
                            className="flex items-center gap-1 text-[10px] text-electric-cyan hover:underline"
                          >
                            <Copy size={10} />Copy
                          </button>
                        </div>
                        <pre className="bg-deep-navy/60 rounded-lg p-3 text-[11px] text-coral-flame/80 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed border border-steel-slate/15">
                          {err.stackTrace}
                        </pre>
                      </div>

                      {/* Suggested fix */}
                      <div className="flex items-start gap-2 bg-amber-glow/5 rounded-lg p-2.5 border border-amber-glow/15">
                        <Lightbulb size={14} className="text-amber-glow flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-[10px] font-semibold text-amber-glow mb-0.5">Suggested Fix</p>
                          <p className="text-xs text-muted-silver">{err.suggestedFix}</p>
                        </div>
                      </div>

                      {/* Action buttons */}
                      {!actionTaken && (
                        <div className="flex gap-2 flex-wrap">
                          <Button
                            size="sm"
                            variant="primary"
                            leftIcon={<RotateCcw size={12} />}
                            onClick={() => handleAction(err.id, 'Retrying…')}
                            disabled={err.retries >= err.maxRetries}
                          >
                            Retry ({err.maxRetries - err.retries} left)
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            leftIcon={<SkipForward size={12} />}
                            onClick={() => handleAction(err.id, 'Skipped')}
                          >
                            Skip Stage
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            leftIcon={<XOctagon size={12} />}
                            onClick={() => handleAction(err.id, 'Aborted')}
                            className="text-coral-flame hover:text-coral-flame"
                          >
                            Abort Run
                          </Button>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
