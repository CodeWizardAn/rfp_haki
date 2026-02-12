import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
  MessageSquare,
  Send,
  PauseCircle,
  RotateCcw,
  Shield,
  User,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { formatCompactCurrency } from '@/utils/formatters';

type ApprovalStatus = 'pending' | 'approved' | 'reviewing' | 'rejected' | 'on_hold';

interface ApprovalLevel {
  level: number;
  role: string;
  name: string;
  status: ApprovalStatus;
  date?: string;
  comment?: string;
}

const statusConfig: Record<ApprovalStatus, { icon: React.ReactNode; color: string; bg: string; badge: string; label: string }> = {
  pending:   { icon: <Clock size={16} />, color: 'text-muted-silver', bg: 'bg-steel-slate/20', badge: 'silver', label: 'Pending' },
  approved:  { icon: <CheckCircle2 size={16} />, color: 'text-neon-emerald', bg: 'bg-neon-emerald/20', badge: 'emerald', label: 'Approved' },
  reviewing: { icon: <Loader2 size={16} className="animate-spin" />, color: 'text-electric-cyan', bg: 'bg-electric-cyan/20', badge: 'cyan', label: 'Reviewing' },
  rejected:  { icon: <XCircle size={16} />, color: 'text-coral-flame', bg: 'bg-coral-flame/20', badge: 'coral', label: 'Rejected' },
  on_hold:   { icon: <PauseCircle size={16} />, color: 'text-amber-glow', bg: 'bg-amber-glow/20', badge: 'amber', label: 'On Hold' },
};

const mockBid = {
  id: 'BID-2026-001',
  rfpId: 'RFP-2026-0001',
  vendor: 'Havells India Ltd',
  amount: 25340000,
  items: 24,
  createdAt: '2026-02-04',
  version: 'v1.2',
};

const mockLevels: ApprovalLevel[] = [
  { level: 1, role: 'Procurement Officer', name: 'Rajesh Kumar', status: 'approved', date: '2026-02-05 10:30', comment: 'Pricing looks good. All items verified against OEM price list.' },
  { level: 2, role: 'Manager', name: 'Priya Sharma', status: 'reviewing', date: '2026-02-06 14:15', comment: 'Reviewing vendor terms and delivery timeline. Need clarification on NRE costs.' },
  { level: 3, role: 'Director', name: 'Amit Patel', status: 'pending' },
  { level: 4, role: 'CFO', name: 'Sunita Reddy', status: 'pending' },
];

interface CommentEntry {
  user: string;
  role: string;
  text: string;
  date: string;
  action?: 'approved' | 'rejected' | 'revision' | 'comment';
}

const mockComments: CommentEntry[] = [
  { user: 'Rajesh Kumar', role: 'Procurement Officer', text: 'Pricing looks good. All items verified against OEM price list.', date: '2026-02-05 10:30', action: 'approved' },
  { user: 'Priya Sharma', role: 'Manager', text: 'Reviewing vendor terms and delivery timeline. Need clarification on NRE costs.', date: '2026-02-06 14:15', action: 'comment' },
  { user: 'Rajesh Kumar', role: 'Procurement Officer', text: 'NRE costs confirmed with vendor — ₹1.2L for tooling + ₹80K for type testing.', date: '2026-02-06 15:40', action: 'comment' },
];

export default function BidApprovalPage() {
  const { bidId } = useParams();
  const [comment, setComment] = useState('');
  const [showConfirm, setShowConfirm] = useState<'approve' | 'reject' | 'revision' | 'hold' | null>(null);

  const progress = mockLevels.filter((l) => l.status === 'approved').length;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Link to="/bids" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div className="p-2 rounded-xl bg-violet-pulse/10">
            <Shield size={24} className="text-violet-pulse" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Approval Workflow</h1>
            <p className="text-body text-muted-silver">{bidId || mockBid.id} — {mockBid.vendor}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Badge variant="soft" color="cyan" size="sm">{mockBid.version}</Badge>
          <Badge variant="soft" color="amber" size="sm">{formatCompactCurrency(mockBid.amount)}</Badge>
        </div>
      </div>

      {/* Approval Flow Visualization */}
      <Card variant="glass">
        <CardHeader>
          <CardTitle>Approval Progress — Level {progress} of {mockLevels.length}</CardTitle>
        </CardHeader>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="w-full h-2 bg-steel-slate/20 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(progress / mockLevels.length) * 100}%` }}
              className="h-full bg-gradient-to-r from-electric-cyan to-neon-emerald rounded-full"
              transition={{ duration: 0.8 }}
            />
          </div>
        </div>

        {/* Nodes */}
        <div className="flex items-start justify-between gap-2 overflow-x-auto pb-4">
          {mockLevels.map((level, idx) => {
            const config = statusConfig[level.status];
            const isActive = level.status === 'reviewing';
            return (
              <div key={level.level} className="flex items-start gap-0 flex-1 min-w-[160px]">
                <div className="flex flex-col items-center flex-1">
                  <motion.div
                    animate={isActive ? { scale: [1, 1.05, 1] } : {}}
                    transition={{ repeat: Infinity, duration: 2 }}
                    className={`w-14 h-14 rounded-2xl ${config.bg} flex items-center justify-center ${
                      isActive ? 'ring-2 ring-electric-cyan/40' : ''
                    }`}
                  >
                    <span className={config.color}>{config.icon}</span>
                  </motion.div>
                  <p className="text-xs font-semibold text-ghost-white mt-2 text-center">{level.role}</p>
                  <p className="text-[10px] text-muted-silver">{level.name}</p>
                  <Badge variant="soft" color={config.badge as any} size="sm" className="mt-1">
                    {config.label}
                  </Badge>
                  {level.date && (
                    <p className="text-[10px] text-muted-silver/60 mt-0.5">{level.date}</p>
                  )}
                </div>
                {idx < mockLevels.length - 1 && (
                  <div className="flex items-center pt-6 px-1">
                    <div className={`w-8 h-0.5 rounded ${
                      level.status === 'approved' ? 'bg-neon-emerald' : 'bg-steel-slate/30'
                    }`} />
                    <div className={`w-0 h-0 border-t-[4px] border-b-[4px] border-l-[6px] border-transparent ${
                      level.status === 'approved' ? 'border-l-neon-emerald' : 'border-l-steel-slate/30'
                    }`} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Comments & History */}
        <div className="lg:col-span-2 space-y-4">
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare size={16} />
                Comments & History
              </CardTitle>
            </CardHeader>
            <div className="space-y-4 max-h-[400px] overflow-y-auto">
              {mockComments.map((c, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 rounded-full bg-steel-slate/30 flex items-center justify-center flex-shrink-0">
                    <User size={14} className="text-muted-silver" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-ghost-white">{c.user}</span>
                      <span className="text-[10px] text-muted-silver">{c.role}</span>
                      {c.action === 'approved' && <Badge variant="soft" color="emerald" size="sm">Approved</Badge>}
                      {c.action === 'rejected' && <Badge variant="soft" color="coral" size="sm">Rejected</Badge>}
                      {c.action === 'revision' && <Badge variant="soft" color="amber" size="sm">Revision</Badge>}
                    </div>
                    <p className="text-sm text-muted-silver mt-1">{c.text}</p>
                    <p className="text-[10px] text-muted-silver/50 mt-1">{c.date}</p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Comment Input */}
            <div className="flex gap-2 mt-4 pt-4 border-t border-steel-slate/20">
              <input
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add a comment…"
                className="flex-1 px-3 py-2 rounded-xl bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50"
              />
              <Button variant="primary" size="sm" leftIcon={<Send size={12} />}>Send</Button>
            </div>
          </Card>
        </div>

        {/* Bid Summary + Actions */}
        <div className="space-y-4">
          <Card variant="glass">
            <CardHeader><CardTitle>Bid Summary</CardTitle></CardHeader>
            <div className="space-y-3">
              {([
                ['Bid ID', mockBid.id],
                ['RFP', mockBid.rfpId],
                ['Vendor', mockBid.vendor],
                ['Amount', formatCompactCurrency(mockBid.amount)],
                ['Items', `${mockBid.items} line items`],
                ['Created', mockBid.createdAt],
                ['Version', mockBid.version],
              ] as [string, string][]).map(([label, value]) => (
                <div key={label} className="flex justify-between text-xs">
                  <span className="text-muted-silver">{label}</span>
                  <span className="text-ghost-white font-medium">{value}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Actions */}
          <Card variant="glass">
            <CardHeader><CardTitle>Actions</CardTitle></CardHeader>
            <div className="space-y-2">
              <Button
                variant="primary"
                className="w-full !bg-neon-emerald/20 !text-neon-emerald hover:!bg-neon-emerald/30"
                leftIcon={<CheckCircle2 size={14} />}
                onClick={() => setShowConfirm('approve')}
              >
                Approve
              </Button>
              <Button
                variant="secondary"
                className="w-full !border-coral-flame/30 !text-coral-flame hover:!bg-coral-flame/10"
                leftIcon={<XCircle size={14} />}
                onClick={() => setShowConfirm('reject')}
              >
                Reject
              </Button>
              <Button
                variant="secondary"
                className="w-full !border-amber-glow/30 !text-amber-glow hover:!bg-amber-glow/10"
                leftIcon={<RotateCcw size={14} />}
                onClick={() => setShowConfirm('revision')}
              >
                Request Revision
              </Button>
              <Button
                variant="secondary"
                className="w-full"
                leftIcon={<PauseCircle size={14} />}
                onClick={() => setShowConfirm('hold')}
              >
                Put on Hold
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {showConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setShowConfirm(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-midnight-blue/95 border border-steel-slate/30 rounded-2xl p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold text-ghost-white mb-2">
                {showConfirm === 'approve' && 'Confirm Approval'}
                {showConfirm === 'reject' && 'Confirm Rejection'}
                {showConfirm === 'revision' && 'Request Revision'}
                {showConfirm === 'hold' && 'Put on Hold'}
              </h3>
              <p className="text-sm text-muted-silver mb-4">
                {showConfirm === 'approve' && `Approve ${mockBid.id} for ${formatCompactCurrency(mockBid.amount)}?`}
                {showConfirm === 'reject' && 'Please provide a reason for rejection (required).'}
                {showConfirm === 'revision' && 'Specify what needs to be changed.'}
                {showConfirm === 'hold' && 'This will pause the approval workflow.'}
              </p>
              <textarea
                placeholder={showConfirm === 'approve' ? 'Optional comment…' : 'Reason / Comment (required)…'}
                rows={3}
                className="w-full px-3 py-2 rounded-xl bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50 mb-4"
              />
              <div className="flex gap-2 justify-end">
                <Button variant="secondary" size="sm" onClick={() => setShowConfirm(null)}>Cancel</Button>
                <Button
                  variant="primary"
                  size="sm"
                  className={
                    showConfirm === 'approve' ? '!bg-neon-emerald !text-deep-navy' :
                    showConfirm === 'reject' ? '!bg-coral-flame !text-white' :
                    showConfirm === 'revision' ? '!bg-amber-glow !text-deep-navy' : ''
                  }
                  onClick={() => setShowConfirm(null)}
                >
                  Confirm
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
