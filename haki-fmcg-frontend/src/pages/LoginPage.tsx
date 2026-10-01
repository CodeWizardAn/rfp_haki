import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Shield, User, UserPlus } from 'lucide-react';
import { Button, Input } from '@/components/ui';
import { HakiLogo } from '@/components/common';
import { useAuthStore } from '@/stores';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const redirectTo = searchParams.get('redirect');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(username, password);
      // Route based on role or explicit redirect query param
      if (redirectTo && redirectTo.startsWith('/')) {
        navigate(redirectTo);
        return;
      }
      const user = useAuthStore.getState().user;
      if (user?.role === 'admin' || user?.role === 'manager') {
        navigate('/dashboard');
      } else {
        navigate('/user');
      }
    } catch {
      // error handled in store
    }
  };

  // Quick-fill demo credentials & instant sign-in
  const fillDemo = async (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    clearError();
    try {
      await login(u, p);
      if (redirectTo && redirectTo.startsWith('/')) {
        navigate(redirectTo);
        return;
      }
      const currentUser = useAuthStore.getState().user;
      if (currentUser?.role === 'admin' || currentUser?.role === 'manager') {
        navigate('/dashboard');
      } else {
        navigate('/user');
      }
    } catch {
      // error handled in store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center gradient-hero p-4">
      {/* Decorative blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-electric-cyan/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-pulse/5 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md glass-card-elevated p-8 relative z-10"
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <HakiLogo size="xl" asLink to="/" />
          <p className="text-body text-[#64748B] mt-3 text-center font-medium">
            AI-Powered RFP &amp; Electrical Procurement Platform
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Username"
            placeholder="Enter your username"
            value={username}
            onChange={(e) => { setUsername(e.target.value); clearError(); }}
            autoComplete="username"
          />

          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Enter your password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); clearError(); }}
            autoComplete="current-password"
            error={error || undefined}
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="hover:text-ghost-white transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            }
          />

          <Button type="submit" className="w-full" loading={isLoading} size="lg">
            Sign In
          </Button>
        </form>

        {/* Create account link */}
        <div className="mt-4 text-center">
          <span className="text-sm text-muted-silver">Don't have an account? </span>
          <Link
            to="/register"
            className="inline-flex items-center gap-1 text-sm font-medium text-electric-cyan hover:text-electric-cyan/80 transition-colors"
          >
            <UserPlus size={14} />
            Create Account
          </Link>
        </div>

        {/* Demo credentials quick-fill */}
        <div className="mt-6 pt-4 border-t border-steel-slate/20">
          <p className="text-xs text-muted-silver text-center mb-3">Quick Demo Access</p>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => fillDemo('admin', 'admin123')}
              className="flex flex-col items-center gap-2 p-3 rounded-xl bg-steel-slate/20 hover:bg-steel-slate/30 border border-steel-slate/30 hover:border-violet-pulse/40 transition-all group"
            >
              <div className="w-10 h-10 rounded-lg bg-violet-pulse/15 flex items-center justify-center group-hover:bg-violet-pulse/25 transition-colors">
                <Shield size={20} className="text-violet-pulse" />
              </div>
              <span className="text-xs font-medium text-ghost-white">Admin Portal</span>
              <span className="text-[10px] text-muted-silver">admin / admin123</span>
            </button>
            <button
              onClick={() => fillDemo('user', 'user1234')}
              className="flex flex-col items-center gap-2 p-3 rounded-xl bg-steel-slate/20 hover:bg-steel-slate/30 border border-steel-slate/30 hover:border-neon-emerald/40 transition-all group"
            >
              <div className="w-10 h-10 rounded-lg bg-neon-emerald/15 flex items-center justify-center group-hover:bg-neon-emerald/25 transition-colors">
                <User size={20} className="text-neon-emerald" />
              </div>
              <span className="text-xs font-medium text-ghost-white">User Portal</span>
              <span className="text-[10px] text-muted-silver">user / user1234</span>
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
