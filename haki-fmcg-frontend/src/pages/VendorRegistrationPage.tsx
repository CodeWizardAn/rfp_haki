import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  User,
  Package,
  FileText,
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  Upload,
  X,
  AlertTriangle,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface FormData {
  name: string;
  gst: string;
  pan: string;
  address: string;
  city: string;
  state: string;
  pin: string;
  contactName: string;
  email: string;
  phone: string;
  website: string;
  categories: string[];
  documents: { name: string; file: string }[];
}

/* ─── data ─── */
const CATEGORIES = [
  'LT Power Cables', 'HT XLPE Cables', 'Control Cables', 'Fire Survival Cables',
  'Wiring Cables', 'Instrumentation Cables', 'Solar Cables', 'Marine Cables',
  'Cable Accessories', 'Jointing Kits', 'Cable Glands', 'Cable Trays',
];

const DOC_TYPES = [
  { id: 'gst_cert', label: 'GST Certificate', required: true },
  { id: 'pan_card', label: 'PAN Card', required: true },
  { id: 'iso_cert', label: 'ISO 9001 Certificate', required: false },
  { id: 'bis_cert', label: 'BIS License', required: false },
  { id: 'registration', label: 'Company Registration', required: true },
];

const steps = [
  { id: 'basic', label: 'Basic Info', icon: Building2 },
  { id: 'contact', label: 'Contact', icon: User },
  { id: 'products', label: 'Products', icon: Package },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'review', label: 'Review', icon: CheckCircle2 },
];

function validateGST(gst: string) {
  return /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$/.test(gst);
}
function validatePAN(pan: string) {
  return /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(pan);
}
function validateEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
function validatePhone(phone: string) {
  return /^[6-9]\d{9}$/.test(phone);
}

export default function VendorRegistrationPage() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormData>({
    name: '', gst: '', pan: '', address: '', city: '', state: '', pin: '',
    contactName: '', email: '', phone: '', website: '',
    categories: [],
    documents: [],
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const updateField = (field: keyof FormData, value: string) => {
    setForm((p) => ({ ...p, [field]: value }));
    setErrors((p) => { const n = { ...p }; delete n[field]; return n; });
  };

  const toggleCategory = (cat: string) => {
    setForm((p) => ({
      ...p,
      categories: p.categories.includes(cat) ? p.categories.filter((c) => c !== cat) : [...p.categories, cat],
    }));
  };

  const addDocument = (docId: string) => {
    if (!form.documents.find((d) => d.name === docId)) {
      setForm((p) => ({ ...p, documents: [...p.documents, { name: docId, file: `${docId}_uploaded.pdf` }] }));
    }
  };

  const removeDocument = (docId: string) => {
    setForm((p) => ({ ...p, documents: p.documents.filter((d) => d.name !== docId) }));
  };

  const validateStep = (s: number): boolean => {
    const errs: Record<string, string> = {};
    if (s === 0) {
      if (!form.name.trim()) errs.name = 'Company name is required';
      if (!form.gst.trim()) errs.gst = 'GST number is required';
      else if (!validateGST(form.gst)) errs.gst = 'Invalid GST format (e.g., 27AAPFU0939F1ZV)';
      if (!form.pan.trim()) errs.pan = 'PAN is required';
      else if (!validatePAN(form.pan)) errs.pan = 'Invalid PAN format (e.g., AAPFU0939F)';
      if (!form.address.trim()) errs.address = 'Address is required';
      if (!form.city.trim()) errs.city = 'City is required';
      if (!form.state.trim()) errs.state = 'State is required';
    } else if (s === 1) {
      if (!form.contactName.trim()) errs.contactName = 'Contact name is required';
      if (!form.email.trim()) errs.email = 'Email is required';
      else if (!validateEmail(form.email)) errs.email = 'Invalid email format';
      if (!form.phone.trim()) errs.phone = 'Phone is required';
      else if (!validatePhone(form.phone)) errs.phone = 'Invalid phone (10 digits starting 6-9)';
    } else if (s === 2) {
      if (form.categories.length === 0) errs.categories = 'Select at least one category';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const next = () => { if (validateStep(step) && step < 4) setStep(step + 1); };
  const prev = () => { if (step > 0) setStep(step - 1); };
  const submit = () => { setSubmitted(true); };

  const InputField = ({ label, field, placeholder, mono }: { label: string; field: keyof FormData; placeholder: string; mono?: boolean }) => (
    <div>
      <label className="text-xs text-muted-silver block mb-1">{label}</label>
      <input
        value={form[field] as string}
        onChange={(e) => updateField(field, e.target.value)}
        placeholder={placeholder}
        className={`glass-input w-full rounded-lg px-3 py-2 text-sm text-ghost-white ${mono ? 'font-mono uppercase' : ''} ${errors[field] ? 'border-coral-flame/40' : ''}`}
      />
      {errors[field] && <span className="text-[10px] text-coral-flame mt-0.5 block">{errors[field]}</span>}
    </div>
  );

  if (submitted) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center justify-center min-h-[60vh]">
        <Card variant="glass" className="p-8 text-center max-w-md">
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2, type: 'spring' }} className="w-16 h-16 rounded-full bg-neon-emerald/15 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={32} className="text-neon-emerald" />
          </motion.div>
          <h2 className="text-lg font-bold text-ghost-white mb-2">Registration Submitted!</h2>
          <p className="text-sm text-muted-silver mb-4">{form.name} has been registered. Our team will review and verify the details within 2-3 business days.</p>
          <p className="text-xs text-muted-silver font-mono mb-4">GST: {form.gst}</p>
          <Link to="/vendors">
            <Button>Back to Vendors</Button>
          </Link>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
          <ArrowLeft size={18} className="text-muted-silver" />
        </Link>
        <div>
          <h1 className="text-h1 text-ghost-white">Register New Vendor</h1>
          <p className="text-body text-muted-silver">Step {step + 1} of {steps.length}: {steps[step]?.label}</p>
        </div>
      </div>

      {/* Step Indicators */}
      <div className="flex items-center gap-1">
        {steps.map((s, i) => {
          const Icon = s.icon;
          const isComplete = i < step;
          const isCurrent = i === step;
          return (
            <div key={s.id} className="flex items-center flex-1">
              <button
                onClick={() => i < step && setStep(i)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors w-full
                  ${isCurrent ? 'bg-electric-cyan/10 text-electric-cyan border border-electric-cyan/30' : isComplete ? 'bg-neon-emerald/8 text-neon-emerald cursor-pointer' : 'text-muted-silver/50 cursor-default'}`}
              >
                {isComplete ? <CheckCircle2 size={13} /> : <Icon size={13} />}
                <span className="hidden md:inline">{s.label}</span>
              </button>
              {i < steps.length - 1 && <ChevronRight size={12} className="text-steel-slate/30 mx-1 flex-shrink-0" />}
            </div>
          );
        })}
      </div>

      {/* Step Content */}
      <Card variant="glass" className="p-5 min-h-[320px]">
        <motion.div key={step} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}>
          {/* Step 0: Basic Info */}
          {step === 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-ghost-white mb-3">Company Information</h3>
              <div className="grid md:grid-cols-2 gap-3">
                <InputField label="Company Name *" field="name" placeholder="e.g., Finolex Cables Ltd" />
                <InputField label="GST Number *" field="gst" placeholder="e.g., 27AAPFU0939F1ZV" mono />
              </div>
              <div className="grid md:grid-cols-2 gap-3">
                <InputField label="PAN Number *" field="pan" placeholder="e.g., AAPFU0939F" mono />
                <InputField label="PIN Code" field="pin" placeholder="e.g., 411026" mono />
              </div>
              <InputField label="Registered Address *" field="address" placeholder="Full address" />
              <div className="grid md:grid-cols-2 gap-3">
                <InputField label="City *" field="city" placeholder="e.g., Pune" />
                <InputField label="State *" field="state" placeholder="e.g., Maharashtra" />
              </div>
            </div>
          )}

          {/* Step 1: Contact */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-ghost-white mb-3">Contact Details</h3>
              <div className="grid md:grid-cols-2 gap-3">
                <InputField label="Contact Person *" field="contactName" placeholder="Full name" />
                <InputField label="Email *" field="email" placeholder="vendor@company.com" />
              </div>
              <div className="grid md:grid-cols-2 gap-3">
                <InputField label="Phone Number *" field="phone" placeholder="9876543210" mono />
                <InputField label="Website" field="website" placeholder="https://www.company.com" />
              </div>
            </div>
          )}

          {/* Step 2: Products / Categories */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-ghost-white mb-1">Product Categories</h3>
              <p className="text-xs text-muted-silver mb-3">Select the product categories this vendor supplies</p>
              {errors.categories && (
                <span className="text-[10px] text-coral-flame flex items-center gap-1"><AlertTriangle size={10} />{errors.categories}</span>
              )}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {CATEGORIES.map((cat) => {
                  const active = form.categories.includes(cat);
                  return (
                    <button
                      key={cat}
                      onClick={() => toggleCategory(cat)}
                      className={`p-2.5 rounded-lg text-xs text-left transition-all border
                        ${active ? 'border-electric-cyan/40 bg-electric-cyan/8 text-electric-cyan' : 'border-steel-slate/15 text-muted-silver hover:border-steel-slate/30'}`}
                    >
                      <span className="block">{cat}</span>
                      {active && <CheckCircle2 size={11} className="mt-1 text-electric-cyan" />}
                    </button>
                  );
                })}
              </div>
              <p className="text-[10px] text-muted-silver">{form.categories.length} selected</p>
            </div>
          )}

          {/* Step 3: Documents */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-ghost-white mb-3">Upload Documents</h3>
              <div className="space-y-2">
                {DOC_TYPES.map((doc) => {
                  const uploaded = form.documents.find((d) => d.name === doc.id);
                  return (
                    <div key={doc.id} className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${uploaded ? 'border-neon-emerald/30 bg-neon-emerald/5' : 'border-steel-slate/15 bg-steel-slate/5'}`}>
                      <FileText size={14} className={uploaded ? 'text-neon-emerald' : 'text-muted-silver'} />
                      <div className="flex-1">
                        <span className="text-xs text-ghost-white">{doc.label}</span>
                        {doc.required && <span className="text-[9px] text-coral-flame ml-1">*</span>}
                        {uploaded && <span className="text-[10px] text-neon-emerald block">{uploaded.file}</span>}
                      </div>
                      {uploaded ? (
                        <button onClick={() => removeDocument(doc.id)} className="p-1 rounded hover:bg-steel-slate/15">
                          <X size={12} className="text-muted-silver" />
                        </button>
                      ) : (
                        <Button variant="secondary" size="sm" leftIcon={<Upload size={11} />} onClick={() => addDocument(doc.id)}>Upload</Button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-ghost-white mb-3">Review & Submit</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-steel-slate/8 space-y-1.5">
                  <h4 className="text-[10px] text-muted-silver font-medium uppercase tracking-wider">Company</h4>
                  <p className="text-sm text-ghost-white font-semibold">{form.name || '—'}</p>
                  <p className="text-xs text-muted-silver font-mono">GST: {form.gst || '—'}</p>
                  <p className="text-xs text-muted-silver font-mono">PAN: {form.pan || '—'}</p>
                  <p className="text-xs text-muted-silver">{form.address}, {form.city}, {form.state} {form.pin}</p>
                </div>
                <div className="p-3 rounded-lg bg-steel-slate/8 space-y-1.5">
                  <h4 className="text-[10px] text-muted-silver font-medium uppercase tracking-wider">Contact</h4>
                  <p className="text-sm text-ghost-white font-semibold">{form.contactName || '—'}</p>
                  <p className="text-xs text-muted-silver">{form.email || '—'}</p>
                  <p className="text-xs text-muted-silver font-mono">{form.phone || '—'}</p>
                  {form.website && <p className="text-xs text-electric-cyan">{form.website}</p>}
                </div>
                <div className="p-3 rounded-lg bg-steel-slate/8 space-y-1.5">
                  <h4 className="text-[10px] text-muted-silver font-medium uppercase tracking-wider">Categories ({form.categories.length})</h4>
                  <div className="flex flex-wrap gap-1">
                    {form.categories.map((c) => <Badge key={c} variant="soft" color="cyan" size="sm">{c}</Badge>)}
                    {form.categories.length === 0 && <span className="text-xs text-muted-silver">None selected</span>}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-steel-slate/8 space-y-1.5">
                  <h4 className="text-[10px] text-muted-silver font-medium uppercase tracking-wider">Documents ({form.documents.length}/{DOC_TYPES.filter((d) => d.required).length} required)</h4>
                  {form.documents.map((d) => (
                    <span key={d.name} className="text-xs text-neon-emerald flex items-center gap-1"><CheckCircle2 size={10} />{DOC_TYPES.find((t) => t.id === d.name)?.label}</span>
                  ))}
                  {form.documents.length === 0 && <span className="text-xs text-amber-glow">No documents uploaded</span>}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="secondary" leftIcon={<ChevronLeft size={14} />} onClick={prev} disabled={step === 0}>Previous</Button>
        {step < 4 ? (
          <Button rightIcon={<ChevronRight size={14} />} onClick={next}>Next</Button>
        ) : (
          <Button leftIcon={<CheckCircle2 size={14} />} onClick={submit}>Submit Registration</Button>
        )}
      </div>
    </motion.div>
  );
}
