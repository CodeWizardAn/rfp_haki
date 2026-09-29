import React from 'react';
import { motion } from 'framer-motion';

export interface HakiLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  subtitle?: string;
  className?: string;
  animate?: boolean;
}

const sizeMap = {
  xs: { markSize: 24, fontSize: 'text-sm', badgeSize: 'text-[9px] px-1 py-0.2', subSize: 'text-[9px]' },
  sm: { markSize: 32, fontSize: 'text-base font-bold', badgeSize: 'text-[10px] px-1.5 py-0.5', subSize: 'text-[10px]' },
  md: { markSize: 40, fontSize: 'text-lg font-bold', badgeSize: 'text-[11px] px-2 py-0.5', subSize: 'text-xs' },
  lg: { markSize: 52, fontSize: 'text-2xl font-extrabold', badgeSize: 'text-xs px-2.5 py-1', subSize: 'text-sm' },
  xl: { markSize: 64, fontSize: 'text-3xl font-extrabold', badgeSize: 'text-xs px-3 py-1', subSize: 'text-sm' },
};

export const HakiLogo: React.FC<HakiLogoProps> = ({
  size = 'md',
  showText = false,
  subtitle,
  className = '',
  animate = true,
}) => {
  const cfg = sizeMap[size];

  const Mark = (
    <svg
      width={cfg.markSize}
      height={cfg.markSize}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="flex-shrink-0 transition-transform duration-300 group-hover:scale-105"
    >
      <defs>
        {/* Shield background */}
        <linearGradient id={`hl-shield-${size}`} x1="10" y1="10" x2="110" y2="110" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0F172A" />
          <stop offset="50%" stopColor="#0A1124" />
          <stop offset="100%" stopColor="#050B18" />
        </linearGradient>

        {/* Dynamic border glow */}
        <linearGradient id={`hl-border-${size}`} x1="0" y1="0" x2="120" y2="120" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="35%" stopColor="#2563EB" />
          <stop offset="70%" stopColor="#7C3AED" />
          <stop offset="100%" stopColor="#F59E0B" />
        </linearGradient>

        {/* Industrial Copper Cable */}
        <linearGradient id={`hl-copper-${size}`} x1="26" y1="20" x2="48" y2="100" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FBBF24" />
          <stop offset="25%" stopColor="#F59E0B" />
          <stop offset="65%" stopColor="#D97706" />
          <stop offset="100%" stopColor="#B45309" />
        </linearGradient>

        {/* Neural AI Pipeline */}
        <linearGradient id={`hl-neural-${size}`} x1="72" y1="20" x2="94" y2="100" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="40%" stopColor="#2563EB" />
          <stop offset="85%" stopColor="#1D4ED8" />
          <stop offset="100%" stopColor="#7C3AED" />
        </linearGradient>

        {/* Central Energy Crossbar */}
        <linearGradient id={`hl-bridge-${size}`} x1="38" y1="60" x2="82" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#F59E0B" />
          <stop offset="30%" stopColor="#38BDF8" />
          <stop offset="70%" stopColor="#60A5FA" />
          <stop offset="100%" stopColor="#818CF8" />
        </linearGradient>

        {/* Central Nexus Glow */}
        <radialGradient id={`hl-glow-${size}`} cx="60" cy="60" r="16" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="35%" stopColor="#38BDF8" stopOpacity="0.9" />
          <stop offset="75%" stopColor="#2563EB" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Hex-rounded Shield Container */}
      <rect x="8" y="8" width="104" height="104" rx="26" fill={`url(#hl-shield-${size})`} />
      <rect
        x="8"
        y="8"
        width="104"
        height="104"
        rx="26"
        stroke={`url(#hl-border-${size})`}
        strokeWidth="2.5"
        strokeOpacity="0.8"
      />

      {/* Grid Guide */}
      <path d="M22 60 H98 M60 22 V98" stroke="#334155" strokeWidth="1" strokeOpacity="0.25" strokeDasharray="2 3" />

      {/* Left Pillar: Physical Cable & Conductors */}
      <path
        d="M30 25 C30 23.5 31.5 22 33 22 H42 C44 22 45 23.5 45 25 V95 C45 96.5 44 98 42 98 H33 C31.5 98 30 96.5 30 95 Z"
        fill={`url(#hl-copper-${size})`}
      />
      <path d="M31 36 H44 M31 50 H44 M31 70 H44 M31 84 H44" stroke="#FFF" strokeOpacity="0.35" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M34 24 V96" stroke="#FEF08A" strokeOpacity="0.55" strokeWidth="1.5" strokeLinecap="round" />

      {/* Right Pillar: AI Neural Network Trace */}
      <path
        d="M75 25 C75 23.5 76 22 78 22 H87 C88.5 22 90 23.5 90 25 V95 C90 96.5 88.5 98 87 98 H78 C76 98 75 96.5 75 95 Z"
        fill={`url(#hl-neural-${size})`}
      />
      <path d="M76 24 V96" stroke="#93C5FD" strokeOpacity="0.5" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="82.5" cy="33" r="2.5" fill="#FFFFFF" />
      <circle cx="82.5" cy="47" r="2" fill="#BAE6FD" />
      <circle cx="82.5" cy="73" r="2" fill="#BAE6FD" />
      <circle cx="82.5" cy="87" r="2.5" fill="#FFFFFF" />
      <path d="M82.5 33 L88 38 M82.5 87 L77 82" stroke="#60A5FA" strokeWidth="1.5" strokeLinecap="round" />

      {/* Crossbar & Energy Chevron (Interlocking 'H') */}
      <path d="M42 53 H78 V67 H42 Z" fill={`url(#hl-bridge-${size})`} />
      <path
        d="M48 60 L57 60 L62 55 L59 65 L66 60 L73 60"
        stroke="#FFFFFF"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Core Intelligence Nexus */}
      <circle cx="60" cy="60" r="14" fill={`url(#hl-glow-${size})`} />
      <polygon points="60,52 64,60 60,68 56,60" fill="#FFFFFF" />
      <circle cx="60" cy="60" r="2" fill="#2563EB" />
    </svg>
  );

  return (
    <div className={`inline-flex items-center gap-3 select-none group ${className}`}>
      {animate ? (
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative flex items-center justify-center"
        >
          {Mark}
        </motion.div>
      ) : (
        Mark
      )}

      {showText && (
        <div className="flex flex-col leading-tight">
          <div className="flex items-center gap-1.5">
            <span className={`tracking-tight text-slate-900 dark:text-white font-extrabold ${cfg.fontSize}`}>
              HAKI
            </span>
            <span
              className={`font-bold tracking-wider rounded-md bg-blue-50 text-blue-600 border border-blue-200/80 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800 ${cfg.badgeSize}`}
            >
              FMCG 2.0
            </span>
          </div>
          {subtitle && (
            <span className={`text-slate-500 dark:text-slate-400 font-medium tracking-wide ${cfg.subSize}`}>
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default HakiLogo;
