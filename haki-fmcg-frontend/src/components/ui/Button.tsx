import { forwardRef, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'ghost' | 'link';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  iconOnly?: boolean;
  className?: string;
  disabled?: boolean;
  children?: ReactNode;
  onClick?: (e: React.MouseEvent) => void;
  type?: 'button' | 'submit' | 'reset';
  form?: string;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-electric-cyan text-deep-navy hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] active:scale-[0.97] border border-electric-cyan/30',
  secondary:
    'bg-transparent text-ghost-white border border-steel-slate hover:border-electric-cyan/40 hover:bg-steel-slate/30',
  success:
    'bg-neon-emerald text-deep-navy hover:shadow-[0_0_20px_rgba(0,230,138,0.4)] active:scale-[0.97] border border-neon-emerald/30',
  danger:
    'bg-coral-flame text-white hover:shadow-[0_0_20px_rgba(255,71,87,0.4)] active:scale-[0.97] border border-coral-flame/30',
  ghost:
    'bg-transparent text-ghost-white hover:bg-steel-slate/40 border border-transparent',
  link:
    'bg-transparent text-electric-cyan hover:underline underline-offset-4 border-none p-0',
};

const sizeStyles: Record<ButtonSize, string> = {
  xs: 'px-2 py-1 text-xs rounded-md gap-1',
  sm: 'px-3 py-1.5 text-sm rounded-lg gap-1.5',
  md: 'px-4 py-2 text-sm rounded-lg gap-2',
  lg: 'px-6 py-2.5 text-base rounded-xl gap-2',
  xl: 'px-8 py-3 text-lg rounded-xl gap-2.5',
};

const iconOnlySizes: Record<ButtonSize, string> = {
  xs: 'p-1 rounded-md',
  sm: 'p-1.5 rounded-lg',
  md: 'p-2 rounded-lg',
  lg: 'p-2.5 rounded-xl',
  xl: 'p-3 rounded-xl',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      leftIcon,
      rightIcon,
      iconOnly = false,
      className,
      disabled,
      children,
      onClick,
      type = 'button',
      form,
    },
    ref,
  ) => {
    const isDisabled = disabled || loading;

    return (
      <motion.button
        ref={ref}
        type={type}
        form={form}
        whileTap={isDisabled ? undefined : { scale: 0.97 }}
        className={cn(
          'inline-flex items-center justify-center font-medium transition-all duration-200 cursor-pointer select-none',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-electric-cyan/50 focus-visible:ring-offset-2 focus-visible:ring-offset-deep-navy',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
          variantStyles[variant],
          iconOnly ? iconOnlySizes[size] : sizeStyles[size],
          className,
        )}
        disabled={isDisabled}
        onClick={onClick}
      >
        {loading ? (
          <Loader2 className="animate-spin" size={size === 'xs' ? 14 : size === 'sm' ? 16 : 18} />
        ) : (
          leftIcon
        )}
        {!iconOnly && children}
        {!loading && rightIcon}
      </motion.button>
    );
  },
);

Button.displayName = 'Button';
