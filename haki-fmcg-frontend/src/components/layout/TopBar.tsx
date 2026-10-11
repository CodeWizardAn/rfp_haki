import { useMemo } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
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

  const userInitials = useMemo(() => {
    if (!user?.full_name) return 'PM';
    const parts = user.full_name.trim().split(/\s+/).filter(Boolean);
    const first = parts[0] || 'P';
    if (parts.length === 1) return first.slice(0, 2).toUpperCase();
    const last = parts[parts.length - 1] || 'M';
    return ((first[0] || 'P') + (last[0] || 'M')).toUpperCase();
  }, [user?.full_name]);

  const handleLogout = async () => {
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
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-500 hover:text-slate-900 border border-slate-200 hover:border-slate-300 transition-all shadow-sm"
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
          className="relative p-2 rounded-lg text-slate-500 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 transition-all shadow-sm"
        >
          <Bell size={16} />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-[16px] rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center px-1">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* User Profile & Sign Out */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-200/80">
          <div className="flex items-center gap-2.5">
            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-semibold text-xs flex items-center justify-center flex-shrink-0 shadow-sm ring-1 ring-black/5 select-none">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
              ) : (
                <span>{userInitials}</span>
              )}
            </div>

            {/* User Name & Role */}
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-xs font-semibold text-slate-900 leading-tight whitespace-nowrap">
                {user?.full_name || 'Procurement Manager'}
              </span>
              <span className="text-[11px] text-slate-500 capitalize leading-tight mt-0.5">
                {user?.role || 'manager'}
              </span>
            </div>
          </div>

          {/* Sign Out Action Button */}
          <button
            onClick={handleLogout}
            title="Sign out"
            aria-label="Sign out"
            className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 active:bg-red-100 transition-colors ml-0.5"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
