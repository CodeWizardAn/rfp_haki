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
    img: 'w-7 h-7',
    text: 'text-base font-extrabold',
    gap: 'gap-2',
    sub: 'text-[9px]',
  },
  sm: {
    img: 'w-9 h-9',
    text: 'text-lg font-extrabold',
    gap: 'gap-2.5',
    sub: 'text-[10px]',
  },
  md: {
    img: 'w-11 h-11',
    text: 'text-xl font-extrabold',
    gap: 'gap-2.5',
    sub: 'text-xs',
  },
  lg: {
    img: 'w-9 h-9 sm:w-11 sm:h-11',
    text: 'text-xl sm:text-2xl font-extrabold',
    gap: 'gap-2.5 sm:gap-3',
    sub: 'text-xs',
  },
  xl: {
    img: 'w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24',
    text: 'text-2xl sm:text-3xl md:text-4xl font-extrabold',
    gap: 'gap-3 sm:gap-4',
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

  const textColor = onDark ? 'text-white' : 'text-slate-900';
  const subColor = onDark ? 'text-slate-400' : 'text-slate-500';

  if (isCollapsed) {
    return (
      <div className={`flex items-center justify-center w-full select-none ${className}`}>
        <img
          src="/haki-mascot.png"
          alt="Haki"
          className="w-9 h-9 object-contain drop-shadow-sm transition-transform hover:scale-105"
        />
      </div>
    );
  }

  const content = (
    <div className={`inline-flex items-center ${cfg.gap} select-none`}>
      <img
        src="/haki-mascot.png"
        alt="Haki Mascot Logo"
        className={`${cfg.img} object-contain flex-shrink-0 drop-shadow-sm transition-transform hover:scale-105`}
      />
      <div className="flex flex-col justify-center leading-none">
        <span className={`tracking-tight font-sans ${textColor} ${cfg.text} inline-flex items-baseline`}>
          <span>Saar</span>
          <span className="text-[#2563EB] dark:text-[#00D4FF] ml-[0.5px]">थी</span>
        </span>
        {subtitle && (
          <span className={`font-medium tracking-wide mt-1 ${subColor} ${cfg.sub}`}>
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );

  if (asLink) {
    return (
      <Link to={to} className={`inline-flex items-center hover:opacity-95 transition-opacity ${className}`}>
        {content}
      </Link>
    );
  }

  return <div className={className}>{content}</div>;
};

export default HakiLogo;
