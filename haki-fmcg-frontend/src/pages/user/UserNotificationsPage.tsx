import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  Info,
  XCircle,
  Clock,
  Check,
  Trash2,
  Filter,
} from 'lucide-react';
import { Card, Badge, Button } from '@/components/ui';

interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  timestamp: string;
  action?: string;
}

const mockNotifications: NotificationItem[] = [
  { id: '1', type: 'success', title: 'Bid Approved', message: 'Your bid BID-0084 for FMCG Products Q1 Restock has been approved by the review committee.', read: false, timestamp: '2 hours ago', action: '/user/bids' },
  { id: '2', type: 'warning', title: 'Deadline Approaching', message: 'REQ-2026-0042 submission deadline is in 3 days. Please ensure all required documents are uploaded.', read: false, timestamp: '5 hours ago', action: '/user/requests/REQ-2026-0042' },
  { id: '3', type: 'info', title: 'Quote Received', message: 'Polycab Wires Ltd has responded to your quote request QT-0158 for XLPE Power Cable.', read: false, timestamp: '1 day ago', action: '/user/quotes' },
  { id: '4', type: 'success', title: 'New Vendor Recommended', message: 'Based on your purchase history, we recommend Schneider Electric for your electrical equipment needs.', read: true, timestamp: '2 days ago', action: '/user/vendors' },
  { id: '5', type: 'info', title: 'Price Drop Alert', message: 'FR PVC Insulated Copper Cable 1.5 sq mm has dropped 5% from your last purchase price.', read: true, timestamp: '3 days ago', action: '/user/catalog/CAB-001' },
  { id: '6', type: 'success', title: 'Order Delivered', message: 'Your order from REQ-2026-0035 (Office Supplies) has been successfully delivered.', read: true, timestamp: '5 days ago' },
  { id: '7', type: 'error', title: 'Document Rejected', message: 'The compliance certificate uploaded for REQ-2026-0038 was rejected. Please upload a valid document.', read: true, timestamp: '1 week ago', action: '/user/requests/REQ-2026-0038' },
  { id: '8', type: 'info', title: 'System Maintenance', message: 'Scheduled maintenance on Feb 15, 2026 from 2:00 AM to 4:00 AM IST. The portal will be temporarily unavailable.', read: true, timestamp: '1 week ago' },
];

const typeConfig: Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
  info: { icon: <Info size={18} />, color: 'text-electric-cyan', bg: 'bg-electric-cyan/10' },
  success: { icon: <CheckCircle2 size={18} />, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10' },
  warning: { icon: <AlertTriangle size={18} />, color: 'text-amber-glow', bg: 'bg-amber-glow/10' },
  error: { icon: <XCircle size={18} />, color: 'text-coral-flame', bg: 'bg-coral-flame/10' },
};

const tabs = ['All', 'Unread', 'Info', 'Alerts'];

export default function UserNotificationsPage() {
  const [notifications, setNotifications] = useState(mockNotifications);
  const [activeTab, setActiveTab] = useState('All');

  const filtered = notifications.filter((n) => {
    if (activeTab === 'Unread') return !n.read;
    if (activeTab === 'Info') return n.type === 'info' || n.type === 'success';
    if (activeTab === 'Alerts') return n.type === 'warning' || n.type === 'error';
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, read: true })));
  };

  const markAsRead = (id: string) => {
    setNotifications(notifications.map((n) => n.id === id ? { ...n, read: true } : n));
  };

  const removeNotification = (id: string) => {
    setNotifications(notifications.filter((n) => n.id !== id));
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ghost-white">Notifications</h1>
          <p className="text-body text-muted-silver mt-1">
            {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'All caught up!'}
          </p>
        </div>
        {unreadCount > 0 && (
          <Button variant="secondary" size="sm" leftIcon={<Check size={14} />} onClick={markAllRead}>
            Mark All Read
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-4 border-b border-steel-slate/20">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2.5 text-sm font-medium transition-colors relative ${
              activeTab === tab ? 'text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'
            }`}
          >
            {tab}
            {tab === 'Unread' && unreadCount > 0 && (
              <span className="ml-1.5 text-[10px] bg-coral-flame text-white px-1.5 py-0.5 rounded-full">{unreadCount}</span>
            )}
            {activeTab === tab && (
              <motion.div layoutId="notif-tab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-electric-cyan rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Notification list */}
      <div className="space-y-2">
        {filtered.map((notif) => {
          const config = typeConfig[notif.type] ?? typeConfig.info!;
          return (
            <motion.div
              key={notif.id}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card
                variant={notif.read ? 'default' : 'glass'}
                className={`relative ${!notif.read ? 'border-l-2 border-l-electric-cyan' : ''}`}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-lg ${config.bg} flex items-center justify-center flex-shrink-0`}>
                    <span className={config.color}>{config.icon}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className={`text-sm font-semibold ${notif.read ? 'text-muted-silver' : 'text-ghost-white'}`}>
                        {notif.title}
                      </h3>
                      {!notif.read && (
                        <span className="w-2 h-2 rounded-full bg-electric-cyan flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-sm text-muted-silver leading-relaxed">{notif.message}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-[10px] text-muted-silver flex items-center gap-1">
                        <Clock size={10} /> {notif.timestamp}
                      </span>
                      {notif.action && !notif.read && (
                        <button
                          onClick={() => markAsRead(notif.id)}
                          className="text-[10px] text-electric-cyan hover:underline"
                        >
                          Mark as read
                        </button>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => removeNotification(notif.id)}
                    className="p-1.5 rounded-lg text-muted-silver/40 hover:text-coral-flame hover:bg-coral-flame/10 transition-colors flex-shrink-0"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </Card>
            </motion.div>
          );
        })}

        {filtered.length === 0 && (
          <Card className="flex flex-col items-center justify-center py-12">
            <Bell size={40} className="text-muted-silver/20 mb-3" />
            <p className="text-sm text-muted-silver">No notifications to show</p>
          </Card>
        )}
      </div>
    </motion.div>
  );
}
