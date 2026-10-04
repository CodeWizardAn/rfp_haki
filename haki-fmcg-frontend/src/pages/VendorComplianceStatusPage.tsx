import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, Shield, CheckCircle2, XCircle, Clock, AlertTriangle, RefreshCw } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface ComplianceItem { vendor: string; cert: string; status: 'valid' | 'expiring' | 'expired' | 'pending'; issuedDate: string; expiryDate: string; issuer: string; }

const initialItems: ComplianceItem[] = [
  { vendor: 'Havells India', cert: 'BIS ISI Mark (IS 7098)', status: 'valid', issuedDate: '2025-06-15', expiryDate: '2027-06-14', issuer: 'Bureau of Indian Standards' },
  { vendor: 'Havells India', cert: 'ISO 9001:2015', status: 'valid', issuedDate: '2024-12-01', expiryDate: '2027-11-30', issuer: 'TÜV SÜD' },
  { vendor: 'Polycab', cert: 'BIS ISI Mark (IS 7098)', status: 'valid', issuedDate: '2025-03-20', expiryDate: '2027-03-19', issuer: 'Bureau of Indian Standards' },
  { vendor: 'KEI Industries', cert: 'BIS ISI Mark (IS 1554)', status: 'expiring', issuedDate: '2024-02-28', expiryDate: '2026-02-27', issuer: 'Bureau of Indian Standards' },
  { vendor: 'KEI Industries', cert: 'ISO 14001:2015', status: 'valid', issuedDate: '2025-01-10', expiryDate: '2028-01-09', issuer: 'DNV GL' },
  { vendor: 'Finolex Cables', cert: 'BIS ISI Mark (IS 7098)', status: 'expired', issuedDate: '2023-06-01', expiryDate: '2025-05-31', issuer: 'Bureau of Indian Standards' },
  { vendor: 'RR Kabel', cert: 'Factory Inspection', status: 'pending', issuedDate: '—', expiryDate: '—', issuer: 'NABL Accredited Lab' },
];

const statusCfg: Record<string, { icon: typeof CheckCircle2; color: string; badge: 'emerald' | 'amber' | 'coral' | 'teal' }> = {
  valid: { icon: CheckCircle2, color: 'text-neon-emerald', badge: 'emerald' },
  expiring: { icon: AlertTriangle, color: 'text-amber-glow', badge: 'amber' },
  expired: { icon: XCircle, color: 'text-coral-flame', badge: 'coral' },
  pending: { icon: Clock, color: 'text-teal-depth', badge: 'teal' },
};

export default function VendorComplianceStatusPage() {
  const [complianceList, setComplianceList] = useState<ComplianceItem[]>(initialItems);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const stats = {
    valid: complianceList.filter((i) => i.status === 'valid').length,
    expiring: complianceList.filter((i) => i.status === 'expiring').length,
    expired: complianceList.filter((i) => i.status === 'expired').length,
    pending: complianceList.filter((i) => i.status === 'pending').length,
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      toast.success('Compliance certificates and audit registries synchronized');
    }, 600);
  };

  const handleViewCert = (item: ComplianceItem) => {
    toast.success(`Viewing certificate details: ${item.cert} (Issued by ${item.issuer})`);
  };

  const handleRequestRenewal = (index: number, item: ComplianceItem) => {
    setComplianceList((prev) =>
      prev.map((c, i) => (i === index ? { ...c, status: 'pending' as const } : c))
    );
    toast.success(`Renewal notification sent to ${item.vendor} for ${item.cert}`);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Vendor Compliance Status</h1><p className="text-body text-muted-silver">Certificate tracking and regulatory compliance</p></div>
        </div>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2 text-sm text-electric-cyan hover:text-electric-cyan/80 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
          {isRefreshing ? 'Refreshing…' : 'Refresh Status'}
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { l: 'Valid', v: stats.valid, c: 'text-neon-emerald', icon: CheckCircle2 },
          { l: 'Expiring Soon', v: stats.expiring, c: 'text-amber-glow', icon: AlertTriangle },
          { l: 'Expired', v: stats.expired, c: 'text-coral-flame', icon: XCircle },
          { l: 'Pending', v: stats.pending, c: 'text-teal-depth', icon: Clock },
        ].map((s) => (
          <Card key={s.l} variant="glass" className="p-4 text-center">
            <s.icon size={18} className={`${s.c} mx-auto mb-2`} />
            <span className={`text-2xl font-bold ${s.c}`}>{s.v}</span>
            <span className="text-xs text-muted-silver block mt-1">{s.l}</span>
          </Card>
        ))}
      </div>

      <Card variant="glass" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-steel-slate/20">
                {['Vendor', 'Certificate', 'Status', 'Issued', 'Expiry', 'Issuer', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-muted-silver font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {complianceList.map((item, i) => {
                const cfg = (statusCfg[item.status] ?? statusCfg['pending'])!;
                const Icon = cfg.icon;
                return (
                  <tr key={i} className="border-b border-steel-slate/10 hover:bg-steel-slate/5">
                    <td className="px-4 py-3 text-ghost-white font-semibold">{item.vendor}</td>
                    <td className="px-4 py-3"><div className="flex items-center gap-1"><Shield size={10} className="text-electric-cyan" /><span className="text-ghost-white">{item.cert}</span></div></td>
                    <td className="px-4 py-3"><Badge variant="soft" color={cfg.badge} size="sm"><Icon size={10} className="inline mr-0.5" />{item.status}</Badge></td>
                    <td className="px-4 py-3 text-muted-silver">{item.issuedDate}</td>
                    <td className="px-4 py-3 text-muted-silver">{item.expiryDate}</td>
                    <td className="px-4 py-3 text-muted-silver">{item.issuer}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleViewCert(item)}
                          className="text-electric-cyan hover:underline text-[10px]"
                        >
                          View
                        </button>
                        {item.status === 'expired' && (
                          <button
                            type="button"
                            onClick={() => handleRequestRenewal(i, item)}
                            className="text-coral-flame hover:underline text-[10px]"
                          >
                            Request Renewal
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
