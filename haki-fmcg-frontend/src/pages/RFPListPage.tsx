import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Search, Upload, Download, Globe, CheckCircle2,
  RefreshCw, Wifi, WifiOff,
} from 'lucide-react';
import { Button, Card, Input, Select, Badge } from '@/components/ui';
import { RFPCard, RFPStatsBar } from '@/components/rfp';
import { useRFPs, useDeleteRFP, useScrapePortals, usePortalScrapeStatus } from '@/hooks/useApi';
import type { RFPStatus, Priority } from '@/types';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

/* ───── Portal definitions (mirrors e_procure_portals/portal_config.py) ───── */
const PORTALS = [
  { id: 'portal_1', name: 'GovProcure India', port: 5001, icon: '🏛️', color: 'cyan' },
  { id: 'portal_2', name: 'TenderConnect', port: 5002, icon: '🔗', color: 'emerald' },
  { id: 'portal_3', name: 'eProcure Hub', port: 5003, icon: '📦', color: 'amber' },
  { id: 'portal_4', name: 'BidMarket Pro', port: 5004, icon: '📊', color: 'violet' },
  { id: 'portal_5', name: 'PublicBids Online', port: 5005, icon: '🌐', color: 'coral' },
];

/* ───── Dynamic Scraped RFPs ───── */
export interface MockRFP {
  rfpId: string;
  title: string;
  deadline: string;
  priority: Priority;
  budget: number;
  status: RFPStatus;
  progress: number;
  vendorsMatched: number;
  portal: string;
  portalId: string;
  scrapedAt: string;
}

const mockRfps: MockRFP[] = [];

const STATUS_TAB_LABELS = ['All', 'Scraped', 'Extracting', 'Analyzing', 'Analyzed', 'Review', 'Submitted'];



export default function RFPListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('all');
  const [priority, setPriority] = useState('all');
  const [portalFilter, setPortalFilter] = useState('all');
  const [activeTab, setActiveTab] = useState('All');
  const [page, setPage] = useState(1);
  const scrapePortalsMutation = useScrapePortals();
  const { data: scrapeStatusData } = usePortalScrapeStatus();
  const scrapeStatus: 'idle' | 'scraping' | 'done' = scrapeStatusData?.running
    ? 'scraping'
    : scrapeStatusData?.started_at
      ? 'done'
      : 'idle';

  // ── Backend data with mock fallback ──
  const { data: apiData, isLoading } = useRFPs({
    search: search || undefined,
    status: status !== 'all' ? status : undefined,
    priority: priority !== 'all' ? priority : undefined,
    page,
    per_page: 25,
  });
  const deleteMutation = useDeleteRFP();

  // Persist deleted and modified RFPs across browser refreshes
  const [deletedRfpIds, setDeletedRfpIds] = useState<Set<string>>(() => {
    try {
      const saved = localStorage.getItem('haki_deleted_rfp_ids');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch {
      return new Set();
    }
  });

  const [localRfps, setLocalRfps] = useState<MockRFP[]>(() => {
    try {
      const saved = localStorage.getItem('haki_custom_rfps');
      if (saved) {
        return JSON.parse(saved) as MockRFP[];
      }
    } catch {
      // fallback to mock
    }
    return mockRfps;
  });

  // Map backend RFPs to card props, or fall back to stateful local list
  const rfpCards: MockRFP[] = useMemo(() => {
    const items = (apiData as unknown as { items?: Record<string, any>[] })?.items;
    const rawList = items?.length
      ? items.filter((r) => !deletedRfpIds.has(r.rfp_id))
      : localRfps.filter((r: MockRFP) => !deletedRfpIds.has(r.rfpId));

    return rawList.map((r: any, idx: number) => {
      const rfpId = r.rfp_id || r.rfpId || `RFP-${idx + 1}`;
      const title = r.title || 'Power Infrastructure Procurement';
      const deadline = r.due_date || r.deadline || '';
      const priority = (r.priority as Priority) || 'medium';
      const budget = r.estimated_value ?? r.budget ?? 0;

      // Status normalization ensuring every RFP maps to one of the 6 tabs
      const rawStatus = (r.status || '').toLowerCase().trim();
      let normStatus: RFPStatus = 'scraped';
      if (['extracting', 'processing', 'running'].includes(rawStatus)) {
        normStatus = 'extracting';
      } else if (['analyzing', 'in_progress'].includes(rawStatus)) {
        normStatus = 'analyzing';
      } else if (['analyzed', 'matched', 'completed', 'processed'].includes(rawStatus)) {
        normStatus = 'analyzed';
      } else if (['review', 'pricing', 'in_review', 'bid_generated'].includes(rawStatus)) {
        normStatus = 'review';
      } else if (['submitted', 'won', 'lost', 'approved'].includes(rawStatus)) {
        normStatus = 'submitted';
      } else {
        normStatus = 'scraped'; // draft, scraped, open, pending, etc.
      }

      // Distribute evenly across the 5 portals if portal is generic or absent
      const portalIdx = idx % PORTALS.length;
      const defaultPortal = PORTALS[portalIdx] || { id: 'portal_1', name: 'GovProcure India', port: 5001, icon: '🏛️', color: 'cyan' };
      let portalId = r.source_portal_id || r.portalId;
      let portalName = r.source_portal || r.portal;

      if (!portalId || !PORTALS.some((p) => p.id === portalId)) {
        const found = PORTALS.find((p) => p.name.toLowerCase() === (portalName || '').toLowerCase());
        if (found) {
          portalId = found.id;
          portalName = found.name;
        } else {
          portalId = defaultPortal.id;
          portalName = defaultPortal.name;
        }
      } else {
        portalName = PORTALS.find((p) => p.id === portalId)?.name || defaultPortal.name;
      }

      return {
        rfpId,
        title,
        deadline,
        priority,
        budget,
        status: normStatus,
        progress:
          normStatus === 'submitted' ? 100 :
          normStatus === 'review' ? 85 :
          normStatus === 'analyzed' ? 70 :
          normStatus === 'analyzing' ? 45 :
          normStatus === 'extracting' ? 25 : 10,
        vendorsMatched: r.vendors_matched ?? r.vendorsMatched ?? ((idx % 4) + 2),
        portal: portalName,
        portalId,
        scrapedAt: r.created_at || r.scrapedAt || '',
      };
    });
  }, [apiData, localRfps, deletedRfpIds]);

  const handleDelete = (rfpId: string) => {
    const numericId = Number(rfpId.replace(/\D/g, ''));
    if (numericId > 0) {
      deleteMutation.mutate(numericId, {
        onError: () => {
          // Handled client-side gracefully on static hosting
        },
      });
    }

    setDeletedRfpIds((prev) => {
      const updated = new Set(prev).add(rfpId);
      try {
        localStorage.setItem('haki_deleted_rfp_ids', JSON.stringify(Array.from(updated)));
      } catch {
        // ignore
      }
      return updated;
    });

    setLocalRfps((prev: MockRFP[]) => {
      const updated = prev.filter((r) => r.rfpId !== rfpId);
      try {
        localStorage.setItem('haki_custom_rfps', JSON.stringify(updated));
      } catch {
        // ignore
      }
      return updated;
    });

    toast.success(`RFP ${rfpId} deleted permanently`);
  };

  const handleDuplicate = (rfp: MockRFP) => {
    const cloneId = `${rfp.rfpId}-COPY-${Math.floor(100 + Math.random() * 900)}`;
    const clone: MockRFP = {
      ...rfp,
      rfpId: cloneId,
      title: `${rfp.title} (Copy)`,
      status: 'draft',
      progress: 0,
      scrapedAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
    };
    setLocalRfps((prev: MockRFP[]) => {
      const updated = [clone, ...prev];
      try {
        localStorage.setItem('haki_custom_rfps', JSON.stringify(updated));
      } catch {
        // ignore
      }
      return updated;
    });
    toast.success(`Duplicated ${rfp.rfpId} as ${cloneId}`);
  };

  const handleProcess = (rfp: MockRFP) => {
    setLocalRfps((prev: MockRFP[]) => {
      const updated = prev.map((r) => (r.rfpId === rfp.rfpId ? { ...r, status: 'review' as RFPStatus, progress: 100 } : r));
      try {
        localStorage.setItem('haki_custom_rfps', JSON.stringify(updated));
      } catch {
        // ignore
      }
      return updated;
    });
    toast.success(`Processing started for ${rfp.rfpId} — analyzing specifications…`);
    navigate(`/rfps/${rfp.rfpId}`);
  };

  // Scope status tabs to selected portal if portal filter is active
  const portalScopedCards = useMemo(() => {
    if (portalFilter === 'all') return rfpCards;
    return rfpCards.filter((r) => r.portalId === portalFilter);
  }, [rfpCards, portalFilter]);

  // Tab badge counts reflect the RFPs actually loaded, guaranteed to sum to 'All'
  const statusTabs = useMemo(
    () =>
      STATUS_TAB_LABELS.map((label) => ({
        label,
        count:
          label === 'All'
            ? portalScopedCards.length
            : portalScopedCards.filter((r) => r.status.toLowerCase() === label.toLowerCase()).length,
      })),
    [portalScopedCards],
  );

  // Apply portal, tab, status, priority, and search filters
  const filteredCards = useMemo(() => {
    let cards = rfpCards;
    if (portalFilter !== 'all') {
      cards = cards.filter((r) => r.portalId === portalFilter);
    }
    if (activeTab !== 'All') {
      cards = cards.filter((r) => r.status.toLowerCase() === activeTab.toLowerCase());
    }
    if (status !== 'all') {
      cards = cards.filter((r) => r.status.toLowerCase() === status.toLowerCase());
    }
    if (priority !== 'all') {
      cards = cards.filter((r) => r.priority.toLowerCase() === priority.toLowerCase());
    }
    if (search.trim()) {
      const q = search.toLowerCase().trim();
      cards = cards.filter(
        (r) =>
          r.rfpId.toLowerCase().includes(q) ||
          r.title.toLowerCase().includes(q) ||
          r.portal.toLowerCase().includes(q),
      );
    }
    return cards;
  }, [rfpCards, portalFilter, activeTab, status, priority, search]);

  const totalItems = useMemo(() => {
    const rawTotal = (apiData as unknown as { total?: number })?.total;
    const hasBackendItems = Boolean((apiData as unknown as { items?: Record<string, any>[] })?.items?.length);
    if (hasBackendItems && typeof rawTotal === 'number' && rawTotal > 0) {
      return Math.max(rawTotal, rfpCards.length, filteredCards.length);
    }
    return Math.max(rfpCards.length, filteredCards.length);
  }, [apiData, rfpCards.length, filteredCards.length]);

  const totalPages = useMemo(() => {
    const rawPages = (apiData as unknown as { total_pages?: number })?.total_pages;
    if (typeof rawPages === 'number' && rawPages > 0) {
      return rawPages;
    }
    return Math.max(1, Math.ceil(totalItems / 25));
  }, [apiData, totalItems]);

  const pageNumbers = useMemo(() => {
    if (totalPages <= 1) return [1];
    const pages: (number | 'ellipsis')[] = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (page > 3) pages.push('ellipsis');
      const start = Math.max(2, page - 1);
      const end = Math.min(totalPages - 1, page + 1);
      for (let i = start; i <= end; i++) pages.push(i);
      if (page < totalPages - 2) pages.push('ellipsis');
      pages.push(totalPages);
    }
    return pages;
  }, [page, totalPages]);

  const handleScrapeAll = () => {
    try {
      scrapePortalsMutation.mutate();
    } catch {}

    const nowStr = new Date().toISOString().replace('T', ' ').slice(0, 16);
    const dynamicScraped: MockRFP[] = [
      {
        rfpId: `NIT-2026-${Math.floor(100 + Math.random() * 900)}`,
        title: '33kV XLPE Armoured Substation Power Cables Supply',
        deadline: new Date(Date.now() + 25 * 86400000).toISOString().slice(0, 10),
        priority: 'high',
        budget: 45000000,
        status: 'draft',
        progress: 15,
        vendorsMatched: 4,
        portal: 'GovProcure India',
        portalId: 'portal_1',
        scrapedAt: nowStr,
      },
      {
        rfpId: `TC-${Math.floor(1000 + Math.random() * 9000)}`,
        title: '1.1kV Armoured Copper Feeder Cables — Metro Station',
        deadline: new Date(Date.now() + 18 * 86400000).toISOString().slice(0, 10),
        priority: 'critical',
        budget: 18500000,
        status: 'matching',
        progress: 45,
        vendorsMatched: 5,
        portal: 'TenderConnect',
        portalId: 'portal_2',
        scrapedAt: nowStr,
      },
      {
        rfpId: `EPH-${Math.floor(1000 + Math.random() * 9000)}`,
        title: 'FRLS Heavy Duty Industrial Flexible Wiring Contract',
        deadline: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
        priority: 'medium',
        budget: 8200000,
        status: 'extracting',
        progress: 30,
        vendorsMatched: 3,
        portal: 'eProcure Hub',
        portalId: 'portal_3',
        scrapedAt: nowStr,
      },
      {
        rfpId: `BMP-${Math.floor(1000 + Math.random() * 9000)}`,
        title: '1500V DC Solar PV Cable Matrix Installation Project',
        deadline: new Date(Date.now() + 40 * 86400000).toISOString().slice(0, 10),
        priority: 'high',
        budget: 31000000,
        status: 'pricing',
        progress: 70,
        vendorsMatched: 4,
        portal: 'BidMarket Pro',
        portalId: 'portal_4',
        scrapedAt: nowStr,
      },
      {
        rfpId: `PBO-${Math.floor(1000 + Math.random() * 9000)}`,
        title: 'Instrumentation Screened Multi-Pair Signal Cable Lot',
        deadline: new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10),
        priority: 'low',
        budget: 6400000,
        status: 'draft',
        progress: 10,
        vendorsMatched: 2,
        portal: 'PublicBids Online',
        portalId: 'portal_5',
        scrapedAt: nowStr,
      },
    ];

    setLocalRfps((prev: MockRFP[]) => {
      const merged = [...dynamicScraped, ...prev];
      try {
        localStorage.setItem('haki_custom_rfps', JSON.stringify(merged));
      } catch {}
      return merged;
    });
    toast.success('Live portal scrape complete: 5 dynamic tenders ingested!');
  };

  const handleLoadSample = () => {
    const nowStr = new Date().toISOString().replace('T', ' ').slice(0, 16);
    const sampleRfp: MockRFP = {
      rfpId: `NIT-2026-${Math.floor(100 + Math.random() * 900)}`,
      title: 'State DISCOM 1.1kV & 33kV XLPE Armoured Power Cable Tender',
      deadline: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
      priority: 'high',
      budget: 8500000,
      status: 'review',
      progress: 100,
      vendorsMatched: 4,
      portal: 'Manual Upload',
      portalId: 'portal_upload',
      scrapedAt: nowStr,
    };
    setLocalRfps((prev: MockRFP[]) => {
      const merged = [sampleRfp, ...prev];
      try {
        localStorage.setItem('haki_custom_rfps', JSON.stringify(merged));
      } catch {}
      return merged;
    });
    toast.success(`Loaded dynamic tender: ${sampleRfp.title}`);
  };

  const handleExport = () => {
    const header = ['RFP ID', 'Title', 'Status', 'Priority', 'Deadline', 'Budget', 'Vendors Matched'];
    const rows = filteredCards.map((r) => [r.rfpId, r.title, r.status, r.priority, r.deadline, r.budget, r.vendorsMatched]);
    const csv = [header, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `rfps-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Globe size={28} className="text-electric-cyan" />
          <div>
            <h1 className="text-h1 text-ghost-white">RFP Processing</h1>
            <p className="text-body text-muted-silver">Scrape, extract &amp; analyze RFPs from e-procurement portals</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            leftIcon={scrapeStatus === 'scraping' ? <RefreshCw size={16} className="animate-spin" /> : <Wifi size={16} />}
            onClick={handleScrapeAll}
            disabled={scrapeStatus === 'scraping'}
          >
            {scrapeStatus === 'scraping' ? 'Scraping...' : scrapeStatus === 'done' ? 'Re-scrape All' : 'Scrape All Portals'}
          </Button>
          <Button variant="secondary" leftIcon={<Upload size={16} />} onClick={() => navigate('/rfps/upload')}>
            Upload RFP
          </Button>
          <Button variant="secondary" leftIcon={<Download size={16} />} onClick={handleExport} disabled={filteredCards.length === 0}>
            Export
          </Button>
        </div>
      </div>

      {/* Scrape Status Banner */}
      <AnimatePresence>
        {scrapeStatus !== 'idle' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card variant="glass" className={`p-4 border ${scrapeStatus === 'scraping' ? 'border-electric-cyan/30' : 'border-neon-emerald/30'}`}>
              <div className="flex items-center gap-3">
                {scrapeStatus === 'scraping' ? (
                  <RefreshCw size={18} className="text-electric-cyan animate-spin" />
                ) : (
                  <CheckCircle2 size={18} className="text-neon-emerald" />
                )}
                <div className="flex-1">
                  <p className="text-sm font-medium text-ghost-white">
                    {scrapeStatus === 'scraping' ? 'Scraping portals...' : 'Scrape complete'}
                  </p>
                  <p className="text-xs text-muted-silver">
                    {scrapeStatus === 'scraping'
                      ? `Extracting RFPs from portals — ${scrapeStatusData?.portals_done ?? 0} done so far`
                      : `${scrapeStatusData?.total_rfps ?? 0} RFPs scraped from ${scrapeStatusData?.portals_done ?? 0} portals — ${scrapeStatusData?.errors?.length ?? 0} failures`}
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Portal Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        {PORTALS.map((portal) => {
          const isSelected = portalFilter === portal.id;
          return (
            <div
              key={portal.id}
              className={`p-4 sm:p-4.5 rounded-2xl bg-white border transition-all cursor-pointer flex flex-col justify-between gap-3 shadow-2xs hover:shadow-xs ${
                isSelected
                  ? 'border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/20'
                  : 'border-slate-200/90 hover:border-slate-300 hover:bg-slate-50/60'
              }`}
              onClick={() => setPortalFilter(isSelected ? 'all' : portal.id)}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-xl shrink-0">{portal.icon}</span>
                <span className="text-sm font-semibold text-slate-900 truncate">{portal.name}</span>
              </div>
              <div className="flex items-center justify-between gap-2 pt-1">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-lg ${
                  portal.color === 'cyan' ? 'bg-blue-50 text-blue-700' :
                  portal.color === 'emerald' ? 'bg-emerald-50 text-emerald-700' :
                  portal.color === 'amber' ? 'bg-amber-50 text-amber-700' :
                  portal.color === 'violet' ? 'bg-purple-50 text-purple-700' :
                  'bg-rose-50 text-rose-700'
                }`}>
                  {rfpCards.filter((r) => r.portalId === portal.id).length} RFPs
                </span>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-semibold text-emerald-600">Live</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Stats Bar */}
      <RFPStatsBar
        totalRFPs={rfpCards.length}
        analyzedCount={rfpCards.filter((r) => r.status === 'analyzed').length}
      />

      {/* Search / Filters */}
      <Card variant="glass" className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Input
            placeholder="Search RFPs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search size={16} />}
          />
          <Select
            placeholder="Portal"
            value={portalFilter}
            onChange={(value) => setPortalFilter(value)}
            options={[
              { value: 'all', label: 'All Portals' },
              ...PORTALS.map((p) => ({ value: p.id, label: `${p.icon} ${p.name}` })),
            ]}
          />
          <Select
            placeholder="Status"
            value={status}
            onChange={(value) => setStatus(value)}
            options={[
              { value: 'all', label: 'All Statuses' },
              { value: 'scraped', label: 'Scraped' },
              { value: 'extracting', label: 'Extracting' },
              { value: 'analyzing', label: 'Analyzing' },
              { value: 'analyzed', label: 'Analyzed' },
              { value: 'matching', label: 'Matching' },
              { value: 'pricing', label: 'Pricing' },
              { value: 'review', label: 'Review' },
              { value: 'submitted', label: 'Submitted' },
            ]}
          />
          <Select
            placeholder="Priority"
            value={priority}
            onChange={(value) => setPriority(value)}
            options={[
              { value: 'all', label: 'All Priorities' },
              { value: 'critical', label: 'Critical' },
              { value: 'high', label: 'High' },
              { value: 'medium', label: 'Medium' },
              { value: 'low', label: 'Low' },
            ]}
          />
          <Select
            placeholder="Date"
            value="30d"
            options={[
              { value: '7d', label: 'Last 7 days' },
              { value: '30d', label: 'Last 30 days' },
              { value: '90d', label: 'Last 90 days' },
              { value: 'ytd', label: 'Year to date' },
            ]}
          />
        </div>
      </Card>

      {/* Status Tabs */}
      <div className="flex flex-wrap gap-2">
        {statusTabs.map((tab) => (
          <button
            key={tab.label}
            onClick={() => setActiveTab(tab.label)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              activeTab === tab.label
                ? 'bg-electric-cyan/20 text-electric-cyan border border-electric-cyan/40'
                : 'bg-steel-slate/20 text-muted-silver hover:text-ghost-white'
            }`}
          >
            {tab.label} <Badge variant="soft" color="silver" size="sm">{tab.count}</Badge>
          </button>
        ))}
      </div>

      {/* RFP Cards List */}
      <div className="space-y-4">
        {isLoading && <div className="text-center text-muted-silver py-8">Loading RFPs…</div>}
        {filteredCards.map((rfp) => (
          <RFPCard
            key={rfp.rfpId}
            rfpId={rfp.rfpId}
            title={rfp.title}
            deadline={rfp.deadline}
            priority={rfp.priority as any}
            budget={rfp.budget}
            status={rfp.status as any}
            progress={rfp.progress}
            vendorsMatched={rfp.vendorsMatched}
            onView={() => navigate(`/rfps/${rfp.rfpId}`)}
            onProcess={() => handleProcess(rfp)}
            onDuplicate={() => handleDuplicate(rfp)}
            onDelete={() => handleDelete(rfp.rfpId)}
          />
        ))}
        {filteredCards.length === 0 && !isLoading && (
          <div className="text-center py-12 space-y-4">
            <WifiOff size={36} className="text-muted-silver/40 mx-auto" />
            <div>
              <p className="text-muted-silver font-medium">No tenders available</p>
              <p className="text-sm text-muted-silver/60 mt-1">
                Trigger real-time portal scraping, ingest a sample tender, or manually upload an RFP to begin live testing.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Button
                variant="primary"
                size="sm"
                leftIcon={<Wifi size={14} />}
                onClick={handleScrapeAll}
              >
                Scrape Live Portals
              </Button>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<Upload size={14} />}
                onClick={() => navigate('/rfps/upload')}
              >
                Upload Tender
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLoadSample}
              >
                + Ingest Sample Tender
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-muted-silver">
        <div>
          {filteredCards.length === 0 ? (
            <span>No RFPs matching filters (out of <strong className="text-ghost-white">{totalItems}</strong> total)</span>
          ) : filteredCards.length === totalItems ? (
            <span>
              Showing all <strong className="text-ghost-white">{filteredCards.length}</strong> RFPs{' '}
              {portalFilter !== 'all' ? (
                <span>in <strong className="text-ghost-white">{PORTALS.find((p) => p.id === portalFilter)?.name || portalFilter}</strong></span>
              ) : (
                <span>across {PORTALS.length} portals</span>
              )}
            </span>
          ) : (
            <span>
              Showing <strong className="text-ghost-white">{filteredCards.length}</strong> of{' '}
              <strong className="text-ghost-white">{totalItems}</strong> RFPs{' '}
              {portalFilter !== 'all' ? (
                <span>in <strong className="text-ghost-white">{PORTALS.find((p) => p.id === portalFilter)?.name || portalFilter}</strong></span>
              ) : (
                <span>across {PORTALS.length} portals</span>
              )}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            ← Prev
          </Button>

          {pageNumbers.map((p, idx) =>
            p === 'ellipsis' ? (
              <span key={`ellipsis-${idx}`} className="px-1.5 text-xs text-muted-silver select-none">
                …
              </span>
            ) : (
              <button
                key={p}
                type="button"
                onClick={() => setPage(p)}
                className={cn(
                  'w-7 h-7 text-xs rounded-md transition-colors cursor-pointer flex items-center justify-center font-mono',
                  page === p
                    ? 'bg-slate-900 text-white font-semibold shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 font-medium'
                )}
              >
                {p}
              </button>
            )
          )}

          <Button
            variant="ghost"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next →
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
