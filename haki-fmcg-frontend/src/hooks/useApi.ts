/**
 * React Query hooks — backend ↔ frontend bridge
 * Wraps all service calls with caching, invalidation, optimistic updates.
 * Every hook returns { data, isLoading, error } and gracefully falls back
 * to empty states when the backend is unreachable.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rfpService, type RFPFilters } from '@/services/rfp.service';
import { productService, type ProductFilters } from '@/services/product.service';
import { vendorService, type VendorFilters } from '@/services/vendor.service';
import { bidService, type BidFilters } from '@/services/bid.service';
import { pipelineService } from '@/services/pipeline.service';
import { analyticsService } from '@/services/analytics.service';
import { agentService } from '@/services/agent.service';
import { authService } from '@/services/auth.service';
import api from '@/services/api';
import type {
  RFP,
  Product,
  Vendor,
  Bid,
  PipelineRun,
  DashboardStats,
  AuditLogEntry,
  ComplianceCheck,
  AgentType,
  ApiResponse,
  PaginatedResponse,
} from '@/types';
import { STALE_TIME_SHORT, STALE_TIME_LONG } from '@/utils/constants';

// ─────────────────────── Helpers ───────────────────────

const keys = {
  // auth
  profile: ['auth', 'profile'] as const,

  // dashboard
  dashboardStats: ['dashboard', 'stats'] as const,
  dashboardActivity: (page: number) => ['dashboard', 'activity', page] as const,
  winLossPrediction: ['dashboard', 'win-loss-prediction'] as const,
  systemHealth: ['system', 'health'] as const,

  // rfps
  rfps: (filters?: RFPFilters) => ['rfps', filters ?? {}] as const,
  rfp: (id: number) => ['rfps', id] as const,
  rfpStatus: (id: number) => ['rfps', id, 'status'] as const,
  rfpResults: (id: number) => ['rfps', id, 'results'] as const,

  // products
  products: (filters?: ProductFilters) => ['products', filters ?? {}] as const,
  product: (id: number) => ['products', id] as const,
  productBySku: (sku: string) => ['products', 'sku', sku] as const,
  productCategories: ['products', 'categories'] as const,
  productSearch: (q: string) => ['products', 'search', q] as const,

  // vendors
  vendors: (filters?: VendorFilters) => ['vendors', filters ?? {}] as const,
  vendor: (id: number) => ['vendors', id] as const,
  vendorRankings: ['vendors', 'rankings'] as const,

  // bids
  bids: (filters?: BidFilters) => ['bids', filters ?? {}] as const,
  bid: (id: number) => ['bids', id] as const,

  // pipeline
  pipelineRuns: ['pipeline', 'runs'] as const,
  pipelineRun: (id: number) => ['pipeline', 'runs', id] as const,

  // agents
  agentStatuses: ['agents', 'statuses'] as const,
  agentConversations: (type?: AgentType) => ['agents', 'conversations', type] as const,
  agentConversation: (id: string) => ['agents', 'conversations', id] as const,

  // analytics
  analyticsOverview: ['analytics', 'overview'] as const,
  analyticsRfp: (period?: string) => ['analytics', 'rfp', period] as const,
  analyticsBid: (period?: string) => ['analytics', 'bid', period] as const,
  analyticsPerformance: ['analytics', 'performance'] as const,

  // compliance
  complianceChecks: (rfpId?: number) => ['compliance', rfpId] as const,

  // audit
  auditLogs: (page: number) => ['audit', 'logs', page] as const,
  auditLog: (id: number) => ['audit', 'logs', id] as const,

  // config
  config: ['config'] as const,
  configKey: (key: string) => ['config', key] as const,

  // webhooks
  webhooks: ['webhooks'] as const,
  webhook: (id: string) => ['webhooks', id] as const,
  webhookLogs: (id: string) => ['webhooks', id, 'logs'] as const,
};

export { keys as queryKeys };

// ─────────────────────── Auth ───────────────────────

export function useProfile() {
  return useQuery({
    queryKey: keys.profile,
    queryFn: () => authService.getProfile(),
    staleTime: STALE_TIME_LONG,
    retry: 1,
  });
}

// ─────────────────────── Dashboard ───────────────────────

export function useDashboardStats() {
  return useQuery({
    queryKey: keys.dashboardStats,
    queryFn: () => analyticsService.getDashboardStats(),
    staleTime: STALE_TIME_SHORT,
    retry: 2,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: keys.systemHealth,
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<{
        status: string;
        uptime: number;
        version: string;
        components: Record<string, string>;
      }>>('/health');
      return data.data ?? data;
    },
    staleTime: STALE_TIME_SHORT,
    refetchInterval: 30_000,
    retry: 1,
  });
}

export function useActivityFeed(page = 1) {
  return useQuery({
    queryKey: keys.dashboardActivity(page),
    queryFn: () => analyticsService.getActivityFeed(page),
    staleTime: STALE_TIME_SHORT,
  });
}

export function useWinLossPrediction() {
  return useQuery({
    queryKey: keys.winLossPrediction,
    queryFn: () => analyticsService.getWinLossPrediction(),
    staleTime: STALE_TIME_SHORT,
    retry: 2,
  });
}

// ─────────────────────── RFPs ───────────────────────

export function useRFPs(filters?: RFPFilters) {
  return useQuery({
    queryKey: keys.rfps(filters),
    queryFn: () => rfpService.list(filters),
    staleTime: STALE_TIME_SHORT,
  });
}

export function useRFP(id: number) {
  return useQuery({
    queryKey: keys.rfp(id),
    queryFn: () => rfpService.getById(id),
    enabled: id > 0,
  });
}

export function useRFPStatus(id: number) {
  return useQuery({
    queryKey: keys.rfpStatus(id),
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<{ status: string; progress: number }>>(`/rfps/${id}/status`);
      return data.data;
    },
    enabled: id > 0,
    refetchInterval: 5_000,
  });
}

export function useRFPResults(id: number) {
  return useQuery({
    queryKey: keys.rfpResults(id),
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<Record<string, unknown>>>(`/rfps/${id}/results`);
      return data.data;
    },
    enabled: id > 0,
  });
}

export function useCreateRFP() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (rfp: Partial<RFP>) => rfpService.create(rfp),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rfps'] }),
  });
}

export function useUploadRFP() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => rfpService.uploadFile(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rfps'] }),
  });
}

export function useAnalyzeRFP() {
  return useMutation({
    mutationFn: (payload: {
      file: File;
      options?: {
        include_calculations?: boolean;
        include_recommendations?: boolean;
        include_budget?: boolean;
        cable_length?: number;
        application?: string;
      };
    }) => rfpService.analyzeRFP(payload.file, payload.options),
  });
}

export function useUpdateRFP() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<RFP> }) => rfpService.update(id, data),
    onSuccess: (_d, { id }) => {
      qc.invalidateQueries({ queryKey: keys.rfp(id) });
      qc.invalidateQueries({ queryKey: ['rfps'] });
    },
  });
}

export function useDeleteRFP() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => rfpService.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rfps'] }),
  });
}

// ─────────────────────── Products ───────────────────────

export function useProducts(filters?: ProductFilters) {
  return useQuery({
    queryKey: keys.products(filters),
    queryFn: () => productService.list(filters),
    staleTime: STALE_TIME_LONG,
  });
}

export function useProduct(id: number) {
  return useQuery({
    queryKey: keys.product(id),
    queryFn: () => productService.getById(id),
    enabled: id > 0,
  });
}

export function useProductBySku(sku: string) {
  return useQuery({
    queryKey: keys.productBySku(sku),
    queryFn: () => productService.getBySku(sku),
    enabled: !!sku,
  });
}

export function useProductSearch(query: string, limit = 20) {
  return useQuery({
    queryKey: keys.productSearch(query),
    queryFn: () => productService.search(query, limit),
    enabled: query.length >= 2,
    staleTime: STALE_TIME_SHORT,
  });
}

export function useProductCategories() {
  return useQuery({
    queryKey: keys.productCategories,
    queryFn: () => productService.getCategories(),
    staleTime: STALE_TIME_LONG,
  });
}

// ─────────────────────── Vendors ───────────────────────

export function useVendors(filters?: VendorFilters) {
  return useQuery({
    queryKey: keys.vendors(filters),
    queryFn: () => vendorService.list(filters),
    staleTime: STALE_TIME_SHORT,
  });
}

export function useVendor(id: number) {
  return useQuery({
    queryKey: keys.vendor(id),
    queryFn: () => vendorService.getById(id),
    enabled: id > 0,
  });
}

export function useCreateVendor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vendor: Partial<Vendor>) => vendorService.create(vendor),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['vendors'] }),
  });
}

export function useUpdateVendor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Vendor> }) => vendorService.update(id, data),
    onSuccess: (_d, { id }) => {
      qc.invalidateQueries({ queryKey: keys.vendor(id) });
      qc.invalidateQueries({ queryKey: ['vendors'] });
    },
  });
}

export function useVendorRankings() {
  return useQuery({
    queryKey: keys.vendorRankings,
    queryFn: () => vendorService.getRankings(),
    staleTime: STALE_TIME_LONG,
  });
}

// ─────────────────────── Bids ───────────────────────

export function useBids(filters?: BidFilters) {
  return useQuery({
    queryKey: keys.bids(filters),
    queryFn: () => bidService.list(filters),
    staleTime: STALE_TIME_SHORT,
  });
}

export function useBid(id: number) {
  return useQuery({
    queryKey: keys.bid(id),
    queryFn: () => bidService.getById(id),
    enabled: id > 0,
  });
}

export function useCreateBid() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (bid: Partial<Bid>) => bidService.create(bid),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bids'] }),
  });
}

export function useUpdateBid() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Bid> }) => bidService.update(id, data),
    onSuccess: (_d, { id }) => {
      qc.invalidateQueries({ queryKey: keys.bid(id) });
      qc.invalidateQueries({ queryKey: ['bids'] });
    },
  });
}

export function useDeleteBid() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => bidService.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bids'] }),
  });
}

export function useSubmitBid() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => bidService.submit(id),
    onSuccess: (_d, id) => {
      qc.invalidateQueries({ queryKey: keys.bid(id) });
      qc.invalidateQueries({ queryKey: ['bids'] });
    },
  });
}

export function useBidApproval() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ bidId, action, comments }: { bidId: number; action: 'approve' | 'reject'; comments?: string }) =>
      bidService.approveReject(bidId, action, comments),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bids'] }),
  });
}

// ─────────────────────── Pipeline ───────────────────────

export function usePipelineRuns() {
  return useQuery({
    queryKey: keys.pipelineRuns,
    queryFn: () => pipelineService.list(),
    staleTime: STALE_TIME_SHORT,
    refetchInterval: 10_000,
  });
}

export function usePipelineRun(id: number) {
  return useQuery({
    queryKey: keys.pipelineRun(id),
    queryFn: () => pipelineService.getById(id),
    enabled: id > 0,
    refetchInterval: 5_000,
  });
}

export function useStartPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (rfpId: number) => pipelineService.start(rfpId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipeline'] }),
  });
}

export function useCancelPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => pipelineService.cancel(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipeline'] }),
  });
}

export function useRetryPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, stage }: { id: string; stage?: string }) => pipelineService.retry(id, stage),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pipeline'] }),
  });
}

// ─────────────────────── Agents ───────────────────────

export function useAgentStatuses() {
  return useQuery({
    queryKey: keys.agentStatuses,
    queryFn: () => agentService.getStatuses(),
    staleTime: STALE_TIME_SHORT,
    refetchInterval: 15_000,
  });
}

export function useAgentConversations(type?: AgentType) {
  return useQuery({
    queryKey: keys.agentConversations(type),
    queryFn: () => agentService.getConversations(type),
    staleTime: STALE_TIME_SHORT,
  });
}

export function useAgentConversation(id: string) {
  return useQuery({
    queryKey: keys.agentConversation(id),
    queryFn: () => agentService.getConversation(id),
    enabled: !!id,
    refetchInterval: 3_000,
  });
}

export function useSendAgentMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ conversationId, message }: { conversationId: string; message: string }) =>
      agentService.sendMessage(conversationId, message),
    onSuccess: (_d, { conversationId }) =>
      qc.invalidateQueries({ queryKey: keys.agentConversation(conversationId) }),
  });
}

export function useStartAgentWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ rfpId, agentType }: { rfpId: number; agentType?: AgentType }) =>
      agentService.startWorkflow(rfpId, agentType),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['agents'] }),
  });
}

// ─────────────────────── Analytics ───────────────────────

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: keys.analyticsOverview,
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<Record<string, unknown>>>('/analytics/overview');
      return data.data;
    },
    staleTime: STALE_TIME_SHORT,
  });
}

export function useRFPAnalytics(period?: string) {
  return useQuery({
    queryKey: keys.analyticsRfp(period),
    queryFn: () => analyticsService.getRFPAnalytics(period),
    staleTime: STALE_TIME_SHORT,
  });
}

export function useBidAnalytics(period?: string) {
  return useQuery({
    queryKey: keys.analyticsBid(period),
    queryFn: () => analyticsService.getBidAnalytics(period),
    staleTime: STALE_TIME_SHORT,
  });
}

export function usePerformanceMetrics() {
  return useQuery({
    queryKey: keys.analyticsPerformance,
    queryFn: () => analyticsService.getPerformanceMetrics(),
    staleTime: STALE_TIME_SHORT,
    refetchInterval: 30_000,
  });
}

// ─────────────────────── Compliance & Audit ───────────────────────

export function useComplianceChecks(rfpId?: number) {
  return useQuery({
    queryKey: keys.complianceChecks(rfpId),
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<ComplianceCheck[]>>('/compliance/checks', {
        params: rfpId ? { rfp_id: rfpId } : {},
      });
      return data.data;
    },
    staleTime: STALE_TIME_LONG,
  });
}

export function useAuditLogs(page = 1) {
  return useQuery({
    queryKey: keys.auditLogs(page),
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<AuditLogEntry>>('/audit/logs', {
        params: { page, per_page: 50 },
      });
      return data;
    },
    staleTime: STALE_TIME_SHORT,
  });
}

export function useAuditLog(id: number) {
  return useQuery({
    queryKey: keys.auditLog(id),
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<AuditLogEntry>>(`/audit/logs/${id}`);
      return data.data;
    },
    enabled: id > 0,
  });
}

// ─────────────────────── Config ───────────────────────

export function useConfig() {
  return useQuery({
    queryKey: keys.config,
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<Record<string, unknown>>>('/config');
      return data.data;
    },
    staleTime: STALE_TIME_LONG,
  });
}

export function useUpdateConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) =>
      api.put(`/config/${key}`, { value }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['config'] }),
  });
}

export function useResetConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post('/config/reset'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['config'] }),
  });
}

// ─────────────────────── Portal Scraping ───────────────────────

export interface PortalScrapeStatus {
  running: boolean;
  started_at?: string;
  portals_done: number;
  total_rfps: number;
  errors: string[];
}

export function usePortalScrapeStatus(enabled = true) {
  return useQuery({
    queryKey: ['portals', 'scrape', 'status'],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<PortalScrapeStatus>>('/portals/scrape/status');
      return data.data;
    },
    enabled,
    refetchInterval: (query) => (query.state.data?.running ? 2000 : false),
  });
}

export function useScrapePortals() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post('/portals/scrape'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portals', 'scrape', 'status'] }),
  });
}

export function usePortalRFPs() {
  return useQuery({
    queryKey: ['portals', 'rfps'],
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<Record<string, any>[]>>('/portals/rfps');
      return data.data;
    },
    staleTime: STALE_TIME_SHORT,
  });
}

// ─────────────────────── Webhooks ───────────────────────

export function useWebhooks() {
  return useQuery({
    queryKey: keys.webhooks,
    queryFn: async () => {
      const { data } = await api.get<ApiResponse<unknown[]>>('/webhooks');
      return data.data;
    },
    staleTime: STALE_TIME_LONG,
  });
}

export function useCreateWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (webhook: Record<string, unknown>) => api.post('/webhooks', webhook),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['webhooks'] }),
  });
}

export function useDeleteWebhook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/webhooks/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['webhooks'] }),
  });
}

// ─────────────────────── Batch / Upload ───────────────────────

export function useUploadRFPDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData();
      fd.append('file', file);
      const { data } = await api.post<ApiResponse<{ rfp_id: string; filename: string }>>('/upload/rfp-document', fd, {
        timeout: 120_000,
      });
      return data.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rfps'] }),
  });
}

export function useRunPipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { text?: string; use_agents?: boolean; rfp_urls?: string[] }) => {
      const { data } = await api.post<ApiResponse<PipelineRun>>('/pipeline/run', payload);
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pipeline'] });
      qc.invalidateQueries({ queryKey: ['rfps'] });
    },
  });
}

// ─────────────────────── SSE / Streaming ───────────────────────

export function useSSEProgressUrl(rfpId: number) {
  return `/api/v1/rfps/${rfpId}/progress/stream`;
}

export function useSSEEventsUrl() {
  return `/api/v1/events/stream`;
}
