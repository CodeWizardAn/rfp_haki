import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2,
  Plus,
  Edit3,
  Trash2,
  Star,
  Save,
  X,
  Phone,
  Mail,
  MapPin,
  ShieldCheck,
  Users,
  Award,
  CheckCircle2,
  AlertTriangle,
  Hash,
  Landmark,
} from 'lucide-react';
import { Card, Badge, Button, Modal } from '@/components/ui';

// ── Types ──

interface CompanyProfile {
  id: string;
  company_name: string;
  trading_name: string;
  registration_number: string;
  tax_id: string;
  gst_number: string;
  pan_number: string;
  incorporation_date: string;
  company_type: string;
  industry: string;
  website: string;
  email: string;
  phone: string;
  fax: string;
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  authorized_signatory: string;
  signatory_designation: string;
  signatory_email: string;
  signatory_phone: string;
  bank_name: string;
  bank_branch: string;
  bank_account: string;
  bank_ifsc: string;
  bank_swift: string;
  annual_turnover: string;
  employee_count: number;
  iso_certifications: string[];
  bis_license: string;
  other_certifications: string[];
  experience_years: number;
  key_clients: string[];
  logo_url: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

const EMPTY_PROFILE: Omit<CompanyProfile, 'id' | 'is_default' | 'created_at' | 'updated_at'> = {
  company_name: '', trading_name: '', registration_number: '', tax_id: '', gst_number: '',
  pan_number: '', incorporation_date: '', company_type: 'Private Limited', industry: '',
  website: '', email: '', phone: '', fax: '',
  address_line1: '', address_line2: '', city: '', state: '', country: 'India', postal_code: '',
  authorized_signatory: '', signatory_designation: '', signatory_email: '', signatory_phone: '',
  bank_name: '', bank_branch: '', bank_account: '', bank_ifsc: '', bank_swift: '',
  annual_turnover: '', employee_count: 0,
  iso_certifications: [], bis_license: '', other_certifications: [],
  experience_years: 0, key_clients: [], logo_url: '',
};

const stagger = { hidden: {}, visible: { transition: { staggerChildren: 0.05 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

// ── API helpers ──

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const headers = () => {
  const token = localStorage.getItem('haki_token') || localStorage.getItem('access_token');
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
};

async function fetchProfiles(): Promise<CompanyProfile[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/company-profiles`, { headers: headers() });
    if (!res.ok) return [];
    const json = await res.json();
    return json.data ?? json ?? [];
  } catch { return []; }
}

async function saveProfile(data: any, id?: string): Promise<CompanyProfile | null> {
  try {
    const url = id
      ? `${API_BASE}/api/v1/company-profiles/${id}`
      : `${API_BASE}/api/v1/company-profiles`;
    const res = await fetch(url, {
      method: id ? 'PUT' : 'POST',
      headers: headers(),
      body: JSON.stringify(data),
    });
    if (!res.ok) return null;
    const json = await res.json();
    return json.data ?? json;
  } catch { return null; }
}

async function removeProfile(id: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/company-profiles/${id}`, {
      method: 'DELETE', headers: headers(),
    });
    return res.ok;
  } catch { return false; }
}

async function setDefault(id: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/company-profiles/${id}/default`, {
      method: 'POST', headers: headers(),
    });
    return res.ok;
  } catch { return false; }
}

// ── Component ──

export default function CompanyProfilesPage() {
  const [profiles, setProfiles] = useState<CompanyProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingProfile, setEditingProfile] = useState<Partial<CompanyProfile> | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [activeSection, setActiveSection] = useState(0);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [deleteModal, setDeleteModal] = useState<string | null>(null);

  const loadProfiles = useCallback(async () => {
    setLoading(true);
    const data = await fetchProfiles();
    setProfiles(data);
    setLoading(false);
  }, []);

  useEffect(() => { loadProfiles(); }, [loadProfiles]);

  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(t);
    }
  }, [toast]);

  const handleSave = async () => {
    if (!editingProfile) return;
    setSaving(true);
    const result = await saveProfile(editingProfile, editingProfile.id);
    setSaving(false);
    if (result) {
      setToast({ type: 'success', msg: isNew ? 'Profile created!' : 'Profile updated!' });
      setEditingProfile(null);
      loadProfiles();
    } else {
      setToast({ type: 'error', msg: 'Failed to save profile' });
    }
  };

  const handleDelete = async (id: string) => {
    const ok = await removeProfile(id);
    setDeleteModal(null);
    if (ok) {
      setToast({ type: 'success', msg: 'Profile deleted' });
      loadProfiles();
    } else {
      setToast({ type: 'error', msg: 'Failed to delete profile' });
    }
  };

  const handleSetDefault = async (id: string) => {
    const ok = await setDefault(id);
    if (ok) {
      setToast({ type: 'success', msg: 'Default profile updated' });
      loadProfiles();
    }
  };

  const updateField = (field: string, value: any) => {
    setEditingProfile((p) => p ? { ...p, [field]: value } : p);
  };

  const updateArrayField = (field: string, value: string) => {
    const arr = value.split(',').map((s) => s.trim()).filter(Boolean);
    setEditingProfile((p) => p ? { ...p, [field]: arr } : p);
  };

  const sections = [
    { label: 'Company Info', icon: <Building2 size={14} /> },
    { label: 'Contact', icon: <Phone size={14} /> },
    { label: 'Signatory', icon: <Users size={14} /> },
    { label: 'Bank Details', icon: <Landmark size={14} /> },
    { label: 'Certifications', icon: <ShieldCheck size={14} /> },
    { label: 'Experience', icon: <Award size={14} /> },
  ];

  // ── Render ──

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl border flex items-center gap-2 shadow-xl ${
              toast.type === 'success' ? 'bg-neon-emerald/15 border-neon-emerald/30' : 'bg-coral-flame/15 border-coral-flame/30'
            }`}
          >
            {toast.type === 'success' ? <CheckCircle2 size={16} className="text-neon-emerald" /> : <AlertTriangle size={16} className="text-coral-flame" />}
            <span className="text-sm text-ghost-white">{toast.msg}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <motion.div variants={fadeUp} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-h2 text-ghost-white">Company Profiles</h1>
          <p className="text-body text-muted-silver mt-1">
            Manage company information used to prefill bids &amp; tender documents
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<Plus size={16} />}
          onClick={() => { setEditingProfile({ ...EMPTY_PROFILE } as any); setIsNew(true); setActiveSection(0); }}
        >
          New Profile
        </Button>
      </motion.div>

      {/* Profile Cards */}
      {!editingProfile && (
        <motion.div variants={fadeUp} className="space-y-4">
          {loading ? (
            <div className="text-center py-16">
              <div className="w-8 h-8 border-2 border-electric-cyan border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm text-muted-silver">Loading profiles...</p>
            </div>
          ) : profiles.length === 0 ? (
            <Card variant="glass" className="p-12 text-center">
              <Building2 size={48} className="mx-auto text-steel-slate/40 mb-4" />
              <p className="text-ghost-white font-medium mb-2">No profiles yet</p>
              <p className="text-sm text-muted-silver mb-4">Create a company profile to start generating bids</p>
              <Button
                variant="primary"
                leftIcon={<Plus size={16} />}
                onClick={() => { setEditingProfile({ ...EMPTY_PROFILE } as any); setIsNew(true); setActiveSection(0); }}
              >
                Create First Profile
              </Button>
            </Card>
          ) : (
            profiles.map((profile) => (
              <Card key={profile.id} variant="glass" className="overflow-hidden">
                <div className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-4 flex-1 min-w-0">
                      <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-electric-cyan/20 to-violet-pulse/20 flex items-center justify-center flex-shrink-0">
                        <Building2 size={28} className="text-electric-cyan" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-lg font-semibold text-ghost-white truncate">{profile.company_name}</h3>
                          {profile.is_default && (
                            <Badge variant="soft" color="amber" size="sm"><Star size={10} className="mr-1" /> Default</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-silver">{profile.industry || profile.company_type}</p>
                        <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-muted-silver">
                          <span className="flex items-center gap-1"><Hash size={12} /> {profile.registration_number}</span>
                          <span className="flex items-center gap-1"><Mail size={12} /> {profile.email}</span>
                          <span className="flex items-center gap-1"><MapPin size={12} /> {profile.city}, {profile.state}</span>
                          <span className="flex items-center gap-1"><Users size={12} /> {profile.employee_count} employees</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5 mt-3">
                          {(profile.iso_certifications || []).map((cert) => (
                            <Badge key={cert} variant="outline" size="sm">{cert}</Badge>
                          ))}
                          {(profile.other_certifications || []).slice(0, 3).map((cert) => (
                            <Badge key={cert} variant="outline" color="cyan" size="sm">{cert}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {!profile.is_default && (
                        <Button variant="ghost" size="sm" leftIcon={<Star size={14} />} onClick={() => handleSetDefault(profile.id)}>
                          Set Default
                        </Button>
                      )}
                      <Button variant="ghost" size="sm" leftIcon={<Edit3 size={14} />}
                        onClick={() => { setEditingProfile({ ...profile }); setIsNew(false); setActiveSection(0); }}>
                        Edit
                      </Button>
                      <Button variant="ghost" size="sm" leftIcon={<Trash2 size={14} />}
                        onClick={() => setDeleteModal(profile.id)}
                        className="text-coral-flame hover:text-coral-flame">
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </motion.div>
      )}

      {/* ═══ Edit/Create Form ═══ */}
      {editingProfile && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          {/* Form Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-ghost-white">
              {isNew ? 'Create New Profile' : `Edit — ${editingProfile.company_name}`}
            </h2>
            <div className="flex gap-2">
              <Button variant="ghost" leftIcon={<X size={16} />} onClick={() => setEditingProfile(null)}>Cancel</Button>
              <Button variant="primary" leftIcon={saving ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Save size={16} />}
                onClick={handleSave} disabled={saving || !editingProfile.company_name}>
                {saving ? 'Saving...' : 'Save Profile'}
              </Button>
            </div>
          </div>

          {/* Section Tabs */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-steel-slate/20 w-fit overflow-x-auto">
            {sections.map((sec, i) => (
              <button key={sec.label} onClick={() => setActiveSection(i)}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  activeSection === i ? 'bg-neon-emerald/15 text-neon-emerald' : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30'
                }`}>
                {sec.icon} {sec.label}
              </button>
            ))}
          </div>

          {/* Section 0: Company Info */}
          {activeSection === 0 && (
            <Card variant="glass" className="p-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Company Name *" value={editingProfile.company_name || ''} onChange={(v) => updateField('company_name', v)} />
                <FormField label="Trading Name" value={editingProfile.trading_name || ''} onChange={(v) => updateField('trading_name', v)} />
                <FormField label="Registration Number" value={editingProfile.registration_number || ''} onChange={(v) => updateField('registration_number', v)} />
                <FormField label="Tax ID" value={editingProfile.tax_id || ''} onChange={(v) => updateField('tax_id', v)} />
                <FormField label="GST Number" value={editingProfile.gst_number || ''} onChange={(v) => updateField('gst_number', v)} />
                <FormField label="PAN Number" value={editingProfile.pan_number || ''} onChange={(v) => updateField('pan_number', v)} />
                <FormField label="Incorporation Date" value={editingProfile.incorporation_date || ''} onChange={(v) => updateField('incorporation_date', v)} type="date" />
                <FormSelect label="Company Type" value={editingProfile.company_type || 'Private Limited'}
                  onChange={(v) => updateField('company_type', v)}
                  options={['Private Limited', 'Public Limited', 'LLP', 'Partnership', 'Sole Proprietorship', 'Government Body']} />
                <FormField label="Industry" value={editingProfile.industry || ''} onChange={(v) => updateField('industry', v)} />
                <FormField label="Website" value={editingProfile.website || ''} onChange={(v) => updateField('website', v)} />
              </div>
            </Card>
          )}

          {/* Section 1: Contact */}
          {activeSection === 1 && (
            <Card variant="glass" className="p-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Email" value={editingProfile.email || ''} onChange={(v) => updateField('email', v)} />
                <FormField label="Phone" value={editingProfile.phone || ''} onChange={(v) => updateField('phone', v)} />
                <FormField label="Fax" value={editingProfile.fax || ''} onChange={(v) => updateField('fax', v)} />
                <div className="col-span-full"><hr className="border-steel-slate/20" /></div>
                <FormField label="Address Line 1" value={editingProfile.address_line1 || ''} onChange={(v) => updateField('address_line1', v)} />
                <FormField label="Address Line 2" value={editingProfile.address_line2 || ''} onChange={(v) => updateField('address_line2', v)} />
                <FormField label="City" value={editingProfile.city || ''} onChange={(v) => updateField('city', v)} />
                <FormField label="State" value={editingProfile.state || ''} onChange={(v) => updateField('state', v)} />
                <FormField label="Country" value={editingProfile.country || ''} onChange={(v) => updateField('country', v)} />
                <FormField label="Postal Code" value={editingProfile.postal_code || ''} onChange={(v) => updateField('postal_code', v)} />
              </div>
            </Card>
          )}

          {/* Section 2: Authorized Signatory */}
          {activeSection === 2 && (
            <Card variant="glass" className="p-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Signatory Name" value={editingProfile.authorized_signatory || ''} onChange={(v) => updateField('authorized_signatory', v)} />
                <FormField label="Designation" value={editingProfile.signatory_designation || ''} onChange={(v) => updateField('signatory_designation', v)} />
                <FormField label="Signatory Email" value={editingProfile.signatory_email || ''} onChange={(v) => updateField('signatory_email', v)} />
                <FormField label="Signatory Phone" value={editingProfile.signatory_phone || ''} onChange={(v) => updateField('signatory_phone', v)} />
              </div>
            </Card>
          )}

          {/* Section 3: Bank Details */}
          {activeSection === 3 && (
            <Card variant="glass" className="p-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Bank Name" value={editingProfile.bank_name || ''} onChange={(v) => updateField('bank_name', v)} />
                <FormField label="Branch" value={editingProfile.bank_branch || ''} onChange={(v) => updateField('bank_branch', v)} />
                <FormField label="Account Number" value={editingProfile.bank_account || ''} onChange={(v) => updateField('bank_account', v)} />
                <FormField label="IFSC Code" value={editingProfile.bank_ifsc || ''} onChange={(v) => updateField('bank_ifsc', v)} />
                <FormField label="SWIFT Code" value={editingProfile.bank_swift || ''} onChange={(v) => updateField('bank_swift', v)} />
              </div>
            </Card>
          )}

          {/* Section 4: Certifications */}
          {activeSection === 4 && (
            <Card variant="glass" className="p-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="ISO Certifications (comma separated)" value={(editingProfile.iso_certifications || []).join(', ')}
                  onChange={(v) => updateArrayField('iso_certifications', v)} />
                <FormField label="BIS License" value={editingProfile.bis_license || ''} onChange={(v) => updateField('bis_license', v)} />
                <FormField label="Other Certifications (comma separated)" value={(editingProfile.other_certifications || []).join(', ')}
                  onChange={(v) => updateArrayField('other_certifications', v)} />
              </div>
            </Card>
          )}

          {/* Section 5: Experience */}
          {activeSection === 5 && (
            <Card variant="glass" className="p-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="Annual Turnover" value={editingProfile.annual_turnover || ''} onChange={(v) => updateField('annual_turnover', v)} />
                <FormField label="Employee Count" value={String(editingProfile.employee_count || '')} onChange={(v) => updateField('employee_count', parseInt(v) || 0)} />
                <FormField label="Years of Experience" value={String(editingProfile.experience_years || '')} onChange={(v) => updateField('experience_years', parseInt(v) || 0)} />
                <FormField label="Key Clients (comma separated)" value={(editingProfile.key_clients || []).join(', ')}
                  onChange={(v) => updateArrayField('key_clients', v)} />
              </div>
            </Card>
          )}
        </motion.div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal open={!!deleteModal} onClose={() => setDeleteModal(null)} title="Delete Profile" size="sm">
        <div className="p-4 space-y-4">
          <p className="text-sm text-muted-silver">Are you sure you want to delete this company profile? This cannot be undone.</p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setDeleteModal(null)}>Cancel</Button>
            <Button variant="primary" size="sm" className="bg-coral-flame hover:bg-coral-flame/80"
              onClick={() => deleteModal && handleDelete(deleteModal)}>Delete Profile</Button>
          </div>
        </div>
      </Modal>
    </motion.div>
  );
}

// ── Form sub-components ──

function FormField({ label, value, onChange, type = 'text' }: { label: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <div>
      <label className="text-xs text-muted-silver uppercase tracking-wider mb-1.5 block">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/40 focus:outline-none focus:border-neon-emerald/40 transition-colors"
      />
    </div>
  );
}

function FormSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <div>
      <label className="text-xs text-muted-silver uppercase tracking-wider mb-1.5 block">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2.5 rounded-xl glass-input text-sm text-ghost-white bg-transparent focus:outline-none focus:border-neon-emerald/40 transition-colors"
      >
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}
