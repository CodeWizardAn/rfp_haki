import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings,
  User,
  Bell,
  Globe,
  Database,
  Save,
  ExternalLink,
  ChevronRight,
  Check,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { useConfig, useUpdateConfig, useResetConfig } from '@/hooks/useApi';
import { useAuthStore } from '@/stores';
import { API_BASE_URL } from '@/utils/constants';

type TabId = 'profile' | 'notifications' | 'api' | 'system';

const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'profile', label: 'Profile', icon: <User size={16} /> },
  { id: 'notifications', label: 'Notifications', icon: <Bell size={16} /> },
  { id: 'api', label: 'API & Integrations', icon: <Globe size={16} /> },
  { id: 'system', label: 'System', icon: <Database size={16} /> },
];

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: () => void }) {
  return (
    <button
      onClick={onChange}
      className={`w-10 h-5 rounded-full relative transition-colors ${enabled ? 'bg-electric-cyan' : 'bg-steel-slate/40'}`}
    >
      <motion.span
        layout
        className="block w-4 h-4 bg-white rounded-full absolute top-0.5"
        style={{ left: enabled ? 22 : 2 }}
      />
    </button>
  );
}

function SettingRow({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-4 border-b border-steel-slate/15 last:border-0">
      <div>
        <p className="text-sm font-medium text-ghost-white">{label}</p>
        {description && <p className="text-xs text-muted-silver mt-0.5">{description}</p>}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('profile');
  const [saved, setSaved] = useState(false);

  /* ── Backend hooks ── */
  const { data: apiConfig } = useConfig();
  const updateConfig = useUpdateConfig();
  const resetConfig = useResetConfig();
  const { user } = useAuthStore();

  // Profile state
  const [displayName, setDisplayName] = useState('Haki Admin');
  const [email, setEmail] = useState('admin@hakifmcg.com');
  const [role] = useState('System Administrator');

  // Sync from backend config / user profile
  useEffect(() => {
    if (user) {
      setDisplayName(user.full_name || user.username || displayName);
      setEmail(user.email || email);
    }
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  // Notifications state — backed by the real `notification_enabled` config field
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  useEffect(() => {
    if (apiConfig && typeof apiConfig === 'object') {
      const cfg = apiConfig as Record<string, unknown>;
      if (cfg.notification_enabled !== undefined) setNotificationsEnabled(!!cfg.notification_enabled);
    }
  }, [apiConfig]);

  const handleSave = () => {
    updateConfig.mutate({ key: 'notification_enabled', value: notificationsEnabled });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleResetConfig = () => {
    resetConfig.mutate();
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-electric-cyan/10">
            <Settings size={24} className="text-electric-cyan" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">System Settings</h1>
            <p className="text-body text-muted-silver">Configure preferences, security & integrations</p>
          </div>
        </div>
        <Button variant="primary" leftIcon={saved ? <Check size={14} /> : <Save size={14} />} onClick={handleSave}>
          {saved ? 'Saved!' : 'Save Changes'}
        </Button>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Tabs */}
        <div className="lg:w-56 flex-shrink-0">
          <Card variant="glass">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-electric-cyan/10 text-electric-cyan'
                      : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/15'
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                  {activeTab === tab.id && <ChevronRight size={12} className="ml-auto" />}
                </button>
              ))}
            </nav>
          </Card>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
            >
              {/* Profile Tab */}
              {activeTab === 'profile' && (
                <Card variant="glass">
                  <CardHeader><CardTitle>Profile Settings</CardTitle></CardHeader>
                  <div className="space-y-0">
                    <SettingRow label="Avatar">
                      <div className="w-10 h-10 rounded-full bg-electric-cyan/20 flex items-center justify-center text-electric-cyan font-bold text-sm">
                        HA
                      </div>
                    </SettingRow>
                    <SettingRow label="Display Name" description="Visible across the platform">
                      <input
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        className="w-48 px-3 py-1.5 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm focus:outline-none focus:border-electric-cyan/50"
                      />
                    </SettingRow>
                    <SettingRow label="Email" description="Used for notifications and login">
                      <input
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-48 px-3 py-1.5 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm focus:outline-none focus:border-electric-cyan/50"
                      />
                    </SettingRow>
                    <SettingRow label="Role">
                      <Badge variant="soft" color="cyan" size="sm">{role}</Badge>
                    </SettingRow>
                    <SettingRow label="Timezone">
                      <select className="px-3 py-1.5 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm focus:outline-none">
                        <option value="IST">IST (UTC+5:30)</option>
                        <option value="UTC">UTC</option>
                        <option value="EST">EST (UTC-5)</option>
                      </select>
                    </SettingRow>
                  </div>
                </Card>
              )}

              {/* Notifications Tab */}
              {activeTab === 'notifications' && (
                <Card variant="glass">
                  <CardHeader><CardTitle>Notification Preferences</CardTitle></CardHeader>
                  <div className="space-y-0">
                    <SettingRow label="Notifications" description="Receive in-app alerts for RFP, bid, and pipeline updates">
                      <Toggle enabled={notificationsEnabled} onChange={() => setNotificationsEnabled(!notificationsEnabled)} />
                    </SettingRow>
                  </div>
                </Card>
              )}

              {/* API & Integrations Tab */}
              {activeTab === 'api' && (
                <Card variant="glass">
                  <CardHeader><CardTitle>API & Integrations</CardTitle></CardHeader>
                  <div className="space-y-0">
                    <SettingRow label="Backend URL" description="Primary API endpoint (configured at build time)">
                      <code className="px-2 py-1 rounded bg-steel-slate/20 text-xs font-mono text-muted-silver">{API_BASE_URL}</code>
                    </SettingRow>
                    <SettingRow label="API Documentation" description="OpenAPI / Swagger docs">
                      <Button
                        variant="secondary"
                        size="xs"
                        leftIcon={<ExternalLink size={10} />}
                        onClick={() => window.open(`${API_BASE_URL}/api/v1/docs`, '_blank')}
                      >
                        Open Docs
                      </Button>
                    </SettingRow>
                  </div>
                </Card>
              )}

              {/* System Tab */}
              {activeTab === 'system' && (
                <Card variant="glass">
                  <CardHeader><CardTitle>System</CardTitle></CardHeader>
                  <div className="space-y-0">
                    <SettingRow label="Application Version">
                      <Badge variant="soft" color="cyan" size="sm">v2.0.0</Badge>
                    </SettingRow>
                    <SettingRow label="Frontend Build">
                      <code className="text-xs font-mono text-muted-silver">Vite 7.3.1 + React 19</code>
                    </SettingRow>
                    <div className="pt-4 mt-4 border-t border-steel-slate/20">
                      <p className="text-xs font-semibold text-muted-silver uppercase tracking-wide mb-3">Danger Zone</p>
                    </div>
                    <SettingRow label="Reset All Settings" description="Restore factory defaults">
                      <Button
                        variant="secondary"
                        size="xs"
                        className="!border-coral-flame/30 !text-coral-flame hover:!bg-coral-flame/10"
                        onClick={handleResetConfig}
                        loading={resetConfig.isPending}
                      >
                        {resetConfig.isSuccess ? 'Reset!' : 'Reset'}
                      </Button>
                    </SettingRow>
                  </div>
                </Card>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
