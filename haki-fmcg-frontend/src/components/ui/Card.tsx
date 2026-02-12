import { type HTMLAttributes, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export type CardVariant = 'default' | 'glass' | 'elevated' | 'outlined' | 'gradient' | 'interactive';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  glowColor?: 'cyan' | 'emerald' | 'amber' | 'coral' | 'violet';
  noPadding?: boolean;
}

const variantStyles: Record<CardVariant, string> = {
  default: 'bg-midnight-blue border border-steel-slate/50 rounded-2xl',
  glass: 'glass-card',
  elevated: 'glass-card-elevated',
  outlined: 'bg-transparent border border-steel-slate rounded-2xl',
  gradient: 'gradient-card border border-steel-slate/30 rounded-2xl',
  interactive:
    'glass-card hover:-translate-y-0.5 hover:border-electric-cyan/25 transition-all duration-300 cursor-pointer',
};

const glowStyles: Record<string, string> = {
  cyan: 'border-t-2 border-t-electric-cyan',
  emerald: 'border-t-2 border-t-neon-emerald',
  amber: 'border-t-2 border-t-amber-glow',
  coral: 'border-t-2 border-t-coral-flame',
  violet: 'border-t-2 border-t-violet-pulse',
};

export function Card({
  variant = 'glass',
  glowColor,
  noPadding = false,
  className,
  children,
  onClick,
}: CardProps & { onClick?: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        variantStyles[variant],
        glowColor && glowStyles[glowColor],
        !noPadding && 'p-5',
        className,
      )}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
}

export function CardHeader({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('mb-4', className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn('text-h3 text-ghost-white', className)} {...props}>
      {children}
    </h3>
  );
}

export function CardDescription({ className, children }: { className?: string; children: ReactNode }) {
  return <p className={cn('text-body text-muted-silver mt-1', className)}>{children}</p>;
}

export function CardContent({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn(className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('mt-4 pt-4 border-t border-steel-slate/30 flex items-center gap-3', className)} {...props}>
      {children}
    </div>
  );
}
