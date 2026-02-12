import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Bell, BellOff, Clock, Calendar, AlertTriangle, CheckCircle2, Settings } from 'lucide-react';
import { Card, Badge } from '@/components/ui';

interface Notification { id: number; type: 'deadline' | 'approval' | 'revision' | 'system'; title: string; message: string; time: string; read: boolean; bidId: string; }

const notifications: Notification[] = [
  { id: 1, type: 'deadline', title: 'Submission Deadline in 2 Days', message: 'BID-2026-0044 must be submitted by Feb 8, 2026 17:00 IST', time: '1h ago', read: false, bidId: 'BID-2026-0044' },
  { id: 2, type: 'approval', title: 'Approval Required', message: 'BID-2026-0043 pricing review pending from VP Sales', time: '3h ago', read: false, bidId: 'BID-2026-0043' },
  { id: 3, type: 'revision', title: 'Revision Submitted', message: 'BID-2026-0042 Rev.3 submitted by Rajesh Kumar', time: '5h ago', read: true, bidId: 'BID-2026-0042' },
  { id: 4, type: 'system', title: 'Auto-Save Completed', message: 'BID-2026-0044 draft auto-saved successfully', time: '6h ago', read: true, bidId: 'BID-2026-0044' },
  { id: 5, type: 'deadline', title: 'Deadline Extended', message: 'BID-2026-0041 deadline extended to Feb 15, 2026', time: '1d ago', read: true, bidId: 'BID-2026-0041' },
  { id: 6, type: 'approval', title: 'Bid Approved', message: 'BID-2026-0040 approved by all reviewers, ready for submission', time: '2d ago', read: true, bidId: 'BID-2026-0040' },
];

const typeCfg: Record<string, { icon: typeof Clock; color: string; badgeColor: 'coral' | 'amber' | 'cyan' | 'teal' }> = {
  deadline: { icon: Calendar, color: 'text-coral-flame', badgeColor: 'coral' },
  approval: { icon: AlertTriangle, color: 'text-amber-glow', badgeColor: 'amber' },
  revision: { icon: Clock, color: 'text-electric-cyan', badgeColor: 'cyan' },
  system: { icon: CheckCircle2, color: 'text-teal-depth', badgeColor: 'teal' },
};

export default function BidNotificationsPage() {
  const [filter, setFilter] = useState<string>('all');
  const [items, setItems] = useState(notifications);

  const markRead = (id: number) => setItems((p) => p.map((n) => n.id === id ? { ...n, read: true } : n));
  const markAllRead = () => setItems((p) => p.map((n) => ({ ...n, read: true })));

  const filtered = filter === 'all' ? items : filter === 'unread' ? items.filter((n) => !n.read) : items.filter((n) => n.type === filter);
  const unreadCount = items.filter((n) => !n.read).length;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/bids" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors"><ArrowLeft size={18} className="text-muted-silver" /></Link>
          <div><h1 className="text-h1 text-ghost-white">Bid Notifications</h1><p className="text-body text-muted-silver">{unreadCount} unread notifications</p></div>
        </div>
        <div className="flex gap-2">
          <button onClick={markAllRead} className="text-xs text-electric-cyan hover:text-electric-cyan/80">Mark all read</button>
          <button className="p-2 rounded-lg hover:bg-steel-slate/15 text-muted-silver"><Settings size={14} /></button>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        {['all', 'unread', 'deadline', 'approval', 'revision', 'system'].map((f) => (
          <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs capitalize transition-colors ${filter === f ? 'bg-electric-cyan/15 text-electric-cyan border border-electric-cyan/30' : 'text-muted-silver border border-transparent hover:text-ghost-white'}`}>
            {f} {f === 'unread' && unreadCount > 0 && <span className="ml-1 bg-coral-flame/20 text-coral-flame px-1.5 rounded-full">{unreadCount}</span>}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {filtered.map((n) => {
          const cfg = (typeCfg[n.type] ?? typeCfg['system'])!;
          const Icon = cfg.icon;
          return (
            <motion.div key={n.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <Card variant="glass" className={`p-4 flex items-start gap-3 transition-colors ${!n.read ? 'border-l-2 border-l-electric-cyan bg-electric-cyan/[0.02]' : ''}`} onClick={() => markRead(n.id)}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${cfg.color.replace('text-', 'bg-')}/10`}>
                  <Icon size={14} className={cfg.color} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className={`text-sm font-semibold ${!n.read ? 'text-ghost-white' : 'text-muted-silver'}`}>{n.title}</h3>
                    <Badge variant="soft" color={cfg.badgeColor} size="sm">{n.type}</Badge>
                    {!n.read && <span className="w-2 h-2 rounded-full bg-electric-cyan" />}
                  </div>
                  <p className="text-xs text-muted-silver mt-0.5">{n.message}</p>
                  <div className="flex items-center gap-3 mt-1 text-[10px] text-muted-silver">
                    <span><Clock size={9} className="inline mr-0.5" />{n.time}</span>
                    <Link to={`/bids/${n.bidId}`} className="text-electric-cyan hover:underline">{n.bidId}</Link>
                  </div>
                </div>
                <button className="text-muted-silver/30 hover:text-muted-silver p-1">
                  {n.read ? <BellOff size={12} /> : <Bell size={12} />}
                </button>
              </Card>
            </motion.div>
          );
        })}
        {filtered.length === 0 && (
          <Card variant="glass" className="p-8 text-center">
            <Bell size={24} className="text-muted-silver/30 mx-auto mb-2" />
            <p className="text-sm text-muted-silver">No notifications matching this filter</p>
          </Card>
        )}
      </div>
    </motion.div>
  );
}
