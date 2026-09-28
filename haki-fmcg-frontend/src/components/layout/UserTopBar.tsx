import { useMemo } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Bell, Search, User, ChevronRight, LogOut, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNotificationStore, useAuthStore } from '@/stores';

function useBreadcrumbs() {
  const location = useLocation();
  return useMemo(() => {
    const parts = location.pathname.split('/').filter(Boolean);
    // skip the 'user' prefix in breadcrumb display
    const displayParts = parts.filter((p) => p !== 'user');
    return displayParts.map((part, i) => ({
      label: part.charAt(0).toUpperCase() + part.slice(1).replace(/-/g, ' '),
      path: '/user/' + displayParts.slice(0, i + 1).join('/'),
      isLast: i === displayParts.length - 1,
    }));
  }, [location.pathname]);
}

export function UserTopBar() {
  const { unreadCount } = useNotificationStore();
  const { user, logout } = useAuthStore();
  const breadcrumbs = useBreadcrumbs();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isAdmin = user?.role === 'admin' || user?.role === 'manager';

  return (
    <header className="h-16 border-b border-steel-slate/20 bg-deep-navy/80 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-30">
      {/* Left: Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm">
        <Link to="/user" className="text-muted-silver hover:text-ghost-white transition-colors">
          Home
        </Link>
        {breadcrumbs.map((crumb) => (
          <span key={crumb.path} className="flex items-center gap-1.5">
            <ChevronRight size={14} className="text-steel-slate" />
            {crumb.isLast ? (
              <span className="text-ghost-white font-medium">{crumb.label}</span>
            ) : (
              <Link to={crumb.path} className="text-muted-silver hover:text-ghost-white transition-colors">
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Search */}
        <button
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
            'glass-input text-muted-silver hover:text-ghost-white hover:border-electric-cyan/30',
            'transition-all duration-200',
          )}
        >
          <Search size={16} />
          <span className="hidden md:inline">Search products...</span>
        </button>

        {/* Switch to Admin (if permitted) */}
        {isAdmin && (
          <Link
            to="/"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-violet-pulse/15 text-violet-pulse hover:bg-violet-pulse/25 transition-colors"
          >
            <Shield size={14} />
            <span className="hidden lg:inline">Admin</span>
          </Link>
        )}

        {/* Notifications */}
        <button
          onClick={() => navigate('/user/notifications')}
          title="Notifications"
          className="relative p-2 rounded-lg text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30 transition-colors"
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full bg-coral-flame text-white text-[10px] font-bold flex items-center justify-center px-1 animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* User avatar & logout */}
        <div className="flex items-center gap-2 pl-2 ml-1 border-l border-steel-slate/30">
          <button
            onClick={() => navigate('/user/profile')}
            title="Profile"
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-neon-emerald to-teal-depth flex items-center justify-center">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
              ) : (
                <User size={16} className="text-white" />
              )}
            </div>
            <div className="hidden md:block">
              <p className="text-sm text-ghost-white font-medium leading-tight">
                {user?.full_name || 'User'}
              </p>
              <p className="text-[10px] text-muted-silver leading-tight capitalize">
                {user?.role || 'viewer'}
              </p>
            </div>
          </button>

          <button
            onClick={handleLogout}
            title="Sign out"
            className="p-1.5 rounded-lg text-muted-silver hover:text-coral-flame hover:bg-coral-flame/10 transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
}
