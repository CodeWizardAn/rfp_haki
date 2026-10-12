import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  ChevronDown,
  ChevronUp,
  Info,
  ExternalLink,
  ArrowRight,
} from 'lucide-react';
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
    status: 'PASS',
    statusLabel: 'Affidavit Verified & Executed',
    tenderClauseText: 'The Bidder must provide a notarized affidavit on non-judicial stamp paper of INR 100/- declaring that the firm has not been blacklisted, debarred, or banned by any Central/State Government Ministry, PSU, or autonomous body during the last 3 years.',
    page: 53,
    clauseRef: 'General Terms • Cl 11.5',
    disqualificationRisk: 'Missing notarization or executing on plain letterhead leads to technical rejection during preliminary scrutiny.',
    actionRequired: 'Attach notarized Annexure-IV executed on ₹100 stamp paper to technical envelope.',
    vendorState: 'Notarized non-blacklisting affidavit on ₹100 stamp paper verified and attached to bid envelope.',
  },
  {
    id: 'delivery_lead_time',
    category: 'Commercial',
    title: 'Delivery Schedule & Liquidated Damages (LD Cap)',
    shortDesc: 'Phased supply within 8 weeks; LD rate 0.5% per week subject to 10% ceiling.',
    status: 'PASS',
    statusLabel: 'Feasible (4.5 Wk Lead Time)',
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
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<ClauseCitation | null>(null);

  const passedCount = items.filter((i) => i.status === 'PASS').length;
  const actionCount = items.filter((i) => i.status === 'ACTION_REQUIRED').length;
  const riskCount = items.filter((i) => i.status === 'KNOCKOUT_RISK').length;

  const filteredItems = items.filter((item) => {
    if (filter === 'RISKS') return item.status === 'KNOCKOUT_RISK';
    if (filter === 'ACTIONS') return item.status === 'ACTION_REQUIRED';
    if (filter === 'CLEARED') return item.status === 'PASS';
    return true;
  });

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-[0_2px_16px_rgba(0,0,0,0.04)] overflow-hidden font-sans">
      {/* ── Top Header Banner ── */}
      <div className="p-5 sm:p-6 bg-gradient-to-r from-slate-50/90 via-white to-slate-50/50 border-b border-slate-100">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
              Knockout Clause &amp; Buried Disqualifiers Radar
            </h3>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 leading-relaxed max-w-2xl">
              Scans commercial, statutory, and pre-qualification traps buried across pages 1 to 90+.
              Prevents sudden disqualification before engineering effort is committed.
            </p>
          </div>

          {/* Quick Score Metrics */}
          <div className="flex items-center gap-2 self-start md:self-auto flex-shrink-0">
            <div className="px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200/80 text-center min-w-[70px]">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Passed</span>
              <span className="text-sm font-extrabold text-emerald-600">{passedCount} / {items.length}</span>
            </div>
            <div className="px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200/80 text-center min-w-[70px]">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Actions</span>
              <span className={`text-sm font-extrabold ${actionCount > 0 ? 'text-amber-600' : 'text-slate-400'}`}>{actionCount}</span>
            </div>
            <div className="px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200/80 text-center min-w-[70px]">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Risks</span>
              <span className={`text-sm font-extrabold ${riskCount > 0 ? 'text-rose-600' : 'text-slate-400'}`}>
                {riskCount}
              </span>
            </div>
          </div>
        </div>

        {/* Filter Navigation */}
        <div className="flex flex-wrap items-center gap-1.5 mt-5 pt-3 border-t border-slate-100">
          <div className="bg-slate-100/80 p-1 rounded-xl inline-flex gap-1 border border-slate-200/60">
            <button
              onClick={() => setFilter('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filter === 'ALL'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              All Gatekeepers ({items.length})
            </button>
            <button
              onClick={() => setFilter('RISKS')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filter === 'RISKS'
                  ? 'bg-white text-rose-700 shadow-xs'
                  : 'text-slate-600 hover:text-rose-700 hover:bg-white/60'
              }`}
            >
              Knockout Risks ({riskCount})
            </button>
            <button
              onClick={() => setFilter('ACTIONS')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filter === 'ACTIONS'
                  ? 'bg-white text-amber-800 shadow-xs'
                  : 'text-slate-600 hover:text-amber-800 hover:bg-white/60'
              }`}
            >
              Action Required ({actionCount})
            </button>
            <button
              onClick={() => setFilter('CLEARED')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filter === 'CLEARED'
                  ? 'bg-white text-emerald-700 shadow-xs'
                  : 'text-slate-600 hover:text-emerald-700 hover:bg-white/60'
              }`}
            >
              Cleared ({passedCount})
            </button>
          </div>
        </div>
      </div>

      {/* ── Gatekeeper List Items ── */}
      <div className="divide-y divide-slate-100">
        {filteredItems.map((item) => {
          const isExpanded = expandedId === item.id;
          const statusPill =
            item.status === 'PASS'
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200/90'
              : item.status === 'ACTION_REQUIRED'
                ? 'bg-amber-50 text-amber-800 border-amber-200/90'
                : 'bg-rose-50 text-rose-700 border-rose-200/90';

          return (
            <div
              key={item.id}
              className={`transition-colors ${
                isExpanded ? 'bg-slate-50/50' : 'bg-white hover:bg-slate-50/40'
              }`}
            >
              {/* Item Header Row */}
              <div
                onClick={() => setExpandedId(isExpanded ? null : item.id)}
                className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer select-none"
              >
                <div className="flex items-start gap-3.5">
                  <div className="mt-0.5 flex-shrink-0">
                    {item.status === 'PASS' ? (
                      <CheckCircle2 size={18} className="text-emerald-600 stroke-[2.2]" />
                    ) : item.status === 'ACTION_REQUIRED' ? (
                      <AlertTriangle size={18} className="text-amber-500 stroke-[2.2]" />
                    ) : (
                      <XCircle size={18} className="text-rose-600 stroke-[2.2]" />
                    )}
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200/60 uppercase tracking-wider">
                        {item.category}
                      </span>
                      <h4 className="text-sm font-bold text-slate-900 tracking-tight">{item.title}</h4>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 leading-normal">{item.shortDesc}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2.5 self-end sm:self-auto flex-shrink-0">
                  <ClauseBadge
                    page={item.page}
                    clause={item.clauseRef}
                    excerpt={item.tenderClauseText}
                    documentName={tenderName}
                  />

                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${statusPill}`}>
                    {item.statusLabel}
                  </span>

                  <div className="w-6 h-6 rounded-md flex items-center justify-center text-slate-400 hover:text-slate-600">
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
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
                    className="overflow-hidden border-t border-slate-100"
                  >
                    <div className="px-5 pb-5 pt-3 space-y-3.5 text-xs bg-slate-50/70">
                      {/* Verbatim Tender Clause Excerpt */}
                      <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-bold text-slate-600 uppercase text-[11px] tracking-wider flex items-center gap-1.5">
                            <FileText size={13} className="text-blue-600" />
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
                            className="text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1"
                          >
                            Trace in Document <ExternalLink size={12} />
                          </button>
                        </div>
                        <p className="text-slate-700 leading-relaxed italic border-l-2 border-blue-500 pl-3">
                          &ldquo;{item.tenderClauseText}&rdquo;
                        </p>
                      </div>

                      {/* Two Column Analysis: Disqualification Trap vs Recommended Action */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="p-4 rounded-xl bg-rose-50/70 border border-rose-200/80 space-y-1">
                          <span className="font-bold text-rose-800 uppercase text-[10px] tracking-wider block">
                            ⚠️ Disqualification Pitfall
                          </span>
                          <p className="text-rose-900/90 leading-relaxed text-xs">{item.disqualificationRisk}</p>
                        </div>

                        <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200/80 space-y-1">
                          <span className="font-bold text-emerald-800 uppercase text-[10px] tracking-wider block">
                            ✓ Recommended Compliance Action
                          </span>
                          <p className="text-emerald-900/90 leading-relaxed text-xs">{item.actionRequired}</p>
                        </div>
                      </div>

                      {/* Current Vendor Position & CTA */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-white border border-slate-200/90 gap-3">
                        <div className="flex items-center gap-2.5">
                          <Info size={16} className="text-blue-600 flex-shrink-0" />
                          <span className="text-slate-700 font-medium text-xs">
                            <strong className="text-slate-900">Current Position:</strong> {item.vendorState}
                          </span>
                        </div>

                        {item.status === 'ACTION_REQUIRED' && onGenerateAffidavit && (
                          <button
                            type="button"
                            onClick={onGenerateAffidavit}
                            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors shadow-xs self-start sm:self-auto flex-shrink-0"
                          >
                            Auto-Draft Affidavit
                            <ArrowRight size={13} />
                          </button>
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
    </div>
  );
}
export default KnockoutClauseRadar;
