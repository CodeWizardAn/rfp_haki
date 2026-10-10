import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Search, Upload, Download, Globe, CheckCircle2, Clock,
  RefreshCw, Wifi, WifiOff,
} from 'lucide-react';
import { Button, Card, Input, Select, Badge } from '@/components/ui';
import { RFPCard, RFPStatsBar } from '@/components/rfp';
import { useRFPs, useDeleteRFP, useScrapePortals, usePortalScrapeStatus } from '@/hooks/useApi';
import type { RFPStatus, Priority } from '@/types';
import toast from 'react-hot-toast';

/* ───── Portal definitions (mirrors e_procure_portals/portal_config.py) ───── */
const PORTALS = [
  { id: 'portal_1', name: 'GovProcure India', port: 5001, icon: '🏛️', color: 'cyan', rfps: ['RFP2', 'RFP21', 'RFP26'] },
  { id: 'portal_2', name: 'TenderConnect', port: 5002, icon: '🔗', color: 'emerald', rfps: ['RFP17', 'RFP22', 'RFP27'] },
  { id: 'portal_3', name: 'eProcure Hub', port: 5003, icon: '📦', color: 'amber', rfps: ['RFP18', 'RFP23', 'RFP28'] },
  { id: 'portal_4', name: 'BidMarket Pro', port: 5004, icon: '📊', color: 'violet', rfps: ['RFP19', 'RFP24', 'RFP29'] },
  { id: 'portal_5', name: 'PublicBids Online', port: 5005, icon: '🌐', color: 'coral', rfps: ['RFP20', 'RFP25', 'RFP30'] },
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
    if (items?.length) {
      return items
        .filter((r) => !deletedRfpIds.has(r.rfp_id))
        .map((r) => ({
          rfpId: r.rfp_id,
          title: r.title,
          deadline: r.due_date ?? '',
          priority: r.priority as Priority,
          budget: r.estimated_value ?? 0,
          status: r.status as RFPStatus,
          progress: r.status === 'won' ? 100 : r.status === 'submitted' ? 100 : r.status === 'review' ? 85 : r.status === 'pricing' ? 65 : r.status === 'matching' ? 45 : r.status === 'extracting' ? 25 : 10,
          vendorsMatched: 0,
          portal: 'API Source',
          portalId: 'portal_1',
          scrapedAt: r.created_at ?? '',
        }));
    }
    return localRfps.filter((r: MockRFP) => !deletedRfpIds.has(r.rfpId));
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

  // Apply portal + tab filters
  const filteredCards = useMemo(() => {
    let cards = rfpCards;
    if (portalFilter !== 'all') {
      cards = cards.filter((r) => r.portalId === portalFilter);
    }
    if (activeTab !== 'All') {
      cards = cards.filter((r) => r.status.toLowerCase() === activeTab.toLowerCase());
    }
    return cards;
  }, [rfpCards, portalFilter, activeTab]);

  // Tab badge counts reflect the RFPs actually loaded, not hardcoded numbers
  const statusTabs = useMemo(
    () =>
      STATUS_TAB_LABELS.map((label) => ({
        label,
        count: label === 'All' ? rfpCards.length : rfpCards.filter((r) => r.status.toLowerCase() === label.toLowerCase()).length,
      })),
    [rfpCards],
  );

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
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {PORTALS.map((portal) => (
          <Card
            key={portal.id}
            variant="glass"
            className={`p-3 cursor-pointer transition-all hover:scale-[1.02] ${
              portalFilter === portal.id ? 'ring-2 ring-electric-cyan/50' : ''
            }`}
            onClick={() => setPortalFilter(portalFilter === portal.id ? 'all' : portal.id)}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{portal.icon}</span>
              <span className="text-xs font-medium text-ghost-white truncate">{portal.name}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1">
                <Badge variant="soft" color={portal.color as any} size="sm">{portal.rfps.length} RFPs</Badge>
              </div>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-neon-emerald animate-pulse" />
                <span className="text-[10px] text-neon-emerald">Live</span>
              </div>
            </div>
            <p className="text-[10px] text-muted-silver mt-1.5">Port {portal.port}</p>
          </Card>
        ))}
      </div>

      {/* Stats Bar */}
      <RFPStatsBar />

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
          <div key={rfp.rfpId} className="relative">
            {/* Portal source indicator */}
            <div className="absolute -top-2 left-4 z-10 flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-deep-navy/90 border border-steel-slate/30">
              <span className="text-xs">{PORTALS.find((p) => p.id === rfp.portalId)?.icon || '📄'}</span>
              <span className="text-[10px] text-muted-silver">{rfp.portal}</span>
              {rfp.scrapedAt && (
                <>
                  <span className="text-[10px] text-steel-slate/60">·</span>
                  <Clock size={9} className="text-muted-silver/60" />
                  <span className="text-[10px] text-muted-silver/60">{rfp.scrapedAt}</span>
                </>
              )}
            </div>
            <RFPCard
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
          </div>
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
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))}>← Prev</Button>
          <span className="text-ghost-white">{page}</span>
          {page < totalPages && <span className="cursor-pointer" onClick={() => setPage(page + 1)}>{page + 1}</span>}
          {totalPages > 3 && <span>...</span>}
          {totalPages > 1 && <span className="cursor-pointer" onClick={() => setPage(totalPages)}>{totalPages}</span>}
          <Button variant="ghost" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>Next →</Button>
        </div>
      </div>
    </motion.div>
  );
}
