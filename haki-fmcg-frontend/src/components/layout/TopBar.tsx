import { useMemo } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Bell, Search, User, ChevronRight, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore, useNotificationStore, useAuthStore } from '@/stores';
import { Badge } from '@/components/ui';
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

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 border-b border-steel-slate/20 bg-deep-navy/80 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-30">
      {/* Left: Back button & Breadcrumb */}
      <div className="flex items-center gap-3">
        <BackButton fallbackUrl="/" />
        <nav className="flex items-center gap-1.5 text-sm">
          <Link to="/" className="text-muted-silver hover:text-ghost-white transition-colors">
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
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Search trigger */}
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
            'glass-input text-muted-silver hover:text-ghost-white hover:border-electric-cyan/30',
            'transition-all duration-200',
          )}
        >
          <Search size={16} />
          <span className="hidden md:inline">Search</span>
          <kbd className="hidden md:inline text-[10px] px-1.5 py-0.5 rounded bg-steel-slate/50 text-muted-silver ml-2">
            ⌘K
          </kbd>
        </button>

        {/* Pipeline status indicator */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neon-emerald/10">
          <span className="w-2 h-2 rounded-full bg-neon-emerald animate-pulse" />
          <span className="text-xs text-neon-emerald font-medium">Healthy</span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30 transition-colors">
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full bg-coral-flame text-white text-[10px] font-bold flex items-center justify-center px-1 animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* User */}
        <div className="flex items-center gap-2 pl-2 ml-1 border-l border-steel-slate/30">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-electric-cyan to-violet-pulse flex items-center justify-center">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
            ) : (
              <User size={16} className="text-white" />
            )}
          </div>
          <div className="hidden md:block">
            <p className="text-sm text-ghost-white font-medium leading-tight">
              {user?.full_name || 'Admin User'}
            </p>
            <Badge variant="soft" color="violet" size="sm" className="mt-0.5">
              {user?.role || 'admin'}
            </Badge>
          </div>

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
