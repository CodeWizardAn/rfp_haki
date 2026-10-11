import { useState, useRef, useEffect, useMemo } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Search, ChevronRight, LogOut } from 'lucide-react';
import { useUIStore, useNotificationStore, useAuthStore } from '@/stores';
import { BackButton } from '@/components/common';

/** Auto-generate breadcrumbs from URL path */
function useBreadcrumbs() {
  const location = useLocation();
  return useMemo(() => {
    const parts = location.pathname.split('/').filter(Boolean);
    return parts.map((part, i) => ({
      label: part.charAt(0).toUpperCase() + part.slice(1).replace(/-/g, ' '),
      path: '/' + parts.slice(0, i + 1).join('/'),
      isLast: i === parts.length - 1,
    }));
  }, [location.pathname]);
}

export function TopBar() {
  const { setCommandPaletteOpen } = useUIStore();
  const { unreadCount } = useNotificationStore();
  const { user, logout } = useAuthStore();
  const breadcrumbs = useBreadcrumbs();
  const navigate = useNavigate();

  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [menuOpen]);

  const userInitials = useMemo(() => {
    if (!user?.full_name) return 'PM';
    const parts = user.full_name.trim().split(/\s+/).filter(Boolean);
    const first = parts[0] || 'P';
    if (parts.length === 1) return first.slice(0, 2).toUpperCase();
    const last = parts[parts.length - 1] || 'M';
    return ((first[0] || 'P') + (last[0] || 'M')).toUpperCase();
  }, [user?.full_name]);

  const handleLogout = async () => {
    setMenuOpen(false);
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 border-b border-black/[0.06] bg-[#FAF8ED]/95 backdrop-blur-md flex items-center justify-between px-4 sm:px-6 sticky top-0 z-30">
      {/* Left: Back button & Breadcrumb */}
      <div className="flex items-center gap-3">
        <BackButton fallbackUrl="/" />
        <nav className="flex items-center gap-1.5 text-xs sm:text-sm">
          <Link to="/" className="text-slate-500 hover:text-slate-900 font-medium transition-colors">
            Home
          </Link>
          {breadcrumbs.map((crumb) => (
            <span key={crumb.path} className="flex items-center gap-1.5">
              <ChevronRight size={13} className="text-slate-400" />
              {crumb.isLast ? (
                <span className="text-slate-900 font-semibold">{crumb.label}</span>
              ) : (
                <Link to={crumb.path} className="text-slate-500 hover:text-slate-900 font-medium transition-colors">
                  {crumb.label}
                </Link>
              )}
            </span>
          ))}
        </nav>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Search trigger */}
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-500 hover:text-slate-900 border border-slate-200 hover:border-slate-300 transition-all shadow-sm cursor-pointer"
        >
          <Search size={14} className="text-slate-400" />
          <span className="hidden md:inline">Search...</span>
          <kbd className="hidden md:inline text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-mono ml-1 border border-slate-200/70">
            ⌘K
          </kbd>
        </button>

        {/* Notifications */}
        <button
          onClick={() => navigate('/bids/notifications')}
          title="View Notifications"
          className="relative p-2 rounded-lg text-slate-500 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 transition-all shadow-sm cursor-pointer"
        >
          <Bell size={16} />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-[16px] rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center px-1">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* Profile Avatar with Click-to-Logout Dropdown */}
        <div ref={menuRef} className="relative pl-2 border-l border-slate-200/80">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            title={user?.full_name || 'Profile menu'}
            aria-label="Profile menu"
            className="w-9 h-9 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs flex items-center justify-center shadow-sm ring-2 ring-white hover:ring-slate-300 transition-all select-none cursor-pointer focus:outline-none"
          >
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
            ) : (
              <span>{userInitials}</span>
            )}
          </button>

          {/* Dropdown Menu */}
          <AnimatePresence>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, y: 6, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.96 }}
                transition={{ duration: 0.15, ease: 'easeOut' }}
                className="absolute right-0 mt-2 w-56 rounded-xl bg-white border border-slate-200/90 shadow-xl py-2 z-50 text-slate-800"
              >
                {/* User Header Details */}
                <div className="px-4 py-2.5 border-b border-slate-100">
                  <p className="text-xs font-bold text-slate-900 leading-tight">
                    {user?.full_name || 'Procurement Manager'}
                  </p>
                  <p className="text-[11px] text-slate-500 capitalize mt-0.5">
                    {user?.role || 'manager'}
                  </p>
                  {user?.email && (
                    <p className="text-[10px] text-slate-400 truncate mt-1">
                      {user.email}
                    </p>
                  )}
                </div>

                {/* Dropdown Options */}
                <div className="pt-1 px-1">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 rounded-lg transition-colors text-left cursor-pointer"
                  >
                    <LogOut size={14} className="text-red-500" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
