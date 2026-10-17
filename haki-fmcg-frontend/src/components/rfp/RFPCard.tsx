import { Clock, Coins, Building2, Play, Copy, Trash2, ArrowUpRight } from 'lucide-react';
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

const priorityStyles: Record<Priority, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200' },
  medium: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  low: { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200' },
};

const statusStyles: Record<string, { bg: string; text: string; dot: string; border: string }> = {
  draft: { bg: 'bg-slate-50', text: 'text-slate-600', dot: 'bg-slate-400', border: 'border-slate-200' },
  scraped: { bg: 'bg-blue-50/60', text: 'text-blue-700', dot: 'bg-blue-500', border: 'border-blue-200/70' },
  extracting: { bg: 'bg-blue-50', text: 'text-blue-700', dot: 'bg-blue-500', border: 'border-blue-200' },
  analyzing: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500', border: 'border-amber-200' },
  analyzed: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', border: 'border-emerald-200' },
  matching: { bg: 'bg-purple-50', text: 'text-purple-700', dot: 'bg-purple-500', border: 'border-purple-200' },
  pricing: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500', border: 'border-amber-200' },
  review: { bg: 'bg-rose-50', text: 'text-rose-700', dot: 'bg-rose-500', border: 'border-rose-200' },
  submitted: { bg: 'bg-blue-50', text: 'text-blue-700', dot: 'bg-blue-600', border: 'border-blue-200' },
  won: { bg: 'bg-emerald-50', text: 'text-emerald-800', dot: 'bg-emerald-600', border: 'border-emerald-200' },
  lost: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500', border: 'border-red-200' },
  cancelled: { bg: 'bg-slate-50', text: 'text-slate-500', dot: 'bg-slate-400', border: 'border-slate-200' },
};

const defaultStatusStyle = { bg: 'bg-slate-50', text: 'text-slate-600', dot: 'bg-slate-400', border: 'border-slate-200' };
const defaultPriorityStyle = { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200' };

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
  const priorityStyle = priorityStyles[priority] ?? defaultPriorityStyle;
  const statusStyle = statusStyles[status] ?? defaultStatusStyle;

  return (
    <div className="group rounded-xl border border-slate-200/90 bg-white p-4 sm:p-5 shadow-[0_1px_3px_rgba(0,0,0,0.03)] hover:shadow-md hover:border-slate-300 transition-all">
      {/* Top Meta Header: Tender ID, Status, Priority, Deadline */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-[11px] font-bold text-slate-700 tracking-wider uppercase bg-slate-100/80 px-2 py-0.5 rounded border border-slate-200/60">
            {rfpId}
          </span>
          <span
            className={cn(
              'text-[10.5px] font-mono font-semibold uppercase tracking-wider px-2 py-0.5 rounded border',
              priorityStyle.bg,
              priorityStyle.text,
              priorityStyle.border
            )}
          >
            {priority} priority
          </span>
          <span
            className={cn(
              'text-[11px] font-medium capitalize px-2 py-0.5 rounded border flex items-center gap-1.5',
              statusStyle.bg,
              statusStyle.text,
              statusStyle.border
            )}
          >
            <span className={cn('w-1.5 h-1.5 rounded-full', statusStyle.dot)} />
            {status}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Clock size={12} className={deadlineLabel.isOverdue ? 'text-red-500' : 'text-slate-400'} />
          <span className={deadlineLabel.isOverdue ? 'font-semibold text-red-600' : 'font-medium text-slate-600'}>
            {deadlineLabel.text}
          </span>
        </div>
      </div>

      {/* Middle Body: Title, Budget, Vendors, Progress */}
      <div className="mt-3.5 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="space-y-1.5 flex-1 min-w-0">
          <h3
            onClick={onView}
            className="text-base sm:text-[17px] font-bold text-slate-900 group-hover:text-blue-600 transition-colors cursor-pointer leading-snug tracking-tight"
          >
            {title}
          </h3>

          <div className="flex items-center gap-3.5 text-xs text-slate-500 flex-wrap pt-0.5">
            <span className="flex items-center gap-1.5">
              <Coins size={13} className="text-slate-400" />
              <span className="font-bold text-slate-900 font-mono">{formatCompactCurrency(budget)}</span>
              <span className="text-slate-400">budget</span>
            </span>
            <span className="text-slate-300">•</span>
            <span className="flex items-center gap-1.5">
              <Building2 size={13} className="text-slate-400" />
              <span className="font-bold text-slate-900">{vendorsMatched}</span>
              <span className="text-slate-400">OEM candidates</span>
            </span>
          </div>
        </div>

        {/* Minimalist Micro Progress Bar */}
        <div className="w-full lg:w-48 bg-slate-50 border border-slate-200/70 p-2.5 rounded-lg flex-shrink-0">
          <div className="flex items-center justify-between text-[11px] mb-1.5">
            <span className="text-slate-500 font-semibold uppercase tracking-wider font-mono text-[10px]">
              Spec Match
            </span>
            <span className="font-mono font-bold text-slate-900 text-xs">{progress}%</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-slate-200/80 overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all duration-500',
                progress >= 80 ? 'bg-emerald-600' : progress >= 40 ? 'bg-blue-600' : 'bg-amber-500'
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Bottom Action Footer */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-end gap-1.5 sm:gap-2">
        <button
          type="button"
          onClick={onDuplicate}
          title="Duplicate tender entry"
          className="p-1.5 sm:p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
        >
          <Copy size={14} />
        </button>
        <button
          type="button"
          onClick={onDelete}
          title="Delete tender entry"
          className="p-1.5 sm:p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
        >
          <Trash2 size={14} />
        </button>
        <div className="h-4 w-px bg-slate-200 mx-1" />
        <button
          type="button"
          onClick={onView}
          className="px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-all cursor-pointer shadow-xs flex items-center gap-1"
        >
          View Details
          <ArrowUpRight size={13} className="text-slate-400" />
        </button>
        <button
          type="button"
          onClick={onProcess}
          className="px-3.5 py-1.5 text-xs font-semibold text-white bg-[#2563EB] hover:bg-[#1D4ED8] rounded-lg transition-all cursor-pointer shadow-xs flex items-center gap-1.5 active:scale-[0.98]"
        >
          <Play size={11} className="fill-white" />
          Process Tender
        </button>
      </div>
    </div>
  );
}
