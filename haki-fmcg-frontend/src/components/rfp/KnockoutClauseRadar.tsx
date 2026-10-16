import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
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
  const [items, setItems] = useState<GatekeeperItem[]>(customItems || DEFAULT_GATEKEEPERS);

  useEffect(() => {
    if (customItems && customItems.length > 0) {
      setItems(customItems);
    }
  }, [customItems]);
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
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden font-sans shadow-xs">
      {/* ── Top Header Banner ── */}
      <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">
            Knockout Clause &amp; Disqualification Radar
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            Pre-qualification audit against statutory and financial traps buried in tender documentation.
          </p>
        </div>

        {/* Status Counts */}
        <div className="flex items-center gap-4 text-sm font-medium">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-600">Passed:</span>
            <span className="font-semibold text-slate-900">{passedCount}/{items.length}</span>
          </div>
          {actionCount > 0 && (
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span className="text-slate-600">Action:</span>
              <span className="font-semibold text-amber-700">{actionCount}</span>
            </div>
          )}
          {riskCount > 0 && (
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <span className="text-slate-600">Risk:</span>
              <span className="font-semibold text-rose-700">{riskCount}</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Filter Tabs ── */}
      <div className="px-6 py-3 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
        {(['ALL', 'RISKS', 'ACTIONS', 'CLEARED'] as const).map((tab) => {
          const labels = {
            ALL: `All Criteria (${items.length})`,
            RISKS: `Risks (${riskCount})`,
            ACTIONS: `Action Needed (${actionCount})`,
            CLEARED: `Cleared (${passedCount})`,
          };
          const isActive = filter === tab;
          return (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-white text-slate-900 shadow-xs border border-slate-200'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              {labels[tab]}
            </button>
          );
        })}
      </div>

      {/* ── Gatekeeper List Items ── */}
      <div className="divide-y divide-slate-100">
        {filteredItems.map((item) => {
          const isExpanded = expandedId === item.id;
          const statusBadge =
            item.status === 'PASS'
              ? 'bg-emerald-50 text-emerald-700'
              : item.status === 'ACTION_REQUIRED'
                ? 'bg-amber-50 text-amber-800'
                : 'bg-rose-50 text-rose-700';

          return (
            <div
              key={item.id}
              className={`transition-colors ${isExpanded ? 'bg-slate-50/60' : 'bg-white hover:bg-slate-50/40'}`}
            >
              {/* Item Header Row */}
              <div
                onClick={() => setExpandedId(isExpanded ? null : item.id)}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer select-none"
              >
                <div className="flex items-start gap-4">
                  <div className="mt-1 flex-shrink-0">
                    {item.status === 'PASS' ? (
                      <CheckCircle2 size={19} className="text-emerald-600" />
                    ) : item.status === 'ACTION_REQUIRED' ? (
                      <AlertTriangle size={19} className="text-amber-500" />
                    ) : (
                      <XCircle size={19} className="text-rose-600" />
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-2.5">
                      <h4 className="text-base font-semibold text-slate-900">{item.title}</h4>
                      <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                        {item.category}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 mt-1 leading-relaxed">{item.shortDesc}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-auto flex-shrink-0">
                  <ClauseBadge
                    page={item.page}
                    clause={item.clauseRef}
                    excerpt={item.tenderClauseText}
                    documentName={tenderName}
                  />

                  <span className={`px-3 py-1 rounded-md text-xs font-medium ${statusBadge}`}>
                    {item.statusLabel}
                  </span>

                  <div className="text-slate-400">
                    {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
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
                    className="overflow-hidden border-t border-slate-100 bg-slate-50/50"
                  >
                    <div className="p-6 space-y-4 text-sm">
                      {/* Verbatim Tender Clause Excerpt */}
                      <div className="bg-white rounded-lg p-5 border border-slate-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold text-slate-700 text-xs">
                            Clause Excerpt ({item.clauseRef} • Page {item.page})
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
                            className="text-xs font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1"
                          >
                            View Source <ExternalLink size={12} />
                          </button>
                        </div>
                        <p className="text-slate-800 leading-relaxed italic border-l-2 border-blue-500 pl-3">
                          &ldquo;{item.tenderClauseText}&rdquo;
                        </p>
                      </div>

                      {/* Two Column Analysis */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 rounded-lg bg-rose-50/60 border border-rose-100">
                          <span className="font-semibold text-rose-800 text-xs block mb-1">
                            Disqualification Risk
                          </span>
                          <p className="text-rose-900 leading-relaxed text-xs">{item.disqualificationRisk}</p>
                        </div>

                        <div className="p-4 rounded-lg bg-emerald-50/60 border border-emerald-100">
                          <span className="font-semibold text-emerald-800 text-xs block mb-1">
                            Required Action
                          </span>
                          <p className="text-emerald-900 leading-relaxed text-xs">{item.actionRequired}</p>
                        </div>
                      </div>

                      {/* Vendor State Note */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-lg bg-white border border-slate-200 gap-3">
                        <div className="flex items-center gap-2">
                          <Info size={16} className="text-slate-400 flex-shrink-0" />
                          <span className="text-slate-700 text-xs">
                            <strong className="text-slate-900 font-medium">Current Evaluation:</strong> {item.vendorState}
                          </span>
                        </div>

                        {item.status === 'ACTION_REQUIRED' && onGenerateAffidavit && (
                          <button
                            type="button"
                            onClick={onGenerateAffidavit}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs transition-colors self-start sm:self-auto"
                          >
                            Draft Affidavit
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
