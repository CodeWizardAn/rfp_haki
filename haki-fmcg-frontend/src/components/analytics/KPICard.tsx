import { motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: ReactNode;
  glowColor: 'cyan' | 'emerald' | 'amber' | 'coral' | 'violet';
  onClick?: () => void;
  loading?: boolean;
}

const glowBorderColors: Record<string, string> = {
  cyan: 'border-t-electric-cyan',
  emerald: 'border-t-neon-emerald',
  amber: 'border-t-amber-glow',
  coral: 'border-t-coral-flame',
  violet: 'border-t-violet-pulse',
};

const glowIconBg: Record<string, string> = {
  cyan: 'bg-electric-cyan/15 text-electric-cyan',
  emerald: 'bg-neon-emerald/15 text-neon-emerald',
  amber: 'bg-amber-glow/15 text-amber-glow',
  coral: 'bg-coral-flame/15 text-coral-flame',
  violet: 'bg-violet-pulse/15 text-violet-pulse',
};

export function KPICard({
  title,
  value,
  change,
  changeLabel,
  icon,
  glowColor,
  onClick,
  loading,
}: KPICardProps) {
  if (loading) {
    return (
      <div className={cn('glass-card p-5 border-t-2', glowBorderColors[glowColor])}>
        <div className="space-y-3 animate-pulse">
          <div className="h-4 w-24 bg-steel-slate/40 rounded" />
          <div className="h-8 w-32 bg-steel-slate/40 rounded" />
          <div className="h-3 w-20 bg-steel-slate/40 rounded" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      onClick={onClick}
      className={cn(
        'glass-card p-5 border-t-2 cursor-pointer transition-all duration-300',
        'hover:border-opacity-100 hover:shadow-lg',
        glowBorderColors[glowColor],
        onClick && 'cursor-pointer',
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="text-caption text-muted-silver">{title}</p>
        <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center', glowIconBg[glowColor])}>
          {icon}
        </div>
      </div>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-display text-[32px] text-ghost-white font-bold leading-none mb-2"
      >
        {value}
      </motion.p>

      {change !== undefined && (
        <div className="flex items-center gap-1.5">
          {change >= 0 ? (
            <TrendingUp size={14} className="text-neon-emerald" />
          ) : (
            <TrendingDown size={14} className="text-coral-flame" />
          )}
          <span
            className={cn(
              'text-xs font-medium',
              change >= 0 ? 'text-neon-emerald' : 'text-coral-flame',
            )}
          >
            {change >= 0 ? '+' : ''}
            {change.toFixed(1)}%
          </span>
          {changeLabel && <span className="text-xs text-muted-silver">{changeLabel}</span>}
        </div>
      )}
    </motion.div>
  );
}
