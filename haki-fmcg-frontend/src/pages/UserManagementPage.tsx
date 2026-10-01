import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  Trash2,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Eye,
  LogOut,
  Key,
  Search,
  Clock,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';

/* ─── types ─── */
type Role = 'Admin' | 'Manager' | 'Analyst' | 'Viewer';

interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  active: boolean;
  lastLogin: string;
  createdAt: string;
  avatar?: string;
  sessions: number;
}

/* ─── data ─── */
const roleConfig: Record<Role, { color: string; icon: typeof Shield; bg: string }> = {
  Admin: { color: 'text-coral-flame', icon: ShieldAlert, bg: 'bg-coral-flame/10' },
  Manager: { color: 'text-violet-pulse', icon: ShieldCheck, bg: 'bg-violet-pulse/10' },
  Analyst: { color: 'text-electric-cyan', icon: Shield, bg: 'bg-electric-cyan/10' },
  Viewer: { color: 'text-muted-silver', icon: Eye, bg: 'bg-steel-slate/15' },
};

const permissions = [
  { module: 'RFP Management', admin: true, manager: true, analyst: true, viewer: true },
  { module: 'Bid Creation', admin: true, manager: true, analyst: true, viewer: false },
  { module: 'Bid Approval', admin: true, manager: true, analyst: false, viewer: false },
  { module: 'Vendor Management', admin: true, manager: true, analyst: true, viewer: true },
  { module: 'Pipeline Config', admin: true, manager: true, analyst: false, viewer: false },
  { module: 'Agent Settings', admin: true, manager: false, analyst: false, viewer: false },
  { module: 'User Management', admin: true, manager: false, analyst: false, viewer: false },
  { module: 'Webhook Config', admin: true, manager: false, analyst: false, viewer: false },
  { module: 'Analytics Export', admin: true, manager: true, analyst: true, viewer: false },
  { module: 'Compliance Audit', admin: true, manager: true, analyst: true, viewer: true },
];

const initialUsers: User[] = [
  { id: 'usr-001', name: 'Rajesh Kumar', email: 'rajesh.kumar@haki.com', role: 'Admin', active: true, lastLogin: '5 min ago', createdAt: '2023-06-15', sessions: 2 },
  { id: 'usr-002', name: 'Priya Sharma', email: 'priya.sharma@haki.com', role: 'Manager', active: true, lastLogin: '1 hr ago', createdAt: '2023-08-22', sessions: 1 },
  { id: 'usr-003', name: 'Amit Patel', email: 'amit.patel@haki.com', role: 'Analyst', active: true, lastLogin: '30 min ago', createdAt: '2023-09-10', sessions: 1 },
  { id: 'usr-004', name: 'Neha Gupta', email: 'neha.gupta@haki.com', role: 'Analyst', active: true, lastLogin: '2 hr ago', createdAt: '2023-11-05', sessions: 0 },
  { id: 'usr-005', name: 'Vikram Singh', email: 'vikram.singh@haki.com', role: 'Viewer', active: false, lastLogin: '3 days ago', createdAt: '2024-01-12', sessions: 0 },
  { id: 'usr-006', name: 'Ananya Desai', email: 'ananya.desai@haki.com', role: 'Manager', active: true, lastLogin: '4 hr ago', createdAt: '2024-02-20', sessions: 1 },
];

export default function UserManagementPage() {
  const [users, setUsers] = useState(initialUsers);
  const [search, setSearch] = useState('');
  const [filterRole, setFilterRole] = useState<Role | 'All'>('All');
  const [showCreate, setShowCreate] = useState(false);
  const [showPermissions, setShowPermissions] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  /* form */
  const [formName, setFormName] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formRole, setFormRole] = useState<Role>('Analyst');

  const filteredUsers = users.filter((u) => {
    const matchesSearch = u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase());
    const matchesRole = filterRole === 'All' || u.role === filterRole;
    return matchesSearch && matchesRole;
  });

  const toggleActive = (id: string) => {
    setUsers((p) => p.map((u) => (u.id === id ? { ...u, active: !u.active } : u)));
  };

  const deleteUser = (id: string) => {
    setUsers((p) => p.filter((u) => u.id !== id));
  };

  const forceLogout = (id: string) => {
    setUsers((p) => p.map((u) => (u.id === id ? { ...u, sessions: 0 } : u)));
  };

  const handleCreate = () => {
    if (!formName || !formEmail) return;
    const newUser: User = {
      id: `usr-${Date.now()}`, name: formName, email: formEmail, role: formRole,
      active: true, lastLogin: '—', createdAt: new Date().toISOString().split('T')[0] ?? '', sessions: 0,
    };
    setUsers((p) => [...p, newUser]);
    setFormName(''); setFormEmail(''); setFormRole('Analyst'); setShowCreate(false);
  };

  const roleCounts = { Admin: 0, Manager: 0, Analyst: 0, Viewer: 0 };
  users.forEach((u) => { roleCounts[u.role]++; });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/settings" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">User Management</h1>
            <p className="text-body text-muted-silver">Manage users, roles & permissions</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" leftIcon={<Shield size={14} />} onClick={() => setShowPermissions(!showPermissions)}>
            Permissions Matrix
          </Button>
          <Button leftIcon={<Plus size={14} />} onClick={() => setShowCreate(true)}>Add User</Button>
        </div>
      </div>

      {/* Role Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(Object.keys(roleConfig) as Role[]).map((role, i) => {
          const cfg = roleConfig[role];
          const Icon = cfg.icon;
          return (
            <motion.div key={role} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} className="glass-card rounded-xl p-3 flex items-center gap-3 cursor-pointer hover:border-electric-cyan/20 transition-colors" onClick={() => setFilterRole(filterRole === role ? 'All' : role)}>
              <div className={`w-9 h-9 rounded-lg ${cfg.bg} flex items-center justify-center flex-shrink-0`}>
                <Icon size={16} className={cfg.color} />
              </div>
              <div>
                <p className="text-lg font-bold text-ghost-white leading-none">{roleCounts[role]}</p>
                <span className="text-[10px] text-muted-silver">{role}s</span>
              </div>
              {filterRole === role && <div className="w-1.5 h-1.5 rounded-full bg-electric-cyan ml-auto" />}
            </motion.div>
          );
        })}
      </div>

      {/* Permissions Matrix */}
      <AnimatePresence>
        {showPermissions && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <Card variant="glass">
              <CardHeader><CardTitle className="text-sm">Role Permissions Matrix</CardTitle></CardHeader>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-steel-slate/15 text-muted-silver">
                      <th className="text-left p-2 pl-4">Module</th>
                      <th className="text-center p-2">Admin</th>
                      <th className="text-center p-2">Manager</th>
                      <th className="text-center p-2">Analyst</th>
                      <th className="text-center p-2 pr-4">Viewer</th>
                    </tr>
                  </thead>
                  <tbody>
                    {permissions.map((p) => (
                      <tr key={p.module} className="border-b border-steel-slate/8">
                        <td className="p-2 pl-4 text-ghost-white">{p.module}</td>
                        {[p.admin, p.manager, p.analyst, p.viewer].map((v, i) => (
                          <td key={i} className="text-center p-2">
                            {v ? <CheckCircle2 size={13} className="text-neon-emerald mx-auto" /> : <XCircle size={13} className="text-steel-slate/40 mx-auto" />}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <Card variant="glass" className="p-4 space-y-4">
              <h3 className="text-sm font-semibold text-ghost-white">New User</h3>
              <div className="grid md:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-muted-silver block mb-1">Full Name</label>
                  <input value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="John Doe" className="glass-input w-full rounded-lg px-3 py-2 text-sm text-ghost-white" />
                </div>
                <div>
                  <label className="text-xs text-muted-silver block mb-1">Email</label>
                  <input value={formEmail} onChange={(e) => setFormEmail(e.target.value)} placeholder="john@haki.com" className="glass-input w-full rounded-lg px-3 py-2 text-sm text-ghost-white" />
                </div>
                <div>
                  <label className="text-xs text-muted-silver block mb-1">Role</label>
                  <select value={formRole} onChange={(e) => setFormRole(e.target.value as Role)} className="glass-input w-full rounded-lg px-3 py-2 text-sm text-ghost-white bg-transparent">
                    <option value="Admin">Admin</option>
                    <option value="Manager">Manager</option>
                    <option value="Analyst">Analyst</option>
                    <option value="Viewer">Viewer</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleCreate}>Create User</Button>
                <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search & Filter */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search users…" className="glass-input w-full rounded-lg pl-9 pr-3 py-2 text-sm text-ghost-white" />
        </div>
        {filterRole !== 'All' && (
          <Button variant="secondary" size="sm" onClick={() => setFilterRole('All')}>
            Clear Filter
          </Button>
        )}
      </div>

      {/* Users List */}
      <div className="space-y-2">
        {filteredUsers.map((user) => {
          const cfg = roleConfig[user.role];
          const Icon = cfg.icon;
          const isExpanded = expanded === user.id;

          return (
            <Card key={user.id} variant="glass" className="overflow-hidden">
              <div className="p-3 flex items-center gap-3">
                {/* Avatar */}
                <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${cfg.bg} text-sm font-bold ${cfg.color}`}>
                  {user.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-ghost-white">{user.name}</span>
                    <Badge variant={user.active ? 'success' : 'default'} size="sm">{user.active ? 'Active' : 'Inactive'}</Badge>
                    {user.sessions > 0 && <span className="w-1.5 h-1.5 rounded-full bg-neon-emerald animate-pulse" title="Online" />}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-muted-silver">
                    <span>{user.email}</span>
                    <span className="flex items-center gap-0.5"><Icon size={9} className={cfg.color} /> {user.role}</span>
                    <span className="flex items-center gap-0.5"><Clock size={9} /> {user.lastLogin}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                  {user.sessions > 0 && (
                    <button onClick={() => forceLogout(user.id)} className="p-1.5 rounded-lg hover:bg-amber-glow/10 transition-colors" title="Force logout">
                      <LogOut size={13} className="text-amber-glow" />
                    </button>
                  )}
                  <button className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors" title="Reset password">
                    <Key size={13} className="text-muted-silver" />
                  </button>
                  <button onClick={() => toggleActive(user.id)} className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors" title="Toggle active">
                    {user.active ? <CheckCircle2 size={13} className="text-neon-emerald" /> : <XCircle size={13} className="text-muted-silver" />}
                  </button>
                  <button onClick={() => deleteUser(user.id)} className="p-1.5 rounded-lg hover:bg-coral-flame/10 transition-colors" title="Delete user">
                    <Trash2 size={13} className="text-coral-flame" />
                  </button>
                  <button onClick={() => setExpanded(isExpanded ? null : user.id)} className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors">
                    {isExpanded ? <ChevronUp size={13} className="text-muted-silver" /> : <ChevronDown size={13} className="text-muted-silver" />}
                  </button>
                </div>
              </div>

              {/* Expanded */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-steel-slate/10">
                    <div className="p-4 grid md:grid-cols-3 gap-4 text-xs">
                      <div>
                        <span className="text-muted-silver block mb-1">User ID</span>
                        <span className="text-ghost-white font-mono">{user.id}</span>
                      </div>
                      <div>
                        <span className="text-muted-silver block mb-1">Created</span>
                        <span className="text-ghost-white">{user.createdAt}</span>
                      </div>
                      <div>
                        <span className="text-muted-silver block mb-1">Active Sessions</span>
                        <span className="text-ghost-white">{user.sessions}</span>
                      </div>
                      <div className="md:col-span-3">
                        <span className="text-muted-silver block mb-1">Role Permissions</span>
                        <div className="flex flex-wrap gap-1.5">
                          {permissions.filter((p) => p[user.role.toLowerCase() as keyof typeof p]).map((p) => (
                            <Badge key={p.module} variant="soft" color="cyan" size="sm">{p.module}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
