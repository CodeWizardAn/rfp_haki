import { Clock, Eye, Play, Copy, Trash2 } from 'lucide-react';
import { Card, Badge, Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import { formatCompactCurrency } from '@/utils/formatters';
import { RFP_STATUS_COLORS } from '@/utils/constants';
import type { RFPStatus, Priority } from '@/types';

interface RFPCardProps {
  rfpId: string;
  title: string;
  deadline?: string;
  priority: Priority;
  budget: number;
  status: RFPStatus;
  progress: number;
  vendorsMatched: number;
  onView?: () => void;
  onProcess?: () => void;
  onDuplicate?: () => void;
  onDelete?: () => void;
}

const priorityColor: Record<Priority, { variant: 'solid' | 'soft'; color: any }> = {
  critical: { variant: 'solid', color: 'coral' },
  high: { variant: 'soft', color: 'amber' },
  medium: { variant: 'soft', color: 'cyan' },
  low: { variant: 'soft', color: 'silver' },
};

function getDeadlineLabel(deadline?: string) {
  if (!deadline) return { text: 'No deadline', color: 'text-muted-silver' };
  const now = new Date();
  const due = new Date(deadline);
  const diffDays = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { text: 'Overdue', color: 'text-coral-flame' };
  if (diffDays <= 3) return { text: `${diffDays} days left`, color: 'text-amber-glow' };
  return { text: `${diffDays} days left`, color: 'text-muted-silver' };
}

export function RFPCard({
  rfpId,
  title,
  deadline,
  priority,
  budget,
  status,
  progress,
  vendorsMatched,
  onView,
  onProcess,
  onDuplicate,
  onDelete,
}: RFPCardProps) {
  const deadlineLabel = getDeadlineLabel(deadline);
  const statusColors = RFP_STATUS_COLORS[status] ?? RFP_STATUS_COLORS.draft;
  const priorityStyle = priorityColor[priority];

  return (
    <Card variant="glass" className="p-0 overflow-hidden">
      <div className="flex">
        <div className={cn('w-1', statusColors.dot)} />
        <div className="flex-1 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs text-muted-silver text-mono-data">{rfpId}</p>
              <h3 className="text-h3 text-ghost-white mt-1">{title}</h3>
            </div>
            <Badge variant={priorityStyle.variant} color={priorityStyle.color}>
              {priority}
            </Badge>
          </div>

          <div className="flex flex-wrap items-center gap-4 mt-3 text-sm">
            <div className="flex items-center gap-1.5">
              <Clock size={14} className={deadlineLabel.color} />
              <span className={deadlineLabel.color}>{deadlineLabel.text}</span>
            </div>
            <div className="text-muted-silver">💰 {formatCompactCurrency(budget)}</div>
            <div className="text-muted-silver">👥 {vendorsMatched} vendors</div>
          </div>

          <div className="mt-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-muted-silver">Matching Progress</span>
              <span className="text-ghost-white font-medium">{progress}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-steel-slate/40">
              <div
                className="h-full rounded-full gradient-pipeline"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div className={cn('inline-flex items-center gap-2 text-xs px-2 py-1 rounded-full', statusColors.bg, statusColors.text)}>
              <span className={cn('w-2 h-2 rounded-full', statusColors.dot)} />
              {status}
            </div>
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" leftIcon={<Eye size={14} />} onClick={onView}>
                View
              </Button>
              <Button variant="primary" size="sm" leftIcon={<Play size={14} />} onClick={onProcess}>
                Process
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<Copy size={14} />} onClick={onDuplicate}>
                Duplicate
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<Trash2 size={14} />} onClick={onDelete}>
                Delete
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
