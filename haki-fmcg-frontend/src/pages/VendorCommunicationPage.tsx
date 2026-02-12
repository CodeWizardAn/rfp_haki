import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  MessageSquare,
  Send,
  Paperclip,
  Search,
  Phone,
  Mail,
  FileText,
  AlertCircle,
  HelpCircle,
  MessageCircle,
} from 'lucide-react';
import { Button, Card } from '@/components/ui';

/* ─── types ─── */
type MsgType = 'inquiry' | 'quotation' | 'complaint' | 'general';

interface Message {
  id: string;
  sender: 'user' | 'vendor';
  senderName: string;
  content: string;
  timestamp: string;
  type: MsgType;
  attachment?: string;
}

interface VendorThread {
  vendorId: string;
  vendorName: string;
  lastMessage: string;
  lastTime: string;
  unread: number;
  avatar: string;
  status: 'online' | 'offline';
}

/* ─── data ─── */
const typeConfig: Record<MsgType, { icon: typeof MessageCircle; color: string; label: string }> = {
  inquiry: { icon: HelpCircle, color: 'text-electric-cyan', label: 'Inquiry' },
  quotation: { icon: FileText, color: 'text-neon-emerald', label: 'Quotation' },
  complaint: { icon: AlertCircle, color: 'text-coral-flame', label: 'Complaint' },
  general: { icon: MessageCircle, color: 'text-muted-silver', label: 'General' },
};

const threads: VendorThread[] = [
  { vendorId: 'v-001', vendorName: 'Finolex Cables', lastMessage: 'Updated pricing sheet attached for Q1 2026.', lastTime: '10 min', unread: 2, avatar: 'FC', status: 'online' },
  { vendorId: 'v-002', vendorName: 'Havells India', lastMessage: 'We can meet the delivery deadline for 3.5C cables.', lastTime: '1 hr', unread: 0, avatar: 'HI', status: 'online' },
  { vendorId: 'v-003', vendorName: 'Polycab Wires', lastMessage: 'Please find the BIS certificate attached.', lastTime: '3 hr', unread: 1, avatar: 'PW', status: 'offline' },
  { vendorId: 'v-004', vendorName: 'KEI Industries', lastMessage: 'Noted. We will revise the NRE costs.', lastTime: '1 day', unread: 0, avatar: 'KI', status: 'offline' },
  { vendorId: 'v-005', vendorName: 'RR Kabel', lastMessage: 'Quality inspection report for batch #2456.', lastTime: '2 days', unread: 0, avatar: 'RR', status: 'offline' },
];

const messagesData: Record<string, Message[]> = {
  'v-001': [
    { id: 'm1', sender: 'vendor', senderName: 'Finolex Cables', content: 'Good morning! We have updated our pricing for LT Power Cables for Q1 2026. The new rates include a 3% volume discount for orders above 10,000 meters.', timestamp: '09:15 AM', type: 'quotation' },
    { id: 'm2', sender: 'user', senderName: 'Rajesh Kumar', content: 'Thanks for the update. Can you also share pricing for 240 sq mm 3.5 Core XLPE variant?', timestamp: '09:22 AM', type: 'inquiry' },
    { id: 'm3', sender: 'vendor', senderName: 'Finolex Cables', content: 'Sure, the 240 sq mm 3.5C XLPE is ₹1,850/meter for volumes above 10,000m. This includes transit insurance.', timestamp: '09:40 AM', type: 'quotation' },
    { id: 'm4', sender: 'user', senderName: 'Rajesh Kumar', content: 'What about the lead time for 15,000 meters?', timestamp: '10:05 AM', type: 'inquiry' },
    { id: 'm5', sender: 'vendor', senderName: 'Finolex Cables', content: 'For 15,000 meters, we can do phased delivery:\n• Phase 1 (9,000m): 4 weeks from PO\n• Phase 2 (6,000m): 6 weeks from PO\n\nAll deliveries ex-works Pune factory.', timestamp: '10:20 AM', type: 'quotation' },
    { id: 'm6', sender: 'vendor', senderName: 'Finolex Cables', content: 'Updated pricing sheet attached for Q1 2026.', timestamp: '10:32 AM', type: 'quotation', attachment: 'Finolex_Q1_2026_PriceList.xlsx' },
  ],
  'v-002': [
    { id: 'h1', sender: 'user', senderName: 'Priya Sharma', content: 'Can Havells meet the delivery deadline of Feb 28 for BID-2026-002?', timestamp: 'Yesterday 3:00 PM', type: 'inquiry' },
    { id: 'h2', sender: 'vendor', senderName: 'Havells India', content: 'We can meet the delivery deadline for 3.5C cables. However, the 12C control cables might need an additional week.', timestamp: 'Yesterday 4:15 PM', type: 'general' },
  ],
};

const quickTemplates = [
  'Request updated pricing for {product}.',
  'Can you confirm delivery timeline for order #{orderId}?',
  'Please share your latest BIS/ISO certifications.',
  'We need a revised quotation including GST.',
];

export default function VendorCommunicationPage() {
  const { vendorId: paramVendorId } = useParams();
  const [activeThread, setActiveThread] = useState(paramVendorId || 'v-001');
  const [msgInput, setMsgInput] = useState('');
  const [msgType, setMsgType] = useState<MsgType>('general');
  const [messages, setMessages] = useState(messagesData);
  const [searchQ, setSearchQ] = useState('');
  const [filterType, setFilterType] = useState<MsgType | 'all'>('all');
  const [showTemplates, setShowTemplates] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [activeThread, messages]);

  const activeVendor = threads.find((t) => t.vendorId === activeThread)!;
  const activeMessages = (messages[activeThread] ?? []).filter((m) => filterType === 'all' || m.type === filterType);

  const sendMessage = () => {
    if (!msgInput.trim()) return;
    const newMsg: Message = {
      id: `m-${Date.now()}`,
      sender: 'user',
      senderName: 'You',
      content: msgInput,
      timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      type: msgType,
    };
    setMessages((p) => ({ ...p, [activeThread]: [...(p[activeThread] ?? []), newMsg] }));
    setMsgInput('');
  };

  const filteredThreads = threads.filter((t) => t.vendorName.toLowerCase().includes(searchQ.toLowerCase()));

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/vendors" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
          <ArrowLeft size={18} className="text-muted-silver" />
        </Link>
        <div>
          <h1 className="text-h1 text-ghost-white">Vendor Communications</h1>
          <p className="text-body text-muted-silver">Message threads with vendors</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-3 h-[calc(100vh-200px)] min-h-[500px]">
        {/* Thread List */}
        <Card variant="glass" className="flex flex-col overflow-hidden">
          <div className="p-2 border-b border-steel-slate/10">
            <div className="relative">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-silver" />
              <input value={searchQ} onChange={(e) => setSearchQ(e.target.value)} placeholder="Search vendors…" className="glass-input w-full rounded-lg pl-8 pr-3 py-1.5 text-xs text-ghost-white" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {filteredThreads.map((t) => (
              <button
                key={t.vendorId}
                onClick={() => setActiveThread(t.vendorId)}
                className={`w-full text-left p-2.5 flex items-start gap-2.5 border-b border-steel-slate/8 transition-colors ${activeThread === t.vendorId ? 'bg-electric-cyan/5' : 'hover:bg-steel-slate/8'}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] font-bold ${activeThread === t.vendorId ? 'bg-electric-cyan/15 text-electric-cyan' : 'bg-steel-slate/15 text-muted-silver'}`}>
                  {t.avatar}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-ghost-white">{t.vendorName}</span>
                    <span className="text-[9px] text-muted-silver">{t.lastTime}</span>
                  </div>
                  <p className="text-[10px] text-muted-silver truncate mt-0.5">{t.lastMessage}</p>
                </div>
                <div className="flex flex-col items-center gap-1 flex-shrink-0">
                  {t.unread > 0 && <span className="w-4 h-4 rounded-full bg-electric-cyan text-deep-navy text-[9px] font-bold flex items-center justify-center">{t.unread}</span>}
                  <span className={`w-1.5 h-1.5 rounded-full ${t.status === 'online' ? 'bg-neon-emerald' : 'bg-steel-slate/30'}`} />
                </div>
              </button>
            ))}
          </div>
        </Card>

        {/* Chat Area */}
        <Card variant="glass" className="flex flex-col overflow-hidden">
          {/* Chat Header */}
          <div className="p-3 border-b border-steel-slate/10 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-electric-cyan/15 flex items-center justify-center text-[10px] font-bold text-electric-cyan">
                {activeVendor.avatar}
              </div>
              <div>
                <span className="text-sm font-semibold text-ghost-white">{activeVendor.vendorName}</span>
                <div className="flex items-center gap-1.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${activeVendor.status === 'online' ? 'bg-neon-emerald' : 'bg-steel-slate/30'}`} />
                  <span className="text-[10px] text-muted-silver capitalize">{activeVendor.status}</span>
                </div>
              </div>
            </div>
            <div className="flex gap-1">
              <button className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors"><Phone size={14} className="text-muted-silver" /></button>
              <button className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors"><Mail size={14} className="text-muted-silver" /></button>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as MsgType | 'all')}
                className="bg-transparent text-[10px] text-muted-silver border border-steel-slate/15 rounded-lg px-2 py-1"
              >
                <option value="all">All Types</option>
                <option value="inquiry">Inquiry</option>
                <option value="quotation">Quotation</option>
                <option value="complaint">Complaint</option>
                <option value="general">General</option>
              </select>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {activeMessages.map((m) => {
              const tc = typeConfig[m.type];
              const TypeIcon = tc.icon;
              const isUser = m.sender === 'user';
              return (
                <motion.div
                  key={m.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[75%] rounded-xl p-2.5 ${isUser ? 'bg-electric-cyan/10 border border-electric-cyan/20' : 'bg-steel-slate/12 border border-steel-slate/15'}`}>
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-[10px] font-semibold text-ghost-white">{m.senderName}</span>
                      <TypeIcon size={9} className={tc.color} />
                      <span className="text-[9px] text-muted-silver ml-auto">{m.timestamp}</span>
                    </div>
                    <p className="text-xs text-ghost-white/90 whitespace-pre-wrap leading-relaxed">{m.content}</p>
                    {m.attachment && (
                      <div className="mt-1.5 flex items-center gap-1.5 bg-steel-slate/15 rounded-lg px-2 py-1">
                        <Paperclip size={10} className="text-muted-silver" />
                        <span className="text-[10px] text-electric-cyan">{m.attachment}</span>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          {/* Quick Templates */}
          <AnimatePresence>
            {showTemplates && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-steel-slate/10">
                <div className="p-2 flex flex-wrap gap-1">
                  {quickTemplates.map((t, i) => (
                    <button key={i} onClick={() => { setMsgInput(t); setShowTemplates(false); }} className="text-[10px] text-muted-silver bg-steel-slate/10 hover:bg-steel-slate/20 rounded-lg px-2 py-1 transition-colors">
                      {t}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input */}
          <div className="p-2.5 border-t border-steel-slate/10 flex items-end gap-2">
            <div className="flex flex-col gap-1 flex-shrink-0">
              <button onClick={() => setShowTemplates(!showTemplates)} className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors" title="Templates">
                <MessageSquare size={14} className="text-muted-silver" />
              </button>
              <button className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors" title="Attach file">
                <Paperclip size={14} className="text-muted-silver" />
              </button>
            </div>
            <div className="flex-1 flex flex-col gap-1">
              <div className="flex gap-1">
                {(Object.keys(typeConfig) as MsgType[]).map((t) => {
                  const tc = typeConfig[t];
                  return (
                    <button key={t} onClick={() => setMsgType(t)} className={`text-[9px] px-1.5 py-0.5 rounded transition-colors ${msgType === t ? `bg-steel-slate/20 ${tc.color}` : 'text-muted-silver/50'}`}>
                      {tc.label}
                    </button>
                  );
                })}
              </div>
              <textarea
                value={msgInput}
                onChange={(e) => setMsgInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                placeholder="Type a message…"
                rows={2}
                className="glass-input w-full rounded-lg px-3 py-2 text-xs text-ghost-white resize-none"
              />
            </div>
            <Button size="sm" leftIcon={<Send size={12} />} onClick={sendMessage} className="flex-shrink-0">
              Send
            </Button>
          </div>
        </Card>
      </div>
    </motion.div>
  );
}
