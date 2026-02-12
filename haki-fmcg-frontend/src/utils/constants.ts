import type { RFPStatus, BidStatus, Priority, PipelineStage, AgentType, VendorTier } from '@/types';

// --- Color mappings for statuses ---

export const RFP_STATUS_COLORS: Record<RFPStatus, { bg: string; text: string; dot: string }> = {
  draft: { bg: 'bg-steel-slate/50', text: 'text-muted-silver', dot: 'bg-muted-silver' },
  extracting: { bg: 'bg-electric-cyan-dim', text: 'text-electric-cyan', dot: 'bg-electric-cyan' },
  matching: { bg: 'bg-violet-dim', text: 'text-violet-pulse', dot: 'bg-violet-pulse' },
  pricing: { bg: 'bg-amber-dim', text: 'text-amber-glow', dot: 'bg-amber-glow' },
  review: { bg: 'bg-rose-pink/15', text: 'text-rose-pink', dot: 'bg-rose-pink' },
  submitted: { bg: 'bg-electric-cyan-dim', text: 'text-electric-cyan', dot: 'bg-electric-cyan' },
  won: { bg: 'bg-emerald-dim', text: 'text-neon-emerald', dot: 'bg-neon-emerald' },
  lost: { bg: 'bg-coral-dim', text: 'text-coral-flame', dot: 'bg-coral-flame' },
  cancelled: { bg: 'bg-steel-slate/30', text: 'text-muted-silver', dot: 'bg-muted-silver' },
};

export const BID_STATUS_COLORS: Record<BidStatus, { bg: string; text: string }> = {
  draft: { bg: '#8892B0', text: 'text-muted-silver' },
  in_review: { bg: '#00D4FF', text: 'text-electric-cyan' },
  approved: { bg: '#00E68A', text: 'text-neon-emerald' },
  rejected: { bg: '#FF4757', text: 'text-coral-flame' },
  submitted: { bg: '#00D4FF', text: 'text-electric-cyan' },
  won: { bg: '#FFB224', text: 'text-amber-glow' },
  lost: { bg: '#1E2642', text: 'text-muted-silver' },
};

export const PRIORITY_COLORS: Record<Priority, { bg: string; text: string }> = {
  critical: { bg: 'bg-coral-dim', text: 'text-coral-flame' },
  high: { bg: 'bg-amber-dim', text: 'text-amber-glow' },
  medium: { bg: 'bg-electric-cyan-dim', text: 'text-electric-cyan' },
  low: { bg: 'bg-steel-slate/50', text: 'text-muted-silver' },
};

export const PIPELINE_STAGE_LABELS: Record<PipelineStage, string> = {
  intake: 'Intake',
  extraction: 'Extraction',
  matching: 'Matching',
  pricing: 'Pricing',
  compliance: 'Compliance',
  review: 'Review',
  approval: 'Approval',
  submission: 'Submission',
};

export const AGENT_COLORS: Record<AgentType, { color: string; bg: string; label: string }> = {
  master: { color: '#7C3AED', bg: 'bg-violet-dim', label: 'Master Agent' },
  sales: { color: '#00D4FF', bg: 'bg-electric-cyan-dim', label: 'Sales Agent' },
  technical: { color: '#14B8A6', bg: 'bg-teal-depth/15', label: 'Technical Agent' },
  pricing: { color: '#FFB224', bg: 'bg-amber-dim', label: 'Pricing Agent' },
};

export const VENDOR_TIER_COLORS: Record<VendorTier, { color: string; label: string }> = {
  platinum: { color: '#E8ECF4', label: 'Platinum' },
  gold: { color: '#FFB224', label: 'Gold' },
  silver: { color: '#8892B0', label: 'Silver' },
  bronze: { color: '#CD7F32', label: 'Bronze' },
  new: { color: '#00D4FF', label: 'New' },
};

// --- API Endpoints ---

// Empty string = relative URLs via Vite proxy; set VITE_API_URL for direct access
export const API_BASE_URL: string =
  import.meta.env.VITE_API_URL !== undefined
    ? import.meta.env.VITE_API_URL
    : '';
export const PDF_SERVICE_URL = import.meta.env.VITE_PDF_URL || 'http://localhost:5000';
export const SPEC_SERVICE_URL = import.meta.env.VITE_SPEC_URL || 'http://localhost:5001';
export const VENDOR_SERVICE_URL = import.meta.env.VITE_VENDOR_URL || 'http://localhost:5005';
export const BID_SERVICE_URL = import.meta.env.VITE_BID_URL || 'http://localhost:5006';

// --- App Constants ---

export const ITEMS_PER_PAGE = 25;
export const STALE_TIME_SHORT = 30 * 1000; // 30s
export const STALE_TIME_LONG = 5 * 60 * 1000; // 5min
export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
export const TOAST_DURATION = 4000;

export const SIDEBAR_WIDTH = 240;
export const SIDEBAR_COLLAPSED_WIDTH = 64;
