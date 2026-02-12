import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Globe,
  Zap,
  Package,
  BarChart3,
  Clock,
  ChevronLeft,
  ChevronRight,
  Building2,
  FileText,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/user', icon: <LayoutDashboard size={20} /> },
  { label: 'RFP Processing', path: '/user/rfps', icon: <Globe size={20} /> },
  { label: 'RFP Analyzer', path: '/user/rfp-analyzer', icon: <Zap size={20} /> },
  { label: 'Products', path: '/user/products', icon: <Package size={20} /> },
  { label: 'Analytics', path: '/user/analytics', icon: <BarChart3 size={20} /> },
  { label: 'History', path: '/user/history', icon: <Clock size={20} /> },
  { label: 'Company Profiles', path: '/user/profiles', icon: <Building2 size={20} /> },
  { label: 'Bid Generator', path: '/user/bid-generator', icon: <FileText size={20} /> },
];

export function UserSidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const location = useLocation();

  return (
    <motion.aside
      animate={{ width: sidebarCollapsed ? 64 : 240 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed left-0 top-0 h-screen z-40 glass-sidebar flex flex-col"
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-steel-slate/20">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-emerald to-teal-depth flex items-center justify-center flex-shrink-0">
            <Zap size={18} className="text-white" />
          </div>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden whitespace-nowrap"
              >
                <span className="text-h3 text-gradient-cyan font-bold">HAKI</span>
                <span className="text-caption text-muted-silver ml-1">Portal</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto overflow-x-hidden">
        {navItems.map((item) => {
          const isActive =
            location.pathname === item.path ||
            (item.path !== '/user' && location.pathname.startsWith(item.path));

          return (
            <NavLink
              key={item.path}
              to={item.path}
              title={sidebarCollapsed ? item.label : undefined}
              className={cn(
                'group flex items-center gap-3 mx-2 px-3 py-2.5 rounded-lg transition-all duration-200 relative mb-0.5',
                isActive
                  ? 'bg-neon-emerald/10 text-neon-emerald'
                  : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30',
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="user-sidebar-active"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full bg-neon-emerald"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}

              <span className="flex-shrink-0">{item.icon}</span>

              <AnimatePresence>
                {!sidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="text-sm font-medium whitespace-nowrap overflow-hidden"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        className="h-12 flex items-center justify-center border-t border-steel-slate/20 text-muted-silver hover:text-ghost-white hover:bg-steel-slate/20 transition-colors"
      >
        {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </motion.aside>
  );
}
