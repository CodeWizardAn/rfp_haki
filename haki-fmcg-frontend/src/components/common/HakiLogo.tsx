import React from 'react';
import { motion } from 'framer-motion';

export interface HakiLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  subtitle?: string;
  variant?: 'default' | 'tile';
  onDark?: boolean;
  className?: string;
  animate?: boolean;
}

const sizeConfig = {
  xs: { mark: 22, text: 'text-sm font-extrabold', badge: 'text-[9px] px-1 py-0.2', sub: 'text-[9px]' },
  sm: { mark: 28, text: 'text-base font-extrabold', badge: 'text-[10px] px-1.5 py-0.5', sub: 'text-[10.5px]' },
  md: { mark: 36, text: 'text-lg font-extrabold', badge: 'text-[11px] px-2 py-0.5', sub: 'text-xs' },
  lg: { mark: 48, text: 'text-2xl font-extrabold', badge: 'text-xs px-2.5 py-1', sub: 'text-sm' },
  xl: { mark: 64, text: 'text-3xl font-extrabold', badge: 'text-xs px-3 py-1', sub: 'text-sm' },
};

export const HakiLogo: React.FC<HakiLogoProps> = ({
  size = 'md',
  showText = false,
  subtitle,
  variant = 'default',
  onDark = false,
  className = '',
  animate = true,
}) => {
  const cfg = sizeConfig[size];

  // Resolve fill colors explicitly based on variant & onDark background
  const rightPillarColor = variant === 'tile' || onDark ? '#FFFFFF' : '#0F172A';
  const textColor = onDark ? 'text-white' : 'text-[#0F172A]';
  const badgeClasses = onDark
    ? 'bg-blue-900/60 text-blue-200 border-blue-700/60'
    : 'bg-[#EFF6FF] text-[#2563EB] border-[#BFDBFE]';
  const subColor = onDark ? 'text-slate-300' : 'text-[#64748B]';

  const MarkSvg = (
    <svg
      width={cfg.mark}
      height={cfg.mark}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="flex-shrink-0 transition-transform duration-200 group-hover:scale-105"
    >
      {variant === 'tile' && (
        <rect width="100" height="100" rx="24" fill="#0F172A" />
      )}

      {/* Left Pillar + Diagonal Crossbar: Electric Blue (#2563EB) */}
      <path
        d="
          M 22 22
          C 22 17.6 25.6 14 30 14
          H 30
          C 34.4 14 38 17.6 38 22
          V 42
          H 51.5
          C 52.8 42 53.6 43.2 53.0 44.4
          L 45.0 57.2
          C 44.5 57.7 43.8 58 43.0 58
          H 38
          V 78
          C 38 82.4 34.4 86 30 86
          H 30
          C 25.6 86 22 82.4 22 78
          Z
        "
        fill="#2563EB"
      />

      {/* Right Pillar + Diagonal Crossbar: Deep Slate (#0F172A) on light, White (#FFFFFF) on dark */}
      <path
        d="
          M 78 78
          C 78 82.4 74.4 86 70 86
          H 70
          C 65.6 86 62 82.4 62 78
          V 58
          H 48.5
          C 47.2 58 46.4 56.8 47.0 55.6
          L 55.0 42.8
          C 55.5 42.3 56.2 42 57.0 42
          H 62
          V 22
          C 62 17.6 65.6 14 70 14
          H 70
          C 74.4 14 78 17.6 78 22
          Z
        "
        fill={rightPillarColor}
      />
    </svg>
  );

  return (
    <div className={`inline-flex items-center gap-2.5 select-none group ${className}`}>
      {animate ? (
        <motion.div
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          className="relative flex items-center justify-center flex-shrink-0"
        >
          {MarkSvg}
        </motion.div>
      ) : (
        MarkSvg
      )}

      {showText && (
        <div className="flex flex-col leading-none">
          <div className="flex items-center gap-1.5">
            <span className={`tracking-tight font-extrabold ${textColor} ${cfg.text}`}>
              HAKI
            </span>
            <span
              className={`font-bold tracking-wider rounded border ${badgeClasses} ${cfg.badge}`}
            >
              FMCG 2.0
            </span>
          </div>
          {subtitle && (
            <span className={`font-semibold tracking-wide mt-1 ${subColor} ${cfg.sub}`}>
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default HakiLogo;
