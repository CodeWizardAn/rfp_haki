import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  GitBranch,
  Clock,
  User,
  ArrowUpRight,
  ArrowDownRight,
  RotateCcw,
  Eye,
  ChevronDown,
  ChevronUp,
  MessageSquare,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface PriceChange {
  item: string;
  old: number;
  new: number;
}

interface Revision {
  version: string;
  date: string;
  author: string;
  reason: string;
  requestedBy: string;
  summary: string;
  priceChanges: PriceChange[];
  termsChanged: string[];
  totalOld: number;
  totalNew: number;
}

/* ─── data ─── */
const revisions: Revision[] = [
  {
    version: 'v1.0',
    date: 'Feb 3, 2026 — 10:15 AM',
    author: 'Rajesh Kumar',
    reason: 'Initial bid creation',
    requestedBy: '—',
    summary: 'Initial bid created from RFP-2024-089 requirements. Standard pricing applied.',
    priceChanges: [],
    termsChanged: [],
    totalOld: 0,
    totalNew: 34147000,
  },
  {
    version: 'v1.1',
    date: 'Feb 4, 2026 — 2:30 PM',
    author: 'Priya Sharma',
    reason: 'Manager requested volume discount revision',
    requestedBy: 'Ananya Desai (Manager)',
    summary: 'Applied 5% volume discount on LT Power Cable. Adjusted jointing kit quantity from 120 to 100.',
    priceChanges: [
      { item: 'LT Power Cable 240mm 3.5C XLPE', old: 1850, new: 1758 },
      { item: 'Jointing Kit (Heat Shrink)', old: 540000, new: 450000 },
    ],
    termsChanged: ['Payment terms changed from 30 days to 45 days'],
    totalOld: 34147000,
    totalNew: 32907600,
  },
  {
    version: 'v1.2',
    date: 'Feb 5, 2026 — 11:45 AM',
    author: 'Rajesh Kumar',
    reason: 'Vendor counter-offer adjustment',
    requestedBy: 'Finolex Cables (Vendor)',
    summary: 'Finolex revised cable pricing upward by 2%. Added transit insurance as separate line item.',
    priceChanges: [
      { item: 'LT Power Cable 240mm 3.5C XLPE', old: 1758, new: 1793 },
      { item: 'Transit Insurance (new)', old: 0, new: 85000 },
    ],
    termsChanged: [
      'Added transit insurance clause',
      'Warranty period extended to 24 months from commissioning',
    ],
    totalOld: 32907600,
    totalNew: 33617600,
  },
  {
    version: 'v2.0',
    date: 'Feb 6, 2026 — 4:00 PM',
    author: 'Priya Sharma',
    reason: 'Final approved version',
    requestedBy: 'Director Approval',
    summary: 'Final version after director approval. Minor formatting changes. GST calculation verified.',
    priceChanges: [],
    termsChanged: ['Added force majeure clause as per legal review'],
    totalOld: 33617600,
    totalNew: 33617600,
  },
];

function formatINR(n: number) {
  if (n === 0) return '—';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
}

function pctChange(oldV: number, newV: number) {
  if (oldV === 0) return null;
  return ((newV - oldV) / oldV * 100).toFixed(1);
}

export default function BidRevisionHistoryPage() {
  const { id } = useParams();
  const [expanded, setExpanded] = useState<string | null>('v1.2');
  const [compareMode, setCompareMode] = useState(false);
  const [compareA, setCompareA] = useState('v1.1');
  const [compareB, setCompareB] = useState('v1.2');

  const revA = revisions.find((r) => r.version === compareA);
  const revB = revisions.find((r) => r.version === compareB);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to={id ? `/bids/${id}` : '/bids'} className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Revision History</h1>
            <p className="text-body text-muted-silver">BID-2026-001 — {revisions.length} versions</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant={compareMode ? 'primary' : 'secondary'} size="sm" leftIcon={<GitBranch size={13} />} onClick={() => setCompareMode(!compareMode)}>
            {compareMode ? 'Exit Compare' : 'Compare Versions'}
          </Button>
        </div>
      </div>

      {/* Compare Mode */}
      <AnimatePresence>
        {compareMode && revA && revB && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <Card variant="glass" className="p-4 space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-xs text-muted-silver">From:</span>
                  <select value={compareA} onChange={(e) => setCompareA(e.target.value)} className="glass-input rounded-lg px-2 py-1 text-xs text-ghost-white bg-transparent">
                    {revisions.map((r) => <option key={r.version} value={r.version}>{r.version}</option>)}
                  </select>
                </div>
                <span className="text-muted-silver">→</span>
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-xs text-muted-silver">To:</span>
                  <select value={compareB} onChange={(e) => setCompareB(e.target.value)} className="glass-input rounded-lg px-2 py-1 text-xs text-ghost-white bg-transparent">
                    {revisions.map((r) => <option key={r.version} value={r.version}>{r.version}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                {[revA, revB].map((rev) => (
                  <div key={rev.version} className="p-3 rounded-lg bg-steel-slate/8 border border-steel-slate/15">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="soft" color="cyan" size="sm">{rev.version}</Badge>
                      <span className="text-xs text-muted-silver">{rev.date}</span>
                    </div>
                    <p className="text-xs text-ghost-white mb-1">{rev.summary}</p>
                    <div className="text-xs font-mono text-ghost-white mt-2">Total: {formatINR(rev.totalNew)}</div>
                  </div>
                ))}
              </div>

              {/* Diff */}
              {revA.totalNew !== revB.totalNew && (
                <div className="flex items-center gap-3 p-2 rounded-lg bg-steel-slate/8">
                  <span className="text-xs text-muted-silver">Price Delta:</span>
                  <span className={`text-sm font-bold font-mono ${revB.totalNew > revA.totalNew ? 'text-coral-flame' : 'text-neon-emerald'}`}>
                    {revB.totalNew > revA.totalNew ? '+' : ''}{formatINR(revB.totalNew - revA.totalNew)}
                  </span>
                  <span className={`text-xs ${revB.totalNew > revA.totalNew ? 'text-coral-flame' : 'text-neon-emerald'}`}>
                    ({revB.totalNew > revA.totalNew ? '+' : ''}{pctChange(revA.totalNew, revB.totalNew)}%)
                  </span>
                </div>
              )}
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-[22px] top-4 bottom-4 w-px bg-steel-slate/20" />

        <div className="space-y-3">
          {revisions.map((rev, i) => {
            const isExpanded = expanded === rev.version;
            const isLatest = i === revisions.length - 1;
            const totalDelta = rev.totalNew - rev.totalOld;
            const totalPct = pctChange(rev.totalOld, rev.totalNew);

            return (
              <div key={rev.version} className="relative pl-12">
                {/* Timeline dot */}
                <div className={`absolute left-3 top-4 w-4 h-4 rounded-full border-2 flex items-center justify-center ${isLatest ? 'border-neon-emerald bg-neon-emerald/20' : 'border-electric-cyan bg-electric-cyan/10'}`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${isLatest ? 'bg-neon-emerald' : 'bg-electric-cyan'}`} />
                </div>

                <Card variant="glass" className="overflow-hidden">
                  <button
                    onClick={() => setExpanded(isExpanded ? null : rev.version)}
                    className="w-full text-left p-3 flex items-start gap-3"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <Badge variant={isLatest ? 'success' : 'soft'} color={isLatest ? 'green' : 'cyan'} size="sm">{rev.version}</Badge>
                        {isLatest && <Badge variant="success" size="sm">Current</Badge>}
                        <span className="text-[10px] text-muted-silver flex items-center gap-1"><Clock size={9} />{rev.date}</span>
                      </div>
                      <p className="text-xs text-ghost-white">{rev.reason}</p>
                      <div className="flex items-center gap-3 mt-1 text-[10px] text-muted-silver">
                        <span className="flex items-center gap-0.5"><User size={9} />{rev.author}</span>
                        {rev.requestedBy !== '—' && <span>Requested by: {rev.requestedBy}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      {totalDelta !== 0 && rev.totalOld > 0 && (
                        <span className={`text-xs font-mono font-semibold flex items-center gap-0.5 ${totalDelta > 0 ? 'text-coral-flame' : 'text-neon-emerald'}`}>
                          {totalDelta > 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                          {totalPct}%
                        </span>
                      )}
                      {isExpanded ? <ChevronUp size={14} className="text-muted-silver" /> : <ChevronDown size={14} className="text-muted-silver" />}
                    </div>
                  </button>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-steel-slate/10">
                        <div className="p-4 space-y-4">
                          {/* Summary */}
                          <div>
                            <span className="text-[10px] text-muted-silver block mb-1">Summary</span>
                            <p className="text-xs text-ghost-white/90">{rev.summary}</p>
                          </div>

                          {/* Price Changes */}
                          {rev.priceChanges.length > 0 && (
                            <div>
                              <span className="text-[10px] text-muted-silver block mb-1.5">Price Changes</span>
                              <div className="space-y-1.5">
                                {rev.priceChanges.map((pc) => {
                                  const delta = pc.new - pc.old;
                                  const isIncrease = delta > 0;
                                  return (
                                    <div key={pc.item} className="flex items-center gap-3 p-2 rounded-lg bg-steel-slate/8 text-xs">
                                      <span className="text-ghost-white flex-1 truncate">{pc.item}</span>
                                      {pc.old > 0 && (
                                        <span className="text-muted-silver line-through font-mono">{formatINR(pc.old)}</span>
                                      )}
                                      <span className="text-ghost-white font-mono font-semibold">{formatINR(pc.new)}</span>
                                      <span className={`font-mono text-[10px] ${isIncrease ? 'text-coral-flame' : 'text-neon-emerald'}`}>
                                        {isIncrease ? <ArrowUpRight size={10} className="inline" /> : <ArrowDownRight size={10} className="inline" />}
                                        {pc.old > 0 ? `${pctChange(pc.old, pc.new)}%` : 'New'}
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}

                          {/* Terms Changes */}
                          {rev.termsChanged.length > 0 && (
                            <div>
                              <span className="text-[10px] text-muted-silver block mb-1.5">Terms & Conditions Changes</span>
                              <ul className="space-y-1">
                                {rev.termsChanged.map((t, i) => (
                                  <li key={i} className="flex items-start gap-1.5 text-xs text-ghost-white/80">
                                    <MessageSquare size={10} className="text-amber-glow mt-0.5 flex-shrink-0" />
                                    {t}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Total */}
                          <div className="flex items-center justify-between pt-2 border-t border-steel-slate/10">
                            <span className="text-xs text-muted-silver">Bid Total</span>
                            <div className="flex items-center gap-3">
                              {rev.totalOld > 0 && rev.totalOld !== rev.totalNew && (
                                <span className="text-xs text-muted-silver line-through font-mono">{formatINR(rev.totalOld)}</span>
                              )}
                              <span className="text-sm font-bold text-electric-cyan font-mono">{formatINR(rev.totalNew)}</span>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex gap-2">
                            <Button variant="secondary" size="sm" leftIcon={<Eye size={12} />}>View Document</Button>
                            {!isLatest && (
                              <Button variant="secondary" size="sm" leftIcon={<RotateCcw size={12} />}>Restore Version</Button>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
