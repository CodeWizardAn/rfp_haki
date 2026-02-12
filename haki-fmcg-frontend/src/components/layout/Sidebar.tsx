import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  FileText,
  GitBranch,
  Bot,
  Package,
  Banknote,
  Building2,
  BarChart3,
  ShieldCheck,
  ClipboardList,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const navSections: { title?: string; items: NavItem[] }[] = [
  {
    items: [
      { label: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
    ],
  },
  {
    title: 'Procurement',
    items: [
      { label: 'RFPs', path: '/rfps', icon: <FileText size={20} /> },
      { label: 'Pipeline', path: '/pipeline', icon: <GitBranch size={20} /> },
      { label: 'Agents', path: '/agents', icon: <Bot size={20} /> },
    ],
  },
  {
    title: 'Management',
    items: [
      { label: 'Products', path: '/products', icon: <Package size={20} /> },
      { label: 'Bids', path: '/bids', icon: <Banknote size={20} /> },
      { label: 'Vendors', path: '/vendors', icon: <Building2 size={20} /> },
    ],
  },
  {
    title: 'Intelligence',
    items: [
      { label: 'Analytics', path: '/analytics', icon: <BarChart3 size={20} /> },
      { label: 'Compliance', path: '/compliance', icon: <ShieldCheck size={20} /> },
      { label: 'Audit Trail', path: '/compliance/audit', icon: <ClipboardList size={20} /> },
    ],
  },
  {
    items: [
      { label: 'Settings', path: '/settings', icon: <Settings size={20} /> },
    ],
  },
];

export function Sidebar() {
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
          <div className="w-8 h-8 rounded-lg gradient-pipeline flex items-center justify-center flex-shrink-0">
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
                <span className="text-caption text-muted-silver ml-1">FMCG</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto overflow-x-hidden">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="mb-2">
            {/* Section title */}
            <AnimatePresence>
              {section.title && !sidebarCollapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-4 py-1.5 text-[10px] uppercase tracking-wider text-muted-silver/60 font-semibold"
                >
                  {section.title}
                </motion.p>
              )}
            </AnimatePresence>

            {section.title && sidebarCollapsed && (
              <div className="mx-auto my-2 w-6 border-t border-steel-slate/30" />
            )}

            {/* Items */}
            {section.items.map((item) => {
              const isActive = location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(item.path));

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  title={sidebarCollapsed ? item.label : undefined}
                  className={cn(
                    'group flex items-center gap-3 mx-2 px-3 py-2 rounded-lg transition-all duration-200 relative',
                    isActive
                      ? 'bg-electric-cyan/10 text-electric-cyan'
                      : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30',
                  )}
                >
                  {/* Active indicator bar */}
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full bg-electric-cyan"
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
          </div>
        ))}
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
