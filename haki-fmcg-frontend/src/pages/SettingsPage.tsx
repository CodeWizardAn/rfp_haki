import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings,
  User,
  Palette,
  Bell,
  Shield,
  Globe,
  Database,
  Key,
  Save,
  Sun,
  Moon,
  Monitor,
  Mail,
  Smartphone,
  Volume2,
  Eye,
  EyeOff,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Check,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';
import { useConfig, useUpdateConfig } from '@/hooks/useApi';
import { useAuthStore } from '@/stores';

type TabId = 'profile' | 'appearance' | 'notifications' | 'security' | 'api' | 'system';

const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'profile', label: 'Profile', icon: <User size={16} /> },
  { id: 'appearance', label: 'Appearance', icon: <Palette size={16} /> },
  { id: 'notifications', label: 'Notifications', icon: <Bell size={16} /> },
  { id: 'security', label: 'Security', icon: <Shield size={16} /> },
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

  useEffect(() => {
    if (apiConfig && typeof apiConfig === 'object') {
      const cfg = apiConfig as Record<string, unknown>;
      if (cfg.backend_url) setBackendUrl(cfg.backend_url as string);
      if (cfg.sse_enabled !== undefined) setSseEnabled(!!cfg.sse_enabled);
    }
  }, [apiConfig]);

  // Appearance state
  const [theme, setTheme] = useState<'dark' | 'light' | 'system'>('dark');
  const [sidebarCompact, setSidebarCompact] = useState(false);
  const [animationsEnabled, setAnimationsEnabled] = useState(true);
  const [glowEffects, setGlowEffects] = useState(true);

  // Notifications state
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [pushNotifs, setPushNotifs] = useState(true);
  const [soundNotifs, setSoundNotifs] = useState(false);
  const [rfpAlerts, setRfpAlerts] = useState(true);
  const [bidAlerts, setBidAlerts] = useState(true);
  const [pipelineAlerts, setPipelineAlerts] = useState(true);

  // Security state
  const [showApiKey, setShowApiKey] = useState(false);
  const [twoFA, setTwoFA] = useState(false);
  const [sessionTimeout, setSessionTimeout] = useState('30');

  // API state
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000');
  const [sseEnabled, setSseEnabled] = useState(true);
  const [autoRetry, setAutoRetry] = useState(true);

  const handleSave = () => {
    // Push settings to backend
    updateConfig.mutate({ key: 'backend_url', value: backendUrl });
    updateConfig.mutate({ key: 'sse_enabled', value: sseEnabled });
    updateConfig.mutate({ key: 'auto_retry', value: autoRetry });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const themeIcons = { dark: <Moon size={14} />, light: <Sun size={14} />, system: <Monitor size={14} /> };

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
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-electric-cyan/20 flex items-center justify-center text-electric-cyan font-bold text-sm">
                          HA
                        </div>
                        <Button variant="secondary" size="xs">Change</Button>
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

              {/* Appearance Tab */}
              {activeTab === 'appearance' && (
                <Card variant="glass">
                  <CardHeader><CardTitle>Appearance</CardTitle></CardHeader>
                  <div className="space-y-0">
                    <SettingRow label="Theme" description="Choose your preferred color scheme">
                      <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
                        {(['dark', 'light', 'system'] as const).map((t) => (
                          <button
                            key={t}
                            onClick={() => setTheme(t)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                              theme === t ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'
                            }`}
                          >
                            {themeIcons[t]}
                            {t.charAt(0).toUpperCase() + t.slice(1)}
                          </button>
                        ))}
                      </div>
                    </SettingRow>
                    <SettingRow label="Compact Sidebar" description="Collapse sidebar by default">
                      <Toggle enabled={sidebarCompact} onChange={() => setSidebarCompact(!sidebarCompact)} />
                    </SettingRow>
                    <SettingRow label="Animations" description="Enable motion and transitions">
                      <Toggle enabled={animationsEnabled} onChange={() => setAnimationsEnabled(!animationsEnabled)} />
                    </SettingRow>
                    <SettingRow label="Glow Effects" description="Neon glow borders and highlights">
                      <Toggle enabled={glowEffects} onChange={() => setGlowEffects(!glowEffects)} />
                    </SettingRow>
                  </div>
                </Card>
              )}

              {/* Notifications Tab */}
              {activeTab === 'notifications' && (
                <Card variant="glass">
                  <CardHeader><CardTitle>Notification Preferences</CardTitle></CardHeader>
                  <div className="space-y-0">
                    <SettingRow label="Email Notifications" description="Receive updates via email">
                      <div className="flex items-center gap-2">
                        <Mail size={14} className="text-muted-silver" />
                        <Toggle enabled={emailNotifs} onChange={() => setEmailNotifs(!emailNotifs)} />
                      </div>
                    </SettingRow>
                    <SettingRow label="Push Notifications" description="Browser push notifications">
                      <div className="flex items-center gap-2">
                        <Smartphone size={14} className="text-muted-silver" />
                        <Toggle enabled={pushNotifs} onChange={() => setPushNotifs(!pushNotifs)} />
                      </div>
                    </SettingRow>
                    <SettingRow label="Sound Alerts" description="Audible alert sounds">
                      <div className="flex items-center gap-2">
                        <Volume2 size={14} className="text-muted-silver" />
                        <Toggle enabled={soundNotifs} onChange={() => setSoundNotifs(!soundNotifs)} />
                      </div>
                    </SettingRow>
                    <div className="pt-4 mt-4 border-t border-steel-slate/20">
                      <p className="text-xs font-semibold text-muted-silver uppercase tracking-wide mb-3">Alert Types</p>
                    </div>
                    <SettingRow label="RFP Alerts" description="New RFPs, status changes, deadlines">
                      <Toggle enabled={rfpAlerts} onChange={() => setRfpAlerts(!rfpAlerts)} />
                    </SettingRow>
                    <SettingRow label="Bid Alerts" description="Bid updates, approvals, expirations">
                      <Toggle enabled={bidAlerts} onChange={() => setBidAlerts(!bidAlerts)} />
                    </SettingRow>
                    <SettingRow label="Pipeline Alerts" description="Pipeline completions, errors">
                      <Toggle enabled={pipelineAlerts} onChange={() => setPipelineAlerts(!pipelineAlerts)} />
                    </SettingRow>
                  </div>
                </Card>
              )}

              {/* Security Tab */}
              {activeTab === 'security' && (
                <Card variant="glass">
                  <CardHeader><CardTitle>Security</CardTitle></CardHeader>
                  <div className="space-y-0">
                    <SettingRow label="Password" description="Last changed 14 days ago">
                      <Button variant="secondary" size="xs">Change Password</Button>
                    </SettingRow>
                    <SettingRow label="Two-Factor Authentication" description="Add an extra layer of security">
                      <Toggle enabled={twoFA} onChange={() => setTwoFA(!twoFA)} />
                    </SettingRow>
                    <SettingRow label="Session Timeout" description="Auto-logout after inactivity (minutes)">
                      <select
                        value={sessionTimeout}
                        onChange={(e) => setSessionTimeout(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm focus:outline-none"
                      >
                        <option value="15">15 min</option>
                        <option value="30">30 min</option>
                        <option value="60">1 hour</option>
                        <option value="120">2 hours</option>
                      </select>
                    </SettingRow>
                    <SettingRow label="API Key" description="Used for external integrations">
                      <div className="flex items-center gap-2">
                        <code className="px-2 py-1 rounded bg-steel-slate/20 text-xs font-mono text-muted-silver">
                          {showApiKey ? 'hk_live_a3f8c2e1d9b7' : '••••••••••••••'}
                        </code>
                        <button onClick={() => setShowApiKey(!showApiKey)} className="text-muted-silver hover:text-ghost-white">
                          {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                      </div>
                    </SettingRow>
                    <SettingRow label="Active Sessions">
                      <div className="flex items-center gap-2">
                        <Badge variant="soft" color="emerald" size="sm">2 active</Badge>
                        <Button variant="secondary" size="xs">Manage</Button>
                      </div>
                    </SettingRow>
                  </div>
                </Card>
              )}

              {/* API & Integrations Tab */}
              {activeTab === 'api' && (
                <Card variant="glass">
                  <CardHeader><CardTitle>API & Integrations</CardTitle></CardHeader>
                  <div className="space-y-0">
                    <SettingRow label="Backend URL" description="Primary API endpoint">
                      <div className="flex items-center gap-2">
                        <input
                          value={backendUrl}
                          onChange={(e) => setBackendUrl(e.target.value)}
                          className="w-56 px-3 py-1.5 rounded-lg bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm font-mono focus:outline-none focus:border-electric-cyan/50"
                        />
                        <Badge variant="dot" color="emerald" size="sm">Connected</Badge>
                      </div>
                    </SettingRow>
                    <SettingRow label="Server-Sent Events" description="Real-time updates via SSE">
                      <Toggle enabled={sseEnabled} onChange={() => setSseEnabled(!sseEnabled)} />
                    </SettingRow>
                    <SettingRow label="Auto Retry" description="Retry failed requests automatically">
                      <Toggle enabled={autoRetry} onChange={() => setAutoRetry(!autoRetry)} />
                    </SettingRow>
                    <SettingRow label="API Documentation" description="OpenAPI / Swagger docs">
                      <Button variant="secondary" size="xs" leftIcon={<ExternalLink size={10} />}>Open Docs</Button>
                    </SettingRow>
                    <div className="pt-4 mt-4 border-t border-steel-slate/20">
                      <p className="text-xs font-semibold text-muted-silver uppercase tracking-wide mb-3">Connected Services</p>
                    </div>
                    {[
                      { name: 'ChromaDB', status: 'connected', desc: 'Vector database for semantic search' },
                      { name: 'PostgreSQL', status: 'connected', desc: 'Primary relational database' },
                      { name: 'PDF Extraction', status: 'connected', desc: 'Document parsing service' },
                    ].map((svc) => (
                      <SettingRow key={svc.name} label={svc.name} description={svc.desc}>
                        <Badge variant="dot" color="emerald" size="sm">{svc.status}</Badge>
                      </SettingRow>
                    ))}
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
                    <SettingRow label="Cache" description="Clear cached data and refresh">
                      <Button variant="secondary" size="xs" leftIcon={<RefreshCw size={10} />}>Clear Cache</Button>
                    </SettingRow>
                    <SettingRow label="Database" description="Database maintenance utilities">
                      <div className="flex gap-2">
                        <Button variant="secondary" size="xs">Migrate</Button>
                        <Button variant="secondary" size="xs">Backup</Button>
                      </div>
                    </SettingRow>
                    <SettingRow label="Logs" description="System and error logs">
                      <Button variant="secondary" size="xs" leftIcon={<ExternalLink size={10} />}>View Logs</Button>
                    </SettingRow>
                    <div className="pt-4 mt-4 border-t border-steel-slate/20">
                      <p className="text-xs font-semibold text-muted-silver uppercase tracking-wide mb-3">Danger Zone</p>
                    </div>
                    <SettingRow label="Reset All Settings" description="Restore factory defaults">
                      <Button variant="secondary" size="xs" className="!border-coral-flame/30 !text-coral-flame hover:!bg-coral-flame/10">Reset</Button>
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
