import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  ArrowLeft,
  Building2,
  Star,
  MapPin,
  Phone,
  Mail,
  Globe,
  Shield,
  TrendingUp,
  TrendingDown,
  Package,
  FileText,
  Award,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Edit3,
} from 'lucide-react';
import { Button, Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { formatCompactCurrency } from '@/utils/formatters';
import {
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

const mockVendor = {
  id: 'VND-001',
  name: 'Havells India Ltd',
  gst: '07AAACH0111E1ZF',
  pan: 'AAACH0111E',
  category: 'OEM',
  badge: 'Gold Partner',
  rating: 4.7,
  score: 92,
  status: 'active' as const,
  address: 'QRG Towers, 2D, Janpath, New Delhi 110001',
  phone: '+91 11 4000 5000',
  email: 'procurement@havells.com',
  website: 'www.havells.com',
  categories: ['Wires', 'LT Cables', 'HT Cables', 'Control Cables'],
  certifications: [
    { name: 'BIS IS 694', status: 'valid', expiry: '2027-06-15' },
    { name: 'BIS IS 1554', status: 'valid', expiry: '2027-03-20' },
    { name: 'ISO 9001:2015', status: 'valid', expiry: '2026-12-01' },
    { name: 'CPRI Type Test', status: 'expiring', expiry: '2026-03-15' },
    { name: 'BIS IS 7098', status: 'valid', expiry: '2027-09-10' },
  ],
  metrics: {
    totalRevenue: 85000000,
    bidsWon: 24,
    bidsTotal: 35,
    avgDelivery: 14,
    onTimeRate: 96,
    qualityScore: 93,
    responseTime: 4.2,
    complianceRate: 95,
    defectRate: 0.8,
  },
};

const radarData = [
  { metric: 'Delivery', value: 96 },
  { metric: 'Quality', value: 93 },
  { metric: 'Response', value: 88 },
  { metric: 'Compliance', value: 95 },
  { metric: 'Price', value: 82 },
];

const deliveryData = [
  { month: 'Sep', onTime: 12, late: 1 },
  { month: 'Oct', onTime: 15, late: 0 },
  { month: 'Nov', onTime: 10, late: 2 },
  { month: 'Dec', onTime: 14, late: 1 },
  { month: 'Jan', onTime: 18, late: 0 },
  { month: 'Feb', onTime: 8, late: 0 },
];

const bidHistory = [
  { id: 'BID-2026-001', rfp: 'RFP-2026-0001', amount: 25340000, status: 'won', date: '2026-02-04' },
  { id: 'BID-2026-008', rfp: 'RFP-2026-0003', amount: 12800000, status: 'submitted', date: '2026-02-02' },
  { id: 'BID-2025-045', rfp: 'RFP-2025-0089', amount: 18500000, status: 'won', date: '2025-12-18' },
  { id: 'BID-2025-038', rfp: 'RFP-2025-0076', amount: 9200000, status: 'lost', date: '2025-11-22' },
  { id: 'BID-2025-029', rfp: 'RFP-2025-0065', amount: 31000000, status: 'won', date: '2025-10-15' },
];

const tooltipStyle = {
  contentStyle: { background: 'rgba(18, 24, 51, 0.95)', border: '1px solid rgba(30, 38, 66, 0.5)', borderRadius: 12 },
  labelStyle: { color: '#E8ECF4' },
};

type TabId = 'performance' | 'bids' | 'certifications' | 'audit';

export default function VendorProfilePage() {
  const { vendorId } = useParams();
  const [activeTab, setActiveTab] = useState<TabId>('performance');
  const v = mockVendor;
  const [vendorRating, setVendorRating] = useState(v.rating);
  const [ratingModal, setRatingModal] = useState(false);
  const [selectedStars, setSelectedStars] = useState(5);
  const [isEditing, setIsEditing] = useState(false);
  const [contactEmail, setContactEmail] = useState(v.email);
  const [contactPhone, setContactPhone] = useState(v.phone);

  const winRate = Math.round((v.metrics.bidsWon / v.metrics.bidsTotal) * 100);

  const handleSaveContact = () => {
    setIsEditing(false);
    toast.success('Vendor contact details updated successfully!');
  };

  const handleRateSubmit = () => {
    const updated = Number(((vendorRating * 4 + selectedStars) / 5).toFixed(1));
    setVendorRating(updated);
    setRatingModal(false);
    toast.success(`Rating submitted! Vendor rating updated to ${updated} ★`);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div className="w-12 h-12 rounded-2xl bg-electric-cyan/10 flex items-center justify-center">
            <Building2 size={22} className="text-electric-cyan" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-h1 text-ghost-white">{v.name}</h1>
              <Badge variant="soft" color="amber" size="sm">
                <Award size={10} className="mr-1" />{v.badge}
              </Badge>
            </div>
            <div className="flex items-center gap-3 text-xs text-muted-silver">
              <span className="font-mono">{vendorId || v.id}</span>
              <span className="flex items-center gap-1"><MapPin size={10} />{v.address.split(',').slice(-2).join(',')}</span>
              <span className="flex items-center gap-1 text-amber-glow font-semibold"><Star size={11} className="fill-amber-glow" />{vendorRating}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            leftIcon={<Edit3 size={14} />}
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing ? 'Cancel Edit' : 'Edit Contact'}
          </Button>
          <Button
            variant="primary"
            leftIcon={<Star size={14} />}
            onClick={() => setRatingModal(true)}
          >
            Rate Vendor
          </Button>
        </div>
      </div>

      {/* Quick Edit Contact Bar if Active */}
      <AnimatePresence>
        {isEditing && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-4 rounded-xl bg-electric-cyan/10 border border-electric-cyan/30 flex flex-wrap items-center justify-between gap-3"
          >
            <div className="flex flex-wrap items-center gap-4 flex-1">
              <div>
                <label className="text-xs text-muted-silver block mb-1">Email</label>
                <input
                  type="email"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  className="bg-deep-navy px-3 py-1.5 rounded-lg border border-steel-slate text-sm text-ghost-white"
                />
              </div>
              <div>
                <label className="text-xs text-muted-silver block mb-1">Phone</label>
                <input
                  type="text"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  className="bg-deep-navy px-3 py-1.5 rounded-lg border border-steel-slate text-sm text-ghost-white"
                />
              </div>
            </div>
            <Button variant="primary" size="sm" onClick={handleSaveContact}>
              Save Contact
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Rate Vendor Modal */}
      <AnimatePresence>
        {ratingModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-[#121833] border border-steel-slate/60 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4"
            >
              <h3 className="text-lg font-bold text-ghost-white">Rate {v.name}</h3>
              <p className="text-xs text-muted-silver">Submit your performance and delivery rating for this vendor.</p>
              <div className="flex items-center justify-center gap-2 py-4">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setSelectedStars(star)}
                    className="p-2 transition-transform hover:scale-125 focus:outline-none"
                  >
                    <Star
                      size={28}
                      className={star <= selectedStars ? 'text-amber-glow fill-amber-glow' : 'text-steel-slate'}
                    />
                  </button>
                ))}
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <Button variant="ghost" size="sm" onClick={() => setRatingModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" onClick={handleRateSubmit}>
                  Submit Rating
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Top Row: Info + Score */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Company Info */}
        <Card variant="glass" className="lg:col-span-2">
          <CardHeader><CardTitle>Company Information</CardTitle></CardHeader>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {([
              [<Globe size={14} key="g" />, 'Website', v.website],
              [<Mail size={14} key="m" />, 'Email', v.email],
              [<Phone size={14} key="p" />, 'Phone', v.phone],
              [<FileText size={14} key="f" />, 'GST', v.gst],
              [<Shield size={14} key="s" />, 'PAN', v.pan],
              [<Package size={14} key="pk" />, 'Category', v.category],
            ] as [React.ReactNode, string, string][]).map(([icon, label, value]) => (
              <div key={label} className="flex items-center gap-2">
                <span className="text-muted-silver">{icon}</span>
                <div>
                  <p className="text-[10px] text-muted-silver uppercase tracking-wide">{label}</p>
                  <p className="text-sm text-ghost-white">{value}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="flex gap-1.5 mt-4 flex-wrap">
            {v.categories.map((cat) => (
              <Badge key={cat} variant="soft" color="cyan" size="sm">{cat}</Badge>
            ))}
          </div>
        </Card>

        {/* Score Gauge */}
        <Card variant="glass" className="flex flex-col items-center justify-center">
          <div className="relative w-28 h-28">
            <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#1E2642" strokeWidth="8" />
              <motion.circle
                cx="50" cy="50" r="42" fill="none"
                stroke={v.score >= 90 ? '#00E68A' : v.score >= 70 ? '#FFB224' : '#FF4757'}
                strokeWidth="8"
                strokeLinecap="round"
                initial={{ strokeDasharray: '0 264' }}
                animate={{ strokeDasharray: `${v.score * 2.64} 264` }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-ghost-white">{v.score}</span>
              <span className="text-[10px] text-muted-silver">/100</span>
            </div>
          </div>
          <div className="flex items-center gap-1 mt-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star key={i} size={14} className={i < Math.floor(v.rating) ? 'text-amber-glow fill-amber-glow' : 'text-steel-slate/30'} />
            ))}
            <span className="text-xs text-muted-silver ml-1">{v.rating}</span>
          </div>
          <p className="text-xs text-muted-silver mt-1">Overall Score</p>
        </Card>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {([
          { label: 'Revenue', value: formatCompactCurrency(v.metrics.totalRevenue), icon: <TrendingUp size={14} />, color: 'text-neon-emerald' },
          { label: 'Win Rate', value: `${winRate}%`, icon: <Award size={14} />, color: 'text-electric-cyan' },
          { label: 'On-Time', value: `${v.metrics.onTimeRate}%`, icon: <Clock size={14} />, color: 'text-amber-glow' },
          { label: 'Quality', value: `${v.metrics.qualityScore}%`, icon: <CheckCircle2 size={14} />, color: 'text-violet-pulse' },
        ]).map((stat) => (
          <Card key={stat.label} variant="glass">
            <div className="flex items-center gap-2 mb-1">
              <span className={stat.color}>{stat.icon}</span>
              <span className="text-xs text-muted-silver">{stat.label}</span>
            </div>
            <p className="text-xl font-bold text-ghost-white">{stat.value}</p>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-steel-slate/20 overflow-x-auto">
        {([
          { id: 'performance' as TabId, label: 'Performance' },
          { id: 'bids' as TabId, label: 'Bids' },
          { id: 'certifications' as TabId, label: 'Certifications' },
          { id: 'audit' as TabId, label: 'Audit' },
        ]).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id ? 'text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'
            }`}
          >
            {tab.label}
            {activeTab === tab.id && (
              <motion.div layoutId="vendor-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-electric-cyan rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
          {/* Performance Tab */}
          {activeTab === 'performance' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Radar Chart */}
              <Card variant="glass">
                <CardHeader><CardTitle>Performance Radar</CardTitle></CardHeader>
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#1E2642" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: '#8892B0', fontSize: 11 }} />
                    <Radar name="Score" dataKey="value" stroke="#00D4FF" fill="#00D4FF" fillOpacity={0.2} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </Card>

              {/* Delivery Chart */}
              <Card variant="glass">
                <CardHeader><CardTitle>Delivery Performance</CardTitle></CardHeader>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={deliveryData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E2642" />
                    <XAxis dataKey="month" tick={{ fill: '#8892B0', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#8892B0', fontSize: 11 }} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="onTime" name="On-Time" fill="#00E68A" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="late" name="Late" fill="#FF4757" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              {/* Key Metrics */}
              <Card variant="glass" className="lg:col-span-2">
                <CardHeader><CardTitle>Key Metrics</CardTitle></CardHeader>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                  {([
                    { label: 'Avg Delivery', value: `${v.metrics.avgDelivery} days`, trend: 'down' },
                    { label: 'On-Time Rate', value: `${v.metrics.onTimeRate}%`, trend: 'up' },
                    { label: 'Response Time', value: `${v.metrics.responseTime}h`, trend: 'down' },
                    { label: 'Defect Rate', value: `${v.metrics.defectRate}%`, trend: 'down' },
                    { label: 'Compliance', value: `${v.metrics.complianceRate}%`, trend: 'up' },
                  ] as { label: string; value: string; trend: string }[]).map((m) => (
                    <div key={m.label} className="text-center">
                      <p className="text-lg font-bold text-ghost-white">{m.value}</p>
                      <div className="flex items-center justify-center gap-1 mt-1">
                        {m.trend === 'up'
                          ? <TrendingUp size={10} className="text-neon-emerald" />
                          : <TrendingDown size={10} className="text-neon-emerald" />}
                        <span className="text-[10px] text-muted-silver">{m.label}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}

          {/* Bids Tab */}
          {activeTab === 'bids' && (
            <Card variant="glass">
              <CardHeader><CardTitle>Bid History ({bidHistory.length})</CardTitle></CardHeader>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-steel-slate/20">
                      <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase">Bid ID</th>
                      <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase">RFP</th>
                      <th className="py-2 px-4 text-right text-xs font-semibold text-muted-silver uppercase">Amount</th>
                      <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase">Status</th>
                      <th className="py-2 px-4 text-left text-xs font-semibold text-muted-silver uppercase">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bidHistory.map((bid) => (
                      <tr key={bid.id} className="border-b border-steel-slate/10 hover:bg-steel-slate/10 transition-colors">
                        <td className="py-3 px-4 font-mono text-electric-cyan text-xs">{bid.id}</td>
                        <td className="py-3 px-4 text-muted-silver text-xs">{bid.rfp}</td>
                        <td className="py-3 px-4 text-ghost-white font-bold text-right">{formatCompactCurrency(bid.amount)}</td>
                        <td className="py-3 px-4">
                          <Badge variant="soft" color={bid.status === 'won' ? 'emerald' : bid.status === 'lost' ? 'coral' : 'cyan'} size="sm">
                            {bid.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-muted-silver text-xs">{bid.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Certifications Tab */}
          {activeTab === 'certifications' && (
            <Card variant="glass">
              <CardHeader><CardTitle>Certifications & Standards</CardTitle></CardHeader>
              <div className="space-y-3">
                {v.certifications.map((cert) => (
                  <div key={cert.name} className="flex items-center justify-between py-3 border-b border-steel-slate/10 last:border-0">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        cert.status === 'valid' ? 'bg-neon-emerald/10' : 'bg-amber-glow/10'
                      }`}>
                        {cert.status === 'valid'
                          ? <CheckCircle2 size={16} className="text-neon-emerald" />
                          : <AlertTriangle size={16} className="text-amber-glow" />}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-ghost-white">{cert.name}</p>
                        <p className="text-xs text-muted-silver">Expires: {cert.expiry}</p>
                      </div>
                    </div>
                    <Badge variant="soft" color={cert.status === 'valid' ? 'emerald' : 'amber'} size="sm">
                      {cert.status === 'valid' ? 'Valid' : 'Expiring Soon'}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Audit Tab */}
          {activeTab === 'audit' && (
            <Card variant="glass">
              <CardHeader><CardTitle>Recent Activity</CardTitle></CardHeader>
              <div className="space-y-4">
                {([
                  { action: 'Bid Submitted', detail: 'BID-2026-008 submitted for RFP-2026-0003', date: '2026-02-02 11:30', type: 'bid' },
                  { action: 'Rating Updated', detail: 'Performance rating updated to 4.7/5.0', date: '2026-01-28 16:45', type: 'rating' },
                  { action: 'Bid Won', detail: 'BID-2026-001 won — ₹2.53 Cr', date: '2026-02-04 09:15', type: 'win' },
                  { action: 'Cert Renewal', detail: 'CPRI Type Test renewal initiated', date: '2026-01-20 14:00', type: 'cert' },
                  { action: 'Profile Updated', detail: 'Contact information updated by admin', date: '2026-01-15 10:20', type: 'profile' },
                ] as { action: string; detail: string; date: string; type: string }[]).map((entry, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-electric-cyan mt-1.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-ghost-white">{entry.action}</p>
                      <p className="text-xs text-muted-silver">{entry.detail}</p>
                      <p className="text-[10px] text-muted-silver/50 mt-0.5">{entry.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}
