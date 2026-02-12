import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { Card, Badge } from '@/components/ui';

/* ─── types ─── */
interface BidDeadline {
  id: string;
  title: string;
  rfp: string;
  vendor: string;
  status: 'draft' | 'submitted' | 'deadline-near' | 'overdue';
  date: string; // YYYY-MM-DD
  value: string;
}

/* ─── data ─── */
const bidDeadlines: BidDeadline[] = [
  { id: 'BID-001', title: 'LT Power Cables 240mm', rfp: 'RFP-089', vendor: 'Finolex', status: 'submitted', date: '2026-02-03', value: '₹3.2 Cr' },
  { id: 'BID-002', title: 'HT XLPE Cable 33kV', rfp: 'RFP-091', vendor: 'Havells', status: 'deadline-near', date: '2026-02-08', value: '₹5.1 Cr' },
  { id: 'BID-003', title: 'Control Cable 12C', rfp: 'RFP-092', vendor: 'Polycab', status: 'draft', date: '2026-02-10', value: '₹1.8 Cr' },
  { id: 'BID-004', title: 'Fire Survival Cable', rfp: 'RFP-088', vendor: 'KEI', status: 'overdue', date: '2026-02-01', value: '₹2.4 Cr' },
  { id: 'BID-005', title: 'Wiring Cable 4mm', rfp: 'RFP-093', vendor: 'RR Kabel', status: 'draft', date: '2026-02-14', value: '₹0.9 Cr' },
  { id: 'BID-006', title: 'Marine Grade Cable', rfp: 'RFP-094', vendor: 'Finolex', status: 'deadline-near', date: '2026-02-09', value: '₹4.2 Cr' },
  { id: 'BID-007', title: 'Solar DC Cable', rfp: 'RFP-095', vendor: 'Polycab', status: 'submitted', date: '2026-02-12', value: '₹1.5 Cr' },
  { id: 'BID-008', title: 'Armoured Cable 3.5C', rfp: 'RFP-090', vendor: 'Havells', status: 'submitted', date: '2026-02-18', value: '₹6.8 Cr' },
  { id: 'BID-009', title: 'Instrumentation Cable', rfp: 'RFP-096', vendor: 'KEI', status: 'draft', date: '2026-02-22', value: '₹1.1 Cr' },
  { id: 'BID-010', title: 'Underground MV Cable', rfp: 'RFP-097', vendor: 'Finolex', status: 'deadline-near', date: '2026-02-25', value: '₹8.3 Cr' },
  { id: 'BID-011', title: 'Flexible Copper Cable', rfp: 'RFP-098', vendor: 'RR Kabel', status: 'draft', date: '2026-03-05', value: '₹0.7 Cr' },
  { id: 'BID-012', title: 'HT Cable 66kV', rfp: 'RFP-099', vendor: 'Havells', status: 'submitted', date: '2026-03-12', value: '₹12.5 Cr' },
];

const statusColors: Record<string, { dot: string; bg: string; label: string }> = {
  draft: { dot: 'bg-muted-silver', bg: 'bg-steel-slate/20', label: 'Draft' },
  submitted: { dot: 'bg-electric-cyan', bg: 'bg-electric-cyan/10', label: 'Submitted' },
  'deadline-near': { dot: 'bg-amber-glow', bg: 'bg-amber-glow/10', label: 'Deadline Near' },
  overdue: { dot: 'bg-coral-flame', bg: 'bg-coral-flame/10', label: 'Overdue' },
};

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function BidCalendarPage() {
  const [year, setYear] = useState(2026);
  const [month, setMonth] = useState(1); // 0-indexed
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = '2026-02-07';

  const dateStr = (d: number) => `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;

  const bidsMap = useMemo(() => {
    const m: Record<string, BidDeadline[]> = {};
    bidDeadlines.forEach((b) => { (m[b.date] ??= []).push(b); });
    return m;
  }, []);

  const prevMonth = () => { if (month === 0) { setMonth(11); setYear(year - 1); } else setMonth(month - 1); };
  const nextMonth = () => { if (month === 11) { setMonth(0); setYear(year + 1); } else setMonth(month + 1); };

  const selectedBids = selectedDate ? (bidsMap[selectedDate] ?? []) : [];
  const cells: (number | null)[] = [...Array(firstDay).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => i + 1)];
  while (cells.length % 7 !== 0) cells.push(null);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/bids" className="p-2 rounded-lg hover:bg-steel-slate/15 transition-colors">
            <ArrowLeft size={18} className="text-muted-silver" />
          </Link>
          <div>
            <h1 className="text-h1 text-ghost-white">Bid Calendar</h1>
            <p className="text-body text-muted-silver">Track bid deadlines & submissions</p>
          </div>
        </div>
        <div className="flex gap-2">
          {Object.entries(statusColors).map(([k, v]) => (
            <div key={k} className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${v.dot}`} />
              <span className="text-[10px] text-muted-silver">{v.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        {/* Calendar */}
        <Card variant="glass" className="p-4">
          {/* Month Nav */}
          <div className="flex items-center justify-between mb-4">
            <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors">
              <ChevronLeft size={16} className="text-muted-silver" />
            </button>
            <h2 className="text-sm font-semibold text-ghost-white">{MONTHS[month]} {year}</h2>
            <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-steel-slate/15 transition-colors">
              <ChevronRight size={16} className="text-muted-silver" />
            </button>
          </div>

          {/* Day Headers */}
          <div className="grid grid-cols-7 gap-1 mb-1">
            {DAYS.map((d) => (
              <div key={d} className="text-center text-[10px] font-medium text-muted-silver py-1">{d}</div>
            ))}
          </div>

          {/* Grid */}
          <div className="grid grid-cols-7 gap-1">
            {cells.map((day, i) => {
              if (day === null) return <div key={`e-${i}`} />;
              const ds = dateStr(day);
              const bids = bidsMap[ds] ?? [];
              const isToday = ds === today;
              const isSelected = ds === selectedDate;

              return (
                <motion.button
                  key={ds}
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => setSelectedDate(isSelected ? null : ds)}
                  className={`relative p-1.5 rounded-lg min-h-[64px] text-left transition-colors border
                    ${isSelected ? 'border-electric-cyan/40 bg-electric-cyan/8' : 'border-transparent hover:bg-steel-slate/10'}
                    ${isToday ? 'ring-1 ring-electric-cyan/30' : ''}
                  `}
                >
                  <span className={`text-[10px] font-medium ${isToday ? 'text-electric-cyan' : 'text-muted-silver'}`}>{day}</span>
                  {bids.length > 0 && (
                    <div className="mt-0.5 space-y-0.5">
                      {bids.slice(0, 2).map((b) => (
                        <div key={b.id} className={`${statusColors[b.status]?.bg ?? ''} rounded px-1 py-0.5 truncate`}>
                          <span className="text-[8px] text-ghost-white/80 leading-none">{b.id.split('-')[1]}</span>
                        </div>
                      ))}
                      {bids.length > 2 && (
                        <span className="text-[8px] text-muted-silver">+{bids.length - 2} more</span>
                      )}
                    </div>
                  )}
                </motion.button>
              );
            })}
          </div>
        </Card>

        {/* Right Panel — Date Detail */}
        <div className="space-y-3">
          <Card variant="glass" className="p-3">
            <div className="flex items-center gap-2 mb-3">
              <CalendarDays size={14} className="text-electric-cyan" />
              <h3 className="text-xs font-semibold text-ghost-white">
                {selectedDate
                  ? new Date(selectedDate + 'T00:00').toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
                  : 'Select a date'}
              </h3>
            </div>

            {selectedBids.length === 0 && (
              <p className="text-xs text-muted-silver py-4 text-center">{selectedDate ? 'No bids due on this date' : 'Click a calendar date to view bids'}</p>
            )}

            <div className="space-y-2">
              {selectedBids.map((b) => {
                const sc = statusColors[b.status];
                return (
                  <motion.div key={b.id} initial={{ opacity: 0, x: 6 }} animate={{ opacity: 1, x: 0 }} className={`p-2.5 rounded-lg border border-steel-slate/15 ${sc?.bg ?? ''}`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono font-semibold text-ghost-white">{b.id}</span>
                      <Badge variant={b.status === 'overdue' ? 'danger' : b.status === 'deadline-near' ? 'warning' : b.status === 'submitted' ? 'info' : 'default'} size="sm">
                        {sc?.label}
                      </Badge>
                    </div>
                    <p className="text-xs text-ghost-white/90 mb-0.5">{b.title}</p>
                    <div className="flex items-center gap-3 text-[10px] text-muted-silver">
                      <span className="flex items-center gap-0.5"><FileText size={9} /> {b.rfp}</span>
                      <span>{b.vendor}</span>
                      <span className="ml-auto font-semibold text-ghost-white">{b.value}</span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </Card>

          {/* Upcoming */}
          <Card variant="glass" className="p-3">
            <h3 className="text-xs font-semibold text-ghost-white mb-2 flex items-center gap-1.5"><Clock size={12} /> Upcoming Deadlines</h3>
            <div className="space-y-1.5">
              {bidDeadlines
                .filter((b) => b.date >= today)
                .sort((a, b) => a.date.localeCompare(b.date))
                .slice(0, 5)
                .map((b) => {
                  const daysLeft = Math.ceil((new Date(b.date).getTime() - new Date(today).getTime()) / 86400000);
                  return (
                    <div key={b.id} className="flex items-center gap-2 text-xs">
                      <span className={`w-1.5 h-1.5 rounded-full ${statusColors[b.status]?.dot ?? ''}`} />
                      <span className="text-ghost-white flex-1 truncate">{b.id}</span>
                      <span className={`font-mono text-[10px] ${daysLeft <= 3 ? 'text-coral-flame' : daysLeft <= 7 ? 'text-amber-glow' : 'text-neon-emerald'}`}>
                        {daysLeft}d
                      </span>
                    </div>
                  );
                })}
            </div>
          </Card>

          {/* Overdue */}
          {bidDeadlines.some((b) => b.status === 'overdue') && (
            <Card variant="glass" className="p-3 border-coral-flame/20">
              <h3 className="text-xs font-semibold text-coral-flame mb-2 flex items-center gap-1.5">
                <AlertTriangle size={12} /> Overdue Bids
              </h3>
              {bidDeadlines
                .filter((b) => b.status === 'overdue')
                .map((b) => (
                  <div key={b.id} className="flex items-center gap-2 text-xs py-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-coral-flame" />
                    <span className="text-ghost-white">{b.id}</span>
                    <span className="text-muted-silver truncate flex-1">{b.title}</span>
                    <span className="text-coral-flame font-mono text-[10px]">{b.date.split('-').reverse().join('/')}</span>
                  </div>
                ))}
            </Card>
          )}
        </div>
      </div>
    </motion.div>
  );
}
