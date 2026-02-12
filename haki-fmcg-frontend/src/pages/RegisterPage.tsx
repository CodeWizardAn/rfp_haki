import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Zap, UserPlus, ArrowLeft } from 'lucide-react';
import { Button, Input } from '@/components/ui';
import { authService, type RegisterPayload } from '@/services/auth.service';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterPayload & { confirmPassword: string }>({
    username: '',
    password: '',
    confirmPassword: '',
    email: '',
    full_name: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((p) => ({ ...p, [field]: e.target.value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);
    try {
      await authService.register({
        username: form.username,
        password: form.password,
        email: form.email,
        full_name: form.full_name,
      });
      setSuccess(true);
      // Redirect to login after 2s
      setTimeout(() => navigate('/login'), 2000);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Registration failed';
      setError(msg);
    } finally {
      setIsLoading(false);
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
        <div className="flex flex-col items-center mb-6">
          <div className="w-14 h-14 rounded-2xl gradient-pipeline flex items-center justify-center mb-4">
            <Zap size={28} className="text-white" />
          </div>
          <h1 className="text-h2 text-ghost-white">Create Account</h1>
          <p className="text-body text-muted-silver mt-1">Join HAKI FMCG Platform</p>
        </div>

        {success ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center space-y-4"
          >
            <div className="w-16 h-16 mx-auto rounded-full bg-neon-emerald/20 flex items-center justify-center">
              <UserPlus size={32} className="text-neon-emerald" />
            </div>
            <p className="text-lg text-ghost-white font-medium">Account Created!</p>
            <p className="text-sm text-muted-silver">
              Redirecting you to login…
            </p>
          </motion.div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3.5">
            <Input
              label="Full Name"
              placeholder="John Doe"
              value={form.full_name}
              onChange={set('full_name')}
              autoComplete="name"
            />

            <Input
              label="Username"
              placeholder="Choose a username"
              value={form.username}
              onChange={set('username')}
              autoComplete="username"
            />

            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={set('email')}
              autoComplete="email"
            />

            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Min 8 characters"
              value={form.password}
              onChange={set('password')}
              autoComplete="new-password"
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

            <Input
              label="Confirm Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Repeat your password"
              value={form.confirmPassword}
              onChange={set('confirmPassword')}
              autoComplete="new-password"
              error={error || undefined}
            />

            <Button type="submit" className="w-full" loading={isLoading} size="lg">
              <UserPlus size={18} className="mr-2" />
              Create Account
            </Button>
          </form>
        )}

        {/* Back to login */}
        <div className="mt-6 pt-4 border-t border-steel-slate/20 text-center">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-sm text-electric-cyan hover:text-electric-cyan/80 transition-colors"
          >
            <ArrowLeft size={14} />
            Back to Sign In
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
