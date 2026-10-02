import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface BackButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  fallbackUrl?: string;
  label?: string;
  variant?: 'header' | 'floating' | 'inline';
  showLabel?: boolean;
}

export function BackButton({
  fallbackUrl = '/',
  label = 'Back',
  variant = 'header',
  showLabel = true,
  className,
  onClick,
  ...props
}: BackButtonProps) {
  const navigate = useNavigate();

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (onClick) {
      onClick(e);
      return;
    }
    // Check if browser has previous history in this session
    if (window.history.state && window.history.state.idx > 0) {
      navigate(-1);
    } else {
      navigate(fallbackUrl);
    }
  };

  const variantStyles = {
    header:
      'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white/80 hover:bg-white border border-slate-200/90 hover:border-slate-300 shadow-2xs hover:shadow-xs backdrop-blur-xs transition-all duration-150 active:scale-95 group cursor-pointer',
    floating:
      'fixed top-5 left-5 z-50 flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white/90 hover:bg-white border border-slate-200 shadow-xs hover:shadow-sm backdrop-blur-md transition-all duration-150 active:scale-95 group cursor-pointer',
    inline:
      'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 shadow-2xs transition-all duration-150 active:scale-95 group cursor-pointer',
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      title="Go back to previous page"
      aria-label="Go back to previous page"
      className={cn(variantStyles[variant], className)}
      {...props}
    >
      <ArrowLeft
        size={14}
        className="text-slate-500 group-hover:text-slate-900 transition-transform duration-150 group-hover:-translate-x-0.5 shrink-0"
      />
      {showLabel && (
        <span className={variant === 'header' ? 'hidden sm:inline' : 'inline'}>{label}</span>
      )}
    </button>
  );
}
