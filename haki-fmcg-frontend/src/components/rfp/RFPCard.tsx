import { Clock, Copy, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatCompactCurrency } from '@/utils/formatters';
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

function getDeadlineLabel(deadline?: string) {
  if (!deadline) return { text: 'No deadline set', isOverdue: false };
  const now = new Date();
  const due = new Date(deadline);
  const diffDays = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { text: `Overdue by ${Math.abs(diffDays)}d`, isOverdue: true };
  if (diffDays === 0) return { text: 'Due today', isOverdue: false };
  if (diffDays === 1) return { text: '1 day left', isOverdue: false };
  return { text: `${diffDays} days left`, isOverdue: false };
}

export function RFPCard({
  rfpId,
  title,
  deadline,
  priority: _priority,
  budget,
  status: _status,
  progress,
  vendorsMatched,
  onView,
  onProcess,
  onDuplicate,
  onDelete,
}: RFPCardProps) {
  const deadlineLabel = getDeadlineLabel(deadline);

  return (
    <div className="group rounded-xl border border-slate-200/80 bg-white p-4 sm:p-5 hover:border-slate-300 hover:shadow-sm transition-all">
      {/* Top Metadata Row: Tender ID & Deadline */}
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="font-mono text-[11px] font-semibold text-slate-400 tracking-wider uppercase">
          {rfpId}
        </span>

        <div className="flex items-center gap-1 text-[11px] text-slate-400">
          <Clock size={11} className={deadlineLabel.isOverdue ? 'text-red-500' : 'text-slate-400'} />
          <span className={deadlineLabel.isOverdue ? 'font-medium text-red-600' : 'text-slate-500'}>
            {deadlineLabel.text}
          </span>
        </div>
      </div>

      {/* Main Row: Title & Inline Spec Match (No box) */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2.5">
        <h3
          onClick={onView}
          className="text-[15px] sm:text-base font-semibold text-slate-900 group-hover:text-blue-600 transition-colors cursor-pointer leading-snug tracking-tight"
        >
          {title}
        </h3>

        {/* Clean inline spec match bar without any outer gray container */}
        <div className="flex items-center gap-2 flex-shrink-0 sm:ml-4">
          <span className="text-[11px] text-slate-400 font-medium">Spec match</span>
          <div className="w-14 h-1 rounded-full bg-slate-100 overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all duration-300',
                progress >= 80 ? 'bg-emerald-600' : progress >= 40 ? 'bg-blue-600' : 'bg-amber-500'
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="font-mono text-xs font-semibold text-slate-700">{progress}%</span>
        </div>
      </div>

      {/* Bottom Footer: Stats & Refined Minimal Actions */}
      <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>
            <strong className="font-mono font-semibold text-slate-900">{formatCompactCurrency(budget)}</strong>{' '}
            <span className="text-slate-400">budget</span>
          </span>
          <span className="text-slate-300">•</span>
          <span>
            <strong className="font-medium text-slate-800">{vendorsMatched}</strong>{' '}
            <span className="text-slate-400">OEM candidates</span>
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={onDuplicate}
            title="Duplicate"
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded transition-colors cursor-pointer"
          >
            <Copy size={13} />
          </button>
          <button
            type="button"
            onClick={onDelete}
            title="Delete"
            className="p-1.5 text-slate-400 hover:text-red-600 rounded transition-colors cursor-pointer"
          >
            <Trash2 size={13} />
          </button>
          <button
            type="button"
            onClick={onView}
            className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors cursor-pointer ml-1"
          >
            Details
          </button>
          <button
            type="button"
            onClick={onProcess}
            className="px-3 py-1 text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-md transition-colors cursor-pointer ml-1 flex items-center gap-1 active:scale-[0.98]"
          >
            Process
            <span className="text-[11px] leading-none">↗</span>
          </button>
        </div>
      </div>
    </div>
  );
}
