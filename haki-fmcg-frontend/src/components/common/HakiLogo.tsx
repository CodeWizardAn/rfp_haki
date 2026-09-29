import React from 'react';
import { Link } from 'react-router-dom';

export interface HakiLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  subtitle?: string;
  onDark?: boolean;
  className?: string;
  collapsed?: boolean;
  showText?: boolean;
  variant?: 'default' | 'tile';
  animate?: boolean;
  asLink?: boolean;
  to?: string;
}

const sizeConfig = {
  xs: {
    haki: 'text-sm font-extrabold',
    divider: 'text-xs',
    fmcg: 'text-[9px] tracking-[0.14em]',
    gap: 'gap-1.5',
    sub: 'text-[9px]',
  },
  sm: {
    haki: 'text-base font-extrabold',
    divider: 'text-sm',
    fmcg: 'text-[10px] tracking-[0.15em]',
    gap: 'gap-2',
    sub: 'text-[10px]',
  },
  md: {
    haki: 'text-xl font-extrabold',
    divider: 'text-lg',
    fmcg: 'text-[11px] tracking-[0.16em]',
    gap: 'gap-2.5',
    sub: 'text-xs',
  },
  lg: {
    haki: 'text-2xl font-extrabold',
    divider: 'text-xl',
    fmcg: 'text-[12px] tracking-[0.16em]',
    gap: 'gap-2.5',
    sub: 'text-xs',
  },
  xl: {
    haki: 'text-3xl sm:text-4xl font-extrabold',
    divider: 'text-2xl sm:text-3xl',
    fmcg: 'text-xs sm:text-sm tracking-[0.18em]',
    gap: 'gap-3',
    sub: 'text-sm',
  },
};

export const HakiLogo: React.FC<HakiLogoProps> = ({
  size = 'md',
  subtitle,
  onDark = false,
  className = '',
  collapsed = false,
  showText = true,
  asLink = false,
  to = '/',
}) => {
  const cfg = sizeConfig[size];
  const isCollapsed = collapsed || showText === false;

  const hakiColor = onDark ? 'text-white' : 'text-slate-900';
  const dividerColor = onDark ? 'text-white/30' : 'text-slate-300';
  const fmcgColor = onDark ? 'text-indigo-400' : 'text-[#4F46E5]';
  const subColor = onDark ? 'text-slate-400' : 'text-slate-500';

  if (isCollapsed) {
    return (
      <div className={`flex items-center justify-center w-full select-none ${className}`}>
        <div className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center font-extrabold text-sm tracking-tight font-sans shadow-xs">
          H
        </div>
      </div>
    );
  }

  const content = (
    <div className={`inline-flex flex-col select-none ${className}`}>
      <div className={`inline-flex items-center ${cfg.gap} leading-none`}>
        <span className={`tracking-tight font-sans ${hakiColor} ${cfg.haki}`}>
          HAKI
        </span>
        <span className={`font-light select-none ${dividerColor} ${cfg.divider}`}>
          |
        </span>
        <span className={`font-bold uppercase font-sans ${fmcgColor} ${cfg.fmcg}`}>
          FMCG 2.0
        </span>
      </div>
      {subtitle && (
        <span className={`font-medium tracking-wide mt-1.5 ${subColor} ${cfg.sub}`}>
          {subtitle}
        </span>
      )}
    </div>
  );

  if (asLink) {
    return (
      <Link to={to} className="inline-flex hover:opacity-90 transition-opacity">
        {content}
      </Link>
    );
  }

  return content;
};

export default HakiLogo;
