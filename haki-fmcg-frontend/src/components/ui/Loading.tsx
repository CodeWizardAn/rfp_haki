import { cn } from '@/lib/utils';

/** Skeleton shimmer for loading states */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-lg bg-steel-slate/40 animate-pulse',
        className,
      )}
      {...props}
    />
  );
}

/** Full-page centered loading spinner */
export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 border-2 border-electric-cyan/30 border-t-electric-cyan rounded-full animate-spin" />
        <p className="text-body text-muted-silver">Loading...</p>
      </div>
    </div>
  );
}

/** Inline spinner */
export function Spinner({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg
      className={cn('animate-spin text-electric-cyan', className)}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

/** Empty state placeholder */
export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center">
      {icon && <div className="mb-4 text-muted-silver">{icon}</div>}
      <h3 className="text-h3 text-ghost-white mb-2">{title}</h3>
      {description && <p className="text-body text-muted-silver max-w-md mb-6">{description}</p>}
      {action}
    </div>
  );
}

/** KPI skeleton card — matches dashboard KPI layout */
export function KPICardSkeleton() {
  return (
    <div className="glass-card p-5 space-y-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-32" />
      <Skeleton className="h-3 w-20" />
    </div>
  );
}
