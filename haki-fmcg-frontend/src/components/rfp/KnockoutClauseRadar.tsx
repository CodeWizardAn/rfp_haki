import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  ChevronDown,
  ChevronUp,
  Info,
  ExternalLink,
  Filter,
} from 'lucide-react';
import { Card, Button } from '@/components/ui';
import { ClauseBadge, ClauseTraceabilityModal, type ClauseCitation } from './ClauseTraceabilityModal';

export type GatekeeperStatus = 'PASS' | 'ACTION_REQUIRED' | 'KNOCKOUT_RISK';

export interface GatekeeperItem {
  id: string;
  category: 'Commercial' | 'Statutory' | 'Technical' | 'Financial';
  title: string;
  shortDesc: string;
  status: GatekeeperStatus;
  statusLabel: string;
  tenderClauseText: string;
  page: number;
  clauseRef: string;
  disqualificationRisk: string;
  actionRequired: string;
  vendorState: string;
}

const DEFAULT_GATEKEEPERS: GatekeeperItem[] = [
  {
    id: 'turnover',
    category: 'Financial',
    title: 'Average Annual Turnover & Net Worth Threshold',
    shortDesc: 'Minimum ₹15.0 Cr turnover over last 3 audited FYs with positive net worth.',
    status: 'PASS',
    statusLabel: 'Verified (3.2x Safety Margin)',
    tenderClauseText: 'The Bidder must have achieved an Average Annual Financial Turnover of not less than INR 15.00 Crores during the immediate preceding three consecutive financial years (FY 2022-23, 2023-24, 2024-25). Net worth must be positive as on 31st March 2025.',
    page: 8,
    clauseRef: 'Section III • Cl 3.1.2',
    disqualificationRisk: 'Failure to submit CA-certified turnover certificate with valid UDIN leads to non-responsive technical disqualification.',
    actionRequired: 'Attach Annexure-II (Audited Balance Sheets with UDIN) to Section-A Envelope.',
    vendorState: 'Vendor 3-year average turnover: ₹48.50 Cr. Net Worth: ₹14.20 Cr (Positive). Meets criteria.',
  },
  {
    id: 'emd_waiver',
    category: 'Statutory',
    title: 'EMD Submission / MSME Exemption Waiver',
    shortDesc: '₹3,50,000 EMD or valid Udyam MSME certificate for wire & cable manufacture.',
    status: 'PASS',
    statusLabel: 'MSME Exemption Eligible',
    tenderClauseText: 'Earnest Money Deposit (EMD) of INR 3,50,000/- must be submitted via BG from a scheduled commercial bank. Micro and Small Enterprises (MSEs) registered with Udyam for relevant manufacturing activity are exempted from EMD payment as per Rule 170 of GFR 2017.',
    page: 14,
    clauseRef: 'Section I • Cl 4.8.1',
    disqualificationRisk: 'Bids without valid EMD BG or matching MSME NIC code are summarily rejected at opening.',
    actionRequired: 'Attach Udyam Registration Certificate with NIC Code 27320 (Manufacture of other electronic and electric wires and cables).',
    vendorState: 'Valid Udyam Registration verified. Claiming 100% EMD waiver of ₹3,50,000.',
  },
  {
    id: 'type_test_cpri',
    category: 'Technical',
    title: 'CPRI / ERDA Type Test Validity (< 5 Years)',
    shortDesc: 'Type test reports from NABL accredited lab dated within 5 years of bid due date.',
    status: 'PASS',
    statusLabel: 'CPRI Test Valid through 2027',
    tenderClauseText: 'The offered wire and cable models must possess full type test certificates conducted at CPRI / ERDA or any ILAC/NABL accredited test house within 5 (five) years prior to the date of bid opening. Routine and acceptance tests will not substitute type tests.',
    page: 29,
    clauseRef: 'Technical Specs • Cl 6.4.3',
    disqualificationRisk: 'Reports older than 5 years or from non-accredited laboratories cause instant technical rejection.',
    actionRequired: 'Verify CPRI Type Test Report #CPRI/BLR/2023/C-4819 covers offered 11kV 3Cx240 and LT 4Cx16 cable specs.',
    vendorState: 'CPRI Bengaluru Type Test Certificate dated October 2023 covers quoted Polycab/Havells cable lines.',
  },
  {
    id: 'make_in_india',
    category: 'Statutory',
    title: 'Class-1 Local Supplier (PPP-MII > 50%)',
    shortDesc: 'Public Procurement (Preference to Make in India) minimum 50% domestic content.',
    status: 'PASS',
    statusLabel: '78.4% Domestic Content Verified',
    tenderClauseText: 'Only "Class-I Local Supplier" with local content equal to or more than 50% as defined under DPIIT Order No. P-45021/2/2017-PP (BE-II) shall be eligible to participate. Bidder must submit a self-declaration indicating percentage of local content and details of local manufacturing locations.',
    page: 41,
    clauseRef: 'Special Conditions • Cl 9.2.1',
    disqualificationRisk: 'Failure to provide Class-1 declaration disallows participation in tenders reserved for domestic manufacturers.',
    actionRequired: 'Submit Form-MII with location of Indian manufacturing facility (Halol / Alwar plant).',
    vendorState: 'Quoted cable assemblies manufactured domestically in Gujarat & Rajasthan plants (78.4% local value add).',
  },
  {
    id: 'blacklisting_affidavit',
    category: 'Commercial',
    title: 'Non-Blacklisting Notarized Affidavit on Stamp Paper',
    shortDesc: 'Submission of ₹100 non-judicial stamp paper affidavit executed within 30 days.',
    status: 'ACTION_REQUIRED',
    statusLabel: 'Affidavit Needed Prior to Submission',
    tenderClauseText: 'The Bidder must provide a notarized affidavit on non-judicial stamp paper of INR 100/- declaring that the firm has not been blacklisted, debarred, or banned by any Central/State Government Ministry, PSU, or autonomous body during the last 3 years.',
    page: 53,
    clauseRef: 'General Terms • Cl 11.5',
    disqualificationRisk: 'Missing notarization or executing on plain letterhead leads to technical rejection during preliminary scrutiny.',
    actionRequired: 'Download Saarthi auto-filled Annexure-IV, execute on ₹100 stamp paper before a First Class Magistrate or Notary, and upload scan.',
    vendorState: 'Action Required: Legal team must notarize Annexure-IV prior to tender closing.',
  },
  {
    id: 'delivery_lead_time',
    category: 'Commercial',
    title: 'Delivery Schedule & Liquidated Damages (LD Cap)',
    shortDesc: 'Phased supply within 8 weeks; LD rate 0.5% per week subject to 10% ceiling.',
    status: 'PASS',
    statusLabel: 'Feasible (4.5 Wk OEM Lead Time)',
    tenderClauseText: 'Complete quantity must be delivered at consignee site within 8 (eight) weeks from date of LOA. Liquidated damages shall be levied @ 0.5% of contract value per week of delay or part thereof, up to a maximum deduction of 10% of total order value.',
    page: 67,
    clauseRef: 'Commercial Terms • Cl 14.1',
    disqualificationRisk: 'Rejecting delivery schedule or requesting exceptions to the 10% LD clause results in rejection as non-conforming bid.',
    actionRequired: 'Confirm production slot with OEM distributor to guarantee dispatch within 4.5 weeks.',
    vendorState: 'Distributor confirmed factory dispatch in 4.5 weeks. Delivery timeline feasible with 3.5-week safety buffer.',
  },
];

interface KnockoutClauseRadarProps {
  customItems?: GatekeeperItem[];
  tenderName?: string;
  onGenerateAffidavit?: () => void;
}

export function KnockoutClauseRadar({
  customItems,
  tenderName = 'Tender Specification',
  onGenerateAffidavit,
}: KnockoutClauseRadarProps) {
  const [items] = useState<GatekeeperItem[]>(customItems || DEFAULT_GATEKEEPERS);
  const [filter, setFilter] = useState<'ALL' | 'RISKS' | 'ACTIONS' | 'CLEARED'>('ALL');
  const [expandedId, setExpandedId] = useState<string | null>('blacklisting_affidavit');
  const [selectedCitation, setSelectedCitation] = useState<ClauseCitation | null>(null);

  const passedCount = items.filter((i) => i.status === 'PASS').length;
  const actionCount = items.filter((i) => i.status === 'ACTION_REQUIRED').length;
  const riskCount = items.filter((i) => i.status === 'KNOCKOUT_RISK').length;

  const overallDecision: 'GO' | 'CAUTION' | 'NO_GO' =
    riskCount > 0 ? 'NO_GO' : actionCount > 0 ? 'CAUTION' : 'GO';

  const filteredItems = items.filter((item) => {
    if (filter === 'RISKS') return item.status === 'KNOCKOUT_RISK';
    if (filter === 'ACTIONS') return item.status === 'ACTION_REQUIRED';
    if (filter === 'CLEARED') return item.status === 'PASS';
    return true;
  });

  return (
    <Card variant="glass" className="overflow-hidden border-steel-slate/30">
      {/* ── Top Header Banner ── */}
      <div className="p-5 border-b border-steel-slate/20 bg-gradient-to-r from-steel-slate/20 via-steel-slate/10 to-transparent">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div
              className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 shadow-lg ${
                overallDecision === 'GO'
                  ? 'bg-neon-emerald/20 text-neon-emerald border border-neon-emerald/40'
                  : overallDecision === 'CAUTION'
                    ? 'bg-amber-glow/20 text-amber-glow border border-amber-glow/40'
                    : 'bg-coral-flame/20 text-coral-flame border border-coral-flame/40'
              }`}
            >
              {overallDecision === 'GO' ? (
                <ShieldCheck size={24} />
              ) : overallDecision === 'CAUTION' ? (
                <AlertTriangle size={24} />
              ) : (
                <ShieldAlert size={24} />
              )}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-base sm:text-lg font-bold text-ghost-white tracking-tight">
                  Knockout Clause &amp; Buried Disqualifiers Radar
                </h3>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold uppercase tracking-wider ${
                    overallDecision === 'GO'
                      ? 'bg-neon-emerald/15 text-neon-emerald border border-neon-emerald/40'
                      : overallDecision === 'CAUTION'
                        ? 'bg-amber-glow/15 text-amber-glow border border-amber-glow/40'
                        : 'bg-coral-flame/15 text-coral-flame border border-coral-flame/40'
                  }`}
                >
                  {overallDecision === 'GO'
                    ? 'GO: All Gatekeepers Cleared'
                    : overallDecision === 'CAUTION'
                      ? 'CAUTION: Action Required to Qualify'
                      : 'NO-GO: Disqualification Risk Detected'}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-muted-silver mt-1 leading-relaxed">
                Autonomous scan of commercial, statutory, and pre-qualification traps buried across pages 1 to 90+.
                Prevents sudden disqualification before engineering effort is committed.
              </p>
            </div>
          </div>

          {/* Quick Score Metrics */}
          <div className="flex items-center gap-2 self-start md:self-auto flex-shrink-0">
            <div className="px-3 py-2 rounded-lg bg-steel-slate/20 border border-steel-slate/30 text-center">
              <span className="text-[10px] text-muted-silver uppercase block font-semibold">Passed</span>
              <span className="text-sm font-bold text-neon-emerald">{passedCount} / {items.length}</span>
            </div>
            <div className="px-3 py-2 rounded-lg bg-steel-slate/20 border border-steel-slate/30 text-center">
              <span className="text-[10px] text-muted-silver uppercase block font-semibold">Actions</span>
              <span className="text-sm font-bold text-amber-glow">{actionCount}</span>
            </div>
            <div className="px-3 py-2 rounded-lg bg-steel-slate/20 border border-steel-slate/30 text-center">
              <span className="text-[10px] text-muted-silver uppercase block font-semibold">Risks</span>
              <span className={`text-sm font-bold ${riskCount > 0 ? 'text-coral-flame' : 'text-slate-400'}`}>
                {riskCount}
              </span>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 mt-4 pt-3 border-t border-steel-slate/15">
          <span className="text-xs font-semibold text-muted-silver mr-2 flex items-center gap-1">
            <Filter size={12} /> Filter:
          </span>
          <button
            onClick={() => setFilter('ALL')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
              filter === 'ALL'
                ? 'bg-electric-cyan/20 text-electric-cyan border border-electric-cyan/40'
                : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/20'
            }`}
          >
            All Gatekeepers ({items.length})
          </button>
          <button
            onClick={() => setFilter('RISKS')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
              filter === 'RISKS'
                ? 'bg-coral-flame/20 text-coral-flame border border-coral-flame/40'
                : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/20'
            }`}
          >
            Knockout Risks ({riskCount})
          </button>
          <button
            onClick={() => setFilter('ACTIONS')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
              filter === 'ACTIONS'
                ? 'bg-amber-glow/20 text-amber-glow border border-amber-glow/40'
                : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/20'
            }`}
          >
            Action Required ({actionCount})
          </button>
          <button
            onClick={() => setFilter('CLEARED')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
              filter === 'CLEARED'
                ? 'bg-neon-emerald/20 text-neon-emerald border border-neon-emerald/40'
                : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/20'
            }`}
          >
            Cleared ({passedCount})
          </button>
        </div>
      </div>

      {/* ── Gatekeeper Accordion Items ── */}
      <div className="divide-y divide-steel-slate/15 p-2 sm:p-4 space-y-2">
        {filteredItems.map((item) => {
          const isExpanded = expandedId === item.id;
          const statusBg =
            item.status === 'PASS'
              ? 'bg-neon-emerald/10 border-neon-emerald/30 text-neon-emerald'
              : item.status === 'ACTION_REQUIRED'
                ? 'bg-amber-glow/10 border-amber-glow/30 text-amber-glow'
                : 'bg-coral-flame/10 border-coral-flame/30 text-coral-flame';

          return (
            <div
              key={item.id}
              className={`rounded-xl border transition-all ${
                isExpanded
                  ? 'bg-steel-slate/20 border-steel-slate/40'
                  : 'bg-steel-slate/10 border-steel-slate/20 hover:bg-steel-slate/15'
              }`}
            >
              {/* Item Header */}
              <div
                onClick={() => setExpandedId(isExpanded ? null : item.id)}
                className="p-3.5 sm:p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 cursor-pointer select-none"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex-shrink-0">
                    {item.status === 'PASS' ? (
                      <CheckCircle2 size={18} className="text-neon-emerald" />
                    ) : item.status === 'ACTION_REQUIRED' ? (
                      <AlertTriangle size={18} className="text-amber-glow" />
                    ) : (
                      <XCircle size={18} className="text-coral-flame" />
                    )}
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-bold text-electric-cyan bg-electric-cyan/10 px-2 py-0.5 rounded">
                        {item.category}
                      </span>
                      <h4 className="text-sm font-semibold text-ghost-white">{item.title}</h4>
                    </div>
                    <p className="text-xs text-muted-silver mt-1">{item.shortDesc}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2.5 self-end sm:self-auto flex-shrink-0">
                  <ClauseBadge
                    page={item.page}
                    clause={item.clauseRef}
                    excerpt={item.tenderClauseText}
                    documentName={tenderName}
                  />

                  <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold border ${statusBg}`}>
                    {item.statusLabel}
                  </span>

                  <button className="text-muted-silver hover:text-ghost-white">
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                </div>
              </div>

              {/* Expanded Detailed Breakdown */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4 pt-1 space-y-3 text-xs border-t border-steel-slate/20">
                      {/* Verbatim Tender Clause Excerpt */}
                      <div className="bg-midnight-void/60 rounded-lg p-3 border border-steel-slate/30">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-semibold text-muted-silver uppercase text-[10px] tracking-wider flex items-center gap-1">
                            <FileText size={12} className="text-electric-cyan" />
                            Verbatim Tender Clause ({item.clauseRef} • Page {item.page})
                          </span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedCitation({
                                page: item.page,
                                clause: item.clauseRef,
                                excerpt: item.tenderClauseText,
                                documentName: tenderName,
                              });
                            }}
                            className="text-[11px] text-electric-cyan hover:underline flex items-center gap-1"
                          >
                            Trace in Document <ExternalLink size={11} />
                          </button>
                        </div>
                        <p className="font-mono text-slate-300 leading-relaxed italic border-l-2 border-electric-cyan/60 pl-2.5">
                          &ldquo;{item.tenderClauseText}&rdquo;
                        </p>
                      </div>

                      {/* Two Column Analysis: Disqualification Trap vs Recommended Action */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        <div className="p-3 rounded-lg bg-coral-flame/10 border border-coral-flame/20 space-y-1">
                          <span className="font-bold text-coral-flame uppercase text-[10px] tracking-wider block">
                            ⚠️ Disqualification Pitfall
                          </span>
                          <p className="text-slate-300 leading-relaxed">{item.disqualificationRisk}</p>
                        </div>

                        <div className="p-3 rounded-lg bg-neon-emerald/10 border border-neon-emerald/20 space-y-1">
                          <span className="font-bold text-neon-emerald uppercase text-[10px] tracking-wider block">
                            ✓ Recommended Compliance Action
                          </span>
                          <p className="text-slate-300 leading-relaxed">{item.actionRequired}</p>
                        </div>
                      </div>

                      {/* Current Vendor Position */}
                      <div className="flex items-center justify-between p-2.5 rounded-lg bg-steel-slate/15 border border-steel-slate/25">
                        <div className="flex items-center gap-2">
                          <Info size={14} className="text-electric-cyan flex-shrink-0" />
                          <span className="text-ghost-white font-medium">
                            <strong className="text-muted-silver">Current Status:</strong> {item.vendorState}
                          </span>
                        </div>

                        {item.status === 'ACTION_REQUIRED' && onGenerateAffidavit && (
                          <Button variant="primary" size="sm" onClick={onGenerateAffidavit}>
                            Auto-Draft Affidavit
                          </Button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* Traceability Modal when clicking Trace button */}
      <ClauseTraceabilityModal
        citation={selectedCitation}
        isOpen={Boolean(selectedCitation)}
        onClose={() => setSelectedCitation(null)}
      />
    </Card>
  );
}
export default KnockoutClauseRadar;
