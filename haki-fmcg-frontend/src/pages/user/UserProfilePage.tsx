import { useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import {
  User,
  Mail,
  Phone,
  Building2,
  MapPin,
  Shield,
  Key,
  Bell,
  Eye,
  EyeOff,
  Save,
  Camera,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Button, Input } from '@/components/ui';
import { useAuthStore } from '@/stores';

export default function UserProfilePage() {
  const { user } = useAuthStore();
  const [activeSection, setActiveSection] = useState<'profile' | 'security' | 'preferences'>('profile');

  // Profile form state
  const [fullName, setFullName] = useState(user?.full_name || 'User');
  const [email, setEmail] = useState(user?.email || 'user@haki.com');
  const [phone, setPhone] = useState('+91 98765 43210');
  const [department, setDepartment] = useState('Procurement');
  const [location, setLocation] = useState('Mumbai, India');
  const [bio, setBio] = useState('Procurement specialist focused on FMCG and electrical products.');

  // Security
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);
  const [revokedSession, setRevokedSession] = useState(false);

  // Preferences
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [pushNotifs, setPushNotifs] = useState(true);
  const [quoteAlerts, setQuoteAlerts] = useState(true);
  const [deadlineReminders, setDeadlineReminders] = useState(true);
  const [priceAlerts, setPriceAlerts] = useState(false);
  const [weeklyDigest, setWeeklyDigest] = useState(true);

  const handleSaveProfile = () => {
    toast.success('Profile details saved successfully!');
  };

  const handleUpdatePassword = () => {
    if (!currentPassword) {
      toast.error('Please enter your current password.');
      return;
    }
    if (!newPassword || newPassword.length < 6) {
      toast.error('New password must be at least 6 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match.');
      return;
    }
    toast.success('Password updated successfully!');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  const handleRevokeSession = () => {
    setRevokedSession(true);
    toast.success('macOS Safari session revoked successfully.');
  };

  const handleSavePreferences = () => {
    toast.success('Notification preferences updated successfully!');
  };

  const sections = [
    { id: 'profile' as const, label: 'Profile', icon: <User size={16} /> },
    { id: 'security' as const, label: 'Security', icon: <Shield size={16} /> },
    { id: 'preferences' as const, label: 'Preferences', icon: <Bell size={16} /> },
  ];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ghost-white">My Profile</h1>
        <p className="text-body text-muted-silver mt-1">Manage your account settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            {/* Avatar */}
            <div className="flex flex-col items-center mb-6">
              <div className="relative mb-3">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-neon-emerald to-teal-depth flex items-center justify-center">
                  {user?.avatar_url ? (
                    <img src={user.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
                  ) : (
                    <User size={32} className="text-white" />
                  )}
                </div>
                <button className="absolute bottom-0 right-0 w-7 h-7 rounded-full bg-electric-cyan flex items-center justify-center hover:bg-electric-cyan/80 transition-colors">
                  <Camera size={14} className="text-deep-navy" />
                </button>
              </div>
              <h3 className="text-sm font-semibold text-ghost-white">{fullName}</h3>
              <p className="text-xs text-muted-silver capitalize">{user?.role || 'viewer'}</p>
            </div>

            {/* Nav */}
            <nav className="space-y-1">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === section.id
                      ? 'bg-electric-cyan/10 text-electric-cyan'
                      : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30'
                  }`}
                >
                  {section.icon}
                  {section.label}
                </button>
              ))}
            </nav>
          </Card>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          {activeSection === 'profile' && (
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
              </CardHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Full Name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    leftIcon={<User size={14} />}
                  />
                  <Input
                    label="Email Address"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    leftIcon={<Mail size={14} />}
                  />
                  <Input
                    label="Phone Number"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    leftIcon={<Phone size={14} />}
                  />
                  <Input
                    label="Department"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    leftIcon={<Building2 size={14} />}
                  />
                  <Input
                    label="Location"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    leftIcon={<MapPin size={14} />}
                  />
                  <Input
                    label="Username"
                    value={user?.username || 'user'}
                    disabled
                    hint="Username cannot be changed"
                  />
                </div>
                <div>
                  <label className="block text-caption text-muted-silver mb-1.5">Bio</label>
                  <textarea
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    rows={3}
                    className="w-full glass-input px-3 py-2.5 text-body text-ghost-white placeholder:text-muted-silver/50 resize-y min-h-[80px] rounded-[10px] focus:outline-none focus:border-electric-cyan/40"
                  />
                </div>
                <div className="flex justify-end">
                  <Button variant="primary" leftIcon={<Save size={16} />} onClick={handleSaveProfile}>
                    Save Changes
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {activeSection === 'security' && (
            <Card>
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
              </CardHeader>
              <div className="space-y-4 max-w-md">
                <Input
                  label="Current Password"
                  type={showPasswords ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  leftIcon={<Key size={14} />}
                  rightIcon={
                    <button onClick={() => setShowPasswords(!showPasswords)} className="hover:text-ghost-white">
                      {showPasswords ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  }
                />
                <Input
                  label="New Password"
                  type={showPasswords ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  leftIcon={<Key size={14} />}
                />
                <Input
                  label="Confirm New Password"
                  type={showPasswords ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  leftIcon={<Key size={14} />}
                  error={confirmPassword && newPassword !== confirmPassword ? 'Passwords do not match' : undefined}
                />
                <div className="flex justify-end pt-2">
                  <Button variant="primary" leftIcon={<Shield size={16} />} onClick={handleUpdatePassword}>
                    Update Password
                  </Button>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-steel-slate/20">
                <h3 className="text-sm font-semibold text-ghost-white mb-3">Active Sessions</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-steel-slate/10">
                    <div>
                      <p className="text-sm text-ghost-white">Windows — Chrome</p>
                      <p className="text-[10px] text-muted-silver">Mumbai, India · Current session</p>
                    </div>
                    <span className="text-[10px] text-neon-emerald">Active now</span>
                  </div>
                  {!revokedSession ? (
                    <div className="flex items-center justify-between p-3 rounded-lg bg-steel-slate/10">
                      <div>
                        <p className="text-sm text-ghost-white">macOS — Safari</p>
                        <p className="text-[10px] text-muted-silver">Mumbai, India · 2 days ago</p>
                      </div>
                      <Button variant="ghost" size="xs" onClick={handleRevokeSession}>Revoke</Button>
                    </div>
                  ) : (
                    <div className="p-2.5 rounded-lg bg-coral-flame/10 border border-coral-flame/20 text-xs text-coral-flame flex items-center justify-between">
                      <span>macOS Safari session revoked</span>
                      <span className="text-[10px] text-muted-silver">Disconnected</span>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          )}

          {activeSection === 'preferences' && (
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
              </CardHeader>
              <div className="space-y-4">
                {[
                  { label: 'Email Notifications', desc: 'Receive updates via email', value: emailNotifs, setter: setEmailNotifs },
                  { label: 'Push Notifications', desc: 'Browser push notifications', value: pushNotifs, setter: setPushNotifs },
                  { label: 'Quote Alerts', desc: 'Notify when vendors respond to quotes', value: quoteAlerts, setter: setQuoteAlerts },
                  { label: 'Deadline Reminders', desc: 'Remind 3 days before deadlines', value: deadlineReminders, setter: setDeadlineReminders },
                  { label: 'Price Drop Alerts', desc: 'Notify when wishlist product prices drop', value: priceAlerts, setter: setPriceAlerts },
                  { label: 'Weekly Digest', desc: 'Summary of procurement activity', value: weeklyDigest, setter: setWeeklyDigest },
                ].map((pref) => (
                  <div key={pref.label} className="flex items-center justify-between py-2">
                    <div>
                      <p className="text-sm text-ghost-white font-medium">{pref.label}</p>
                      <p className="text-xs text-muted-silver">{pref.desc}</p>
                    </div>
                    <button
                      onClick={() => pref.setter(!pref.value)}
                      className={`relative w-11 h-6 rounded-full transition-colors ${pref.value ? 'bg-neon-emerald' : 'bg-steel-slate'}`}
                    >
                      <span
                        className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${pref.value ? 'translate-x-6' : 'translate-x-1'}`}
                      />
                    </button>
                  </div>
                ))}
                <div className="flex justify-end pt-4 border-t border-steel-slate/20">
                  <Button variant="primary" leftIcon={<Save size={16} />} onClick={handleSavePreferences}>
                    Save Preferences
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </motion.div>
  );
}
