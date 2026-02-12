import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Activity, FileText, DollarSign, MessageSquare, CheckCircle2, Clock } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface ActivityItem { id: number; vendor: string; type: 'bid' | 'communication' | 'compliance' | 'pricing' | 'onboarding'; description: string; timestamp: string; status: 'completed' | 'pending' | 'failed'; }

const activities: ActivityItem[] = [
  { id: 1, vendor: 'Havells India', type: 'bid', description: 'Submitted bid for RFP-2026-0044 (Power Cables) — ₹1.78Cr', timestamp: '2h ago', status: 'completed' },
  { id: 2, vendor: 'Polycab', type: 'communication', description: 'Received updated price list for Q1 2026', timestamp: '4h ago', status: 'completed' },
  { id: 3, vendor: 'KEI Industries', type: 'compliance', description: 'BIS Certificate renewal pending — expires Feb 28', timestamp: '6h ago', status: 'pending' },
  { id: 4, vendor: 'Finolex Cables', type: 'pricing', description: 'Bulk pricing negotiation — 8% discount requested for 50km order', timestamp: '1d ago', status: 'pending' },
  { id: 5, vendor: 'RR Kabel', type: 'onboarding', description: 'New vendor registration submitted — documents under review', timestamp: '1d ago', status: 'pending' },
  { id: 6, vendor: 'Havells India', type: 'compliance', description: 'ISO 9001:2015 certificate verified and approved', timestamp: '2d ago', status: 'completed' },
  { id: 7, vendor: 'Polycab', type: 'bid', description: 'Bid was shortlisted for RFP-2026-0042 (Control Cables)', timestamp: '2d ago', status: 'completed' },
  { id: 8, vendor: 'Sterlite Power', type: 'communication', description: 'Meeting scheduled for EHV cable specs discussion', timestamp: '3d ago', status: 'completed' },
  { id: 9, vendor: 'KEI Industries', type: 'pricing', description: 'Price revision rejected — exceeds budget by 15%', timestamp: '3d ago', status: 'failed' },
];

const typeCfg: Record<string, { icon: typeof Activity; color: string; badge: 'cyan' | 'amber' | 'emerald' | 'violet' | 'teal' }> = {
  bid: { icon: FileText, color: 'text-electric-cyan', badge: 'cyan' },
  communication: { icon: MessageSquare, color: 'text-amber-glow', badge: 'amber' },
  compliance: { icon: CheckCircle2, color: 'text-neon-emerald', badge: 'emerald' },
  pricing: { icon: DollarSign, color: 'text-violet-pulse', badge: 'violet' },
  onboarding: { icon: Activity, color: 'text-teal-depth', badge: 'teal' },
};

export default function VendorActivityFeedPage() {
  const [filter, setFilter] = useState<string>('all');
  const filtered = filter === 'all' ? activities : activities.filter((a) => a.type === filter);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
        <div><h1 className="text-h1 text-ghost-white">Vendor Activity Feed</h1><p className="text-body text-muted-silver">Real-time vendor activities and interactions</p></div>
      </div>

      <div className="flex gap-2 flex-wrap">
        {['all', 'bid', 'communication', 'compliance', 'pricing', 'onboarding'].map((f) => (
          <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs capitalize transition-colors ${filter === f ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30' : 'text-muted-silver border border-transparent hover:text-ghost-white'}`}>{f}</button>
        ))}
      </div>

      <div className="relative">
        <div className="absolute left-[19px] top-0 bottom-0 w-px bg-steel-slate/20" />
        <div className="space-y-4">
          {filtered.map((a, i) => {
            const cfg = (typeCfg[a.type] ?? typeCfg['bid'])!;
            const Icon = cfg.icon;
            return (
              <motion.div key={a.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }} className="flex gap-4 relative">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 z-10 ${cfg.color.replace('text-', 'bg-')}/10 border-2 border-deep-navy`}>
                  <Icon size={16} className={cfg.color} />
                </div>
                <Card variant="glass" className="flex-1 p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-ghost-white">{a.vendor}</span>
                        <Badge variant="soft" color={cfg.badge} size="sm">{a.type}</Badge>
                        <Badge variant="soft" color={a.status === 'completed' ? 'emerald' : a.status === 'pending' ? 'amber' : 'coral'} size="sm">{a.status}</Badge>
                      </div>
                      <p className="text-xs text-muted-silver">{a.description}</p>
                    </div>
                    <span className="text-[10px] text-muted-silver whitespace-nowrap ml-3"><Clock size={9} className="inline mr-0.5" />{a.timestamp}</span>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
