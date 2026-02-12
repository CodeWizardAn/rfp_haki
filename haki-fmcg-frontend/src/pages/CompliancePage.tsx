import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Search,
  Download,
  Eye,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

interface ComplianceRule {
  id: string;
  standard: string;
  category: string;
  description: string;
  status: 'passed' | 'failed' | 'warning' | 'pending';
  lastChecked: string;
  details: string;
  risk: 'high' | 'medium' | 'low';
}

const mockRules: ComplianceRule[] = [
  { id: 'CR-001', standard: 'IS 7098 Part 1', category: 'Cable Standards', description: 'XLPE insulated cables for rated voltages from 3.3kV up to 33kV', status: 'passed', lastChecked: '2026-02-06', details: 'All HT cable products comply with IS 7098 specifications for XLPE insulation thickness and conductor requirements.', risk: 'low' },
  { id: 'CR-002', standard: 'IS 1554 Part 1', category: 'Cable Standards', description: 'PVC insulated cables for voltages up to 1100V', status: 'passed', lastChecked: '2026-02-06', details: 'LT PVC cable products from all vendors verified against IS 1554 requirements.', risk: 'low' },
  { id: 'CR-003', standard: 'IEC 60502', category: 'International Standards', description: 'Power cables with extruded insulation for rated voltages from 1kV to 30kV', status: 'passed', lastChecked: '2026-02-05', details: 'International compliance verified for export-grade cables.', risk: 'low' },
  { id: 'CR-004', standard: 'IS 694', category: 'Wire Standards', description: 'PVC insulated cables for working voltages up to 1100V', status: 'warning', lastChecked: '2026-02-06', details: 'Two products from Finolex missing updated BIS certification renewal (due Feb 28, 2026).', risk: 'medium' },
  { id: 'CR-005', standard: 'BIS Certification', category: 'Certification', description: 'Bureau of Indian Standards product certification validity', status: 'warning', lastChecked: '2026-02-04', details: '3 products have BIS certificates expiring within 30 days. Renewal required before bid submission.', risk: 'medium' },
  { id: 'CR-006', standard: 'IS 3961', category: 'Testing Standards', description: 'Recommended current ratings for cables', status: 'passed', lastChecked: '2026-02-06', details: 'Current derating calculations verified against IS 3961 tables for all cable sizes.', risk: 'low' },
  { id: 'CR-007', standard: 'CPRI Approved', category: 'Testing Authority', description: 'Central Power Research Institute test approval', status: 'failed', lastChecked: '2026-02-03', details: 'KEI 11kV cable CPRI type test report expired Dec 2025. Cannot include in government tenders until renewed.', risk: 'high' },
  { id: 'CR-008', standard: 'GST Compliance', category: 'Tax & Finance', description: 'GST registration and filing verification for all vendors', status: 'passed', lastChecked: '2026-02-01', details: 'All active vendors have valid GST registrations with up-to-date filing status verified.', risk: 'low' },
];

const statusConfig = {
  passed: { icon: <CheckCircle2 size={16} />, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10', badge: 'emerald' },
  failed: { icon: <XCircle size={16} />, color: 'text-coral-flame', bg: 'bg-coral-flame/10', badge: 'coral' },
  warning: { icon: <AlertTriangle size={16} />, color: 'text-amber-glow', bg: 'bg-amber-glow/10', badge: 'amber' },
  pending: { icon: <Clock size={16} />, color: 'text-muted-silver', bg: 'bg-steel-slate/10', badge: 'default' },
};

const riskColors = { high: 'coral', medium: 'amber', low: 'emerald' };

export default function CompliancePage() {
  const [expandedRule, setExpandedRule] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const passed = mockRules.filter((r) => r.status === 'passed').length;
  const warnings = mockRules.filter((r) => r.status === 'warning').length;
  const failed = mockRules.filter((r) => r.status === 'failed').length;
  const overallScore = Math.round((passed / mockRules.length) * 100);

  const filteredRules = mockRules.filter((r) => {
    if (filterStatus !== 'all' && r.status !== filterStatus) return false;
    if (searchQuery && !r.standard.toLowerCase().includes(searchQuery.toLowerCase()) && !r.description.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-neon-emerald/10">
            <ShieldCheck size={24} className="text-neon-emerald" />
          </div>
          <div>
            <h1 className="text-h1 text-ghost-white">Compliance Dashboard</h1>
            <p className="text-body text-muted-silver">IS/IEC standards & certification monitoring</p>
          </div>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button variant="secondary" leftIcon={<Download size={14} />}>Export Report</Button>
          <Button variant="primary" leftIcon={<RefreshCw size={14} />}>Run Full Check</Button>
        </div>
      </div>

      {/* Score + Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Overall Score */}
        <Card variant="glass" className="md:row-span-1 flex flex-col items-center justify-center">
          <div className="relative w-24 h-24">
            <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#1E2642" strokeWidth="8" />
              <circle
                cx="50" cy="50" r="42" fill="none"
                stroke={overallScore >= 80 ? '#00E68A' : overallScore >= 60 ? '#FFB224' : '#FF4757'}
                strokeWidth="8"
                strokeDasharray={`${overallScore * 2.64} 264`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-ghost-white">{overallScore}%</span>
              <span className="text-[10px] text-muted-silver">Score</span>
            </div>
          </div>
          <p className="text-xs text-muted-silver mt-2">Overall Compliance</p>
        </Card>

        {[
          { label: 'Passed', value: passed, icon: <CheckCircle2 size={16} />, color: 'text-neon-emerald', bg: 'bg-neon-emerald/10' },
          { label: 'Warnings', value: warnings, icon: <AlertTriangle size={16} />, color: 'text-amber-glow', bg: 'bg-amber-glow/10' },
          { label: 'Failed', value: failed, icon: <XCircle size={16} />, color: 'text-coral-flame', bg: 'bg-coral-flame/10' },
        ].map((stat) => (
          <Card key={stat.label} variant="glass">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${stat.bg}`}>
                <span className={stat.color}>{stat.icon}</span>
              </div>
              <div>
                <p className="text-2xl font-bold text-ghost-white">{stat.value}</p>
                <p className="text-xs text-muted-silver">{stat.label}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Search + Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search standards, descriptions…"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-steel-slate/15 border border-steel-slate/30 text-ghost-white text-sm placeholder:text-muted-silver/40 focus:outline-none focus:border-electric-cyan/50"
          />
        </div>
        <div className="flex gap-1 rounded-xl bg-steel-slate/15 p-1">
          {[
            { id: 'all', label: 'All' },
            { id: 'passed', label: 'Passed' },
            { id: 'warning', label: 'Warnings' },
            { id: 'failed', label: 'Failed' },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilterStatus(f.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterStatus === f.id ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Rules List */}
      <div className="space-y-3">
        {filteredRules.map((rule) => {
          const config = statusConfig[rule.status];
          const isExpanded = expandedRule === rule.id;
          return (
            <Card key={rule.id} variant="glass" className="transition-all">
              <div
                className="flex items-center gap-4 cursor-pointer"
                onClick={() => setExpandedRule(isExpanded ? null : rule.id)}
              >
                <div className={`p-2 rounded-lg ${config.bg} flex-shrink-0`}>
                  <span className={config.color}>{config.icon}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-ghost-white">{rule.standard}</span>
                    <Badge variant="soft" color={config.badge as any} size="sm">{rule.status}</Badge>
                    <Badge variant="outline" color={riskColors[rule.risk] as any} size="sm">{rule.risk} risk</Badge>
                  </div>
                  <p className="text-xs text-muted-silver mt-0.5 truncate">{rule.description}</p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-xs text-muted-silver hidden sm:block">{rule.category}</span>
                  <span className="text-xs text-muted-silver hidden sm:block">{rule.lastChecked}</span>
                  {isExpanded ? <ChevronUp size={14} className="text-muted-silver" /> : <ChevronDown size={14} className="text-muted-silver" />}
                </div>
              </div>
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-4 pt-4 border-t border-steel-slate/20 space-y-3">
                      <p className="text-sm text-muted-silver">{rule.details}</p>
                      <div className="flex gap-2">
                        <Button variant="secondary" size="xs" leftIcon={<Eye size={10} />}>View Standard</Button>
                        <Button variant="secondary" size="xs" leftIcon={<RefreshCw size={10} />}>Re-check</Button>
                        <Button variant="secondary" size="xs" leftIcon={<FileText size={10} />}>View Report</Button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          );
        })}
      </div>
    </motion.div>
  );
}
