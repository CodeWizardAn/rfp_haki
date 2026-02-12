import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export type BadgeVariant = 'solid' | 'soft' | 'outline' | 'dot' | 'pulse' | 'success' | 'danger' | 'default' | 'warning' | 'info';
export type BadgeColor = 'cyan' | 'emerald' | 'amber' | 'coral' | 'violet' | 'rose' | 'teal' | 'silver' | 'green' | 'red' | 'blue' | 'purple';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  color?: BadgeColor;
  size?: 'sm' | 'md';
}

const colorMap: Record<BadgeColor, { solid: string; soft: string; outline: string; dot: string }> = {
  cyan: {
    solid: 'bg-electric-cyan text-deep-navy',
    soft: 'bg-electric-cyan/15 text-electric-cyan',
    outline: 'border-electric-cyan/40 text-electric-cyan',
    dot: 'bg-electric-cyan',
  },
  emerald: {
    solid: 'bg-neon-emerald text-deep-navy',
    soft: 'bg-neon-emerald/15 text-neon-emerald',
    outline: 'border-neon-emerald/40 text-neon-emerald',
    dot: 'bg-neon-emerald',
  },
  amber: {
    solid: 'bg-amber-glow text-deep-navy',
    soft: 'bg-amber-glow/15 text-amber-glow',
    outline: 'border-amber-glow/40 text-amber-glow',
    dot: 'bg-amber-glow',
  },
  coral: {
    solid: 'bg-coral-flame text-white',
    soft: 'bg-coral-flame/15 text-coral-flame',
    outline: 'border-coral-flame/40 text-coral-flame',
    dot: 'bg-coral-flame',
  },
  violet: {
    solid: 'bg-violet-pulse text-white',
    soft: 'bg-violet-pulse/15 text-violet-pulse',
    outline: 'border-violet-pulse/40 text-violet-pulse',
    dot: 'bg-violet-pulse',
  },
  rose: {
    solid: 'bg-rose-pink text-deep-navy',
    soft: 'bg-rose-pink/15 text-rose-pink',
    outline: 'border-rose-pink/40 text-rose-pink',
    dot: 'bg-rose-pink',
  },
  teal: {
    solid: 'bg-teal-depth text-deep-navy',
    soft: 'bg-teal-depth/15 text-teal-depth',
    outline: 'border-teal-depth/40 text-teal-depth',
    dot: 'bg-teal-depth',
  },
  silver: {
    solid: 'bg-muted-silver text-deep-navy',
    soft: 'bg-muted-silver/15 text-muted-silver',
    outline: 'border-muted-silver/40 text-muted-silver',
    dot: 'bg-muted-silver',
  },
  green: {
    solid: 'bg-neon-emerald text-deep-navy',
    soft: 'bg-neon-emerald/15 text-neon-emerald',
    outline: 'border-neon-emerald/40 text-neon-emerald',
    dot: 'bg-neon-emerald',
  },
  red: {
    solid: 'bg-coral-flame text-white',
    soft: 'bg-coral-flame/15 text-coral-flame',
    outline: 'border-coral-flame/40 text-coral-flame',
    dot: 'bg-coral-flame',
  },
  blue: {
    solid: 'bg-electric-cyan text-deep-navy',
    soft: 'bg-electric-cyan/15 text-electric-cyan',
    outline: 'border-electric-cyan/40 text-electric-cyan',
    dot: 'bg-electric-cyan',
  },
  purple: {
    solid: 'bg-violet-pulse text-white',
    soft: 'bg-violet-pulse/15 text-violet-pulse',
    outline: 'border-violet-pulse/40 text-violet-pulse',
    dot: 'bg-violet-pulse',
  },
};

export function Badge({
  variant = 'soft',
  color = 'cyan',
  size = 'sm',
  className,
  children,
  ...props
}: BadgeProps) {
  /* Map semantic variants to soft + color */
  const semanticMap: Record<string, BadgeColor> = { success: 'emerald', danger: 'coral', default: 'silver', warning: 'amber', info: 'cyan' };
  const resolvedColor = semanticMap[variant] ?? color;
  const resolvedVariant = semanticMap[variant] ? 'soft' : variant;
  const colors = colorMap[resolvedColor];
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  if (resolvedVariant === 'dot' || resolvedVariant === 'pulse') {
    return (
      <span
        className={cn('inline-flex items-center gap-1.5', sizeClass, colors.soft, 'rounded-full font-medium', className)}
        {...props}
      >
        <span
          className={cn(
            'w-2 h-2 rounded-full',
            colors.dot,
            resolvedVariant === 'pulse' && 'animate-pulse',
          )}
        />
        {children}
      </span>
    );
  }

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        sizeClass,
        resolvedVariant === 'solid' && colors.solid,
        resolvedVariant === 'soft' && colors.soft,
        resolvedVariant === 'outline' && `border ${colors.outline} bg-transparent`,
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
