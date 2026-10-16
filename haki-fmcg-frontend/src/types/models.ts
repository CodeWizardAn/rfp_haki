// ============================================
// Haki — TypeScript Type Definitions
// Matching backend database/models.py
// ============================================

// --- Enums / Union Types ---

export type RFPStatus =
  | 'draft'
  | 'scraped'
  | 'extracting'
  | 'analyzing'
  | 'analyzed'
  | 'matching'
  | 'pricing'
  | 'review'
  | 'submitted'
  | 'won'
  | 'lost'
  | 'cancelled';

export type Priority = 'critical' | 'high' | 'medium' | 'low';

export type BidStatus =
  | 'draft'
  | 'in_review'
  | 'approved'
  | 'rejected'
  | 'submitted'
  | 'won'
  | 'lost';

export type PipelineStage =
  | 'intake'
  | 'extraction'
  | 'matching'
  | 'pricing'
  | 'compliance'
  | 'review'
  | 'approval'
  | 'submission';

export type PipelineStageStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export type AgentType = 'master' | 'sales' | 'technical' | 'pricing';

export type VendorTier = 'platinum' | 'gold' | 'silver' | 'bronze' | 'new';

export type ComplianceStatus = 'compliant' | 'non_compliant' | 'partial' | 'pending_review';

// --- Core Models ---

export interface RFP {
  id: number;
  rfp_id: string;
  title: string;
  description: string;
  source_url?: string;
  source_file?: string;
  extracted_text?: string;
  submission_deadline?: string;
  budget_amount?: number;
  currency: string;
  status: RFPStatus;
  priority: Priority;
  tags: string[];
  matched_products: Record<string, unknown>;
  pricing_data: Record<string, unknown>;
  requirements: RFPRequirement[];
  bids: Bid[];
  created_at: string;
  updated_at: string;
}

export interface RFPRequirement {
  id: number;
  rfp_id: number;
  section: string;
  requirement_text: string;
  category: string;
  is_mandatory: boolean;
  compliance_status: ComplianceStatus;
  matched_specs: Record<string, unknown>;
  notes?: string;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  description: string;
  category: string;
  subcategory?: string;
  brand: string;
  manufacturer: string;
  unit_price: number;
  currency: string;
  unit_of_measure: string;
  min_order_quantity: number;
  lead_time_days: number;
  specifications: Record<string, unknown>;
  certifications: string[];
  is_active: boolean;
  stock_quantity: number;
  vendor_id?: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface Vendor {
  id: number;
  vendor_id: string;
  name: string;
  contact_person: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  website?: string;
  tier: VendorTier;
  rating: number;
  total_orders: number;
  on_time_delivery_rate: number;
  quality_score: number;
  compliance_score: number;
  is_active: boolean;
  categories: string[];
  certifications: string[];
  payment_terms: string;
  notes?: string;
  products: Product[];
  created_at: string;
  updated_at: string;
}

export interface Bid {
  id: number;
  bid_id: string;
  rfp_id: number;
  title: string;
  description: string;
  status: BidStatus;
  total_value: number;
  currency: string;
  discount_percentage: number;
  validity_days: number;
  delivery_timeline: string;
  payment_terms: string;
  technical_score: number;
  commercial_score: number;
  compliance_score: number;
  overall_score: number;
  items: BidItem[];
  approvals: BidApproval[];
  submitted_at?: string;
  approved_at?: string;
  created_by: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface BidItem {
  id: number;
  bid_id: number;
  product_id: number;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  discount: number;
  total_price: number;
  notes?: string;
}

export interface BidApproval {
  id: number;
  bid_id: number;
  approver_name: string;
  approver_role: string;
  status: 'pending' | 'approved' | 'rejected';
  comments?: string;
  decided_at?: string;
  created_at: string;
}

export interface ProductMatch {
  id: number;
  rfp_requirement_id: number;
  product_id: number;
  product: Product;
  match_score: number;
  semantic_score: number;
  keyword_score: number;
  spec_score: number;
  confidence: 'high' | 'medium' | 'low';
  matched_attributes: string[];
  gaps: string[];
  notes?: string;
  created_at: string;
}

// --- Pipeline ---

export interface PipelineRun {
  id: number;
  pipeline_id: string;
  rfp_id: number;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  current_stage: PipelineStage;
  stages: PipelineStageResult[];
  progress_percentage: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  metadata: Record<string, unknown>;
}

export interface PipelineStageResult {
  stage: PipelineStage;
  status: PipelineStageStatus;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  result_summary?: string;
  error?: string;
  metrics: Record<string, unknown>;
}

// --- Agents ---

export interface AgentConversation {
  id: number;
  conversation_id: string;
  agent_type: AgentType;
  rfp_id?: number;
  messages: AgentMessage[];
  status: 'active' | 'completed' | 'error';
  started_at: string;
  completed_at?: string;
}

export interface AgentMessage {
  id: number;
  role: 'user' | 'agent' | 'system';
  content: string;
  agent_type?: AgentType;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface AgentStatus {
  agent_type: AgentType;
  is_active: boolean;
  current_task?: string;
  tasks_completed: number;
  tasks_failed: number;
  avg_response_time_ms: number;
  last_active: string;
}

// --- Analytics ---

export interface DashboardStats {
  active_rfps: number;
  total_bid_value: number;
  products_count: number;
  active_vendors: number;
  pipeline_health: 'healthy' | 'warning' | 'error';
  rfp_trend: TrendPoint[];
  bid_trend: TrendPoint[];
}

export interface TrendPoint {
  date: string;
  value: number;
}

export interface AnalyticsMetric {
  label: string;
  value: number;
  change: number;
  change_type: 'increase' | 'decrease' | 'stable';
  period: string;
}

export interface RFPAnalytics {
  total: number;
  by_status: Record<RFPStatus, number>;
  avg_processing_time_hours: number;
  success_rate: number;
  monthly_trend: TrendPoint[];
}

export interface BidAnalytics {
  total: number;
  by_status: Record<BidStatus, number>;
  total_value: number;
  win_rate: number;
  avg_score: number;
  monthly_values: TrendPoint[];
}

export interface WinLossBidPrediction {
  bid_id?: string;
  status?: string;
  predicted_win_probability: number;
  predicted_loss_probability: number;
  model_source: string;
  drivers: string[];
}

export interface WinLossPrediction {
  resolved_bids: number;
  won_count: number;
  lost_count: number;
  current_win_rate: number;
  current_win_loss_ratio: string;
  target_bid?: WinLossBidPrediction | null;
  portfolio_forecast: {
    open_bids: number;
    expected_wins: number;
    expected_losses: number;
    predicted_win_loss_ratio: string;
    average_win_probability: number;
    top_candidates: WinLossBidPrediction[];
  };
  model: {
    type: string;
    confidence: number;
    training_samples: number;
    generated_at: string;
  };
}

// --- Compliance & Audit ---

export interface ComplianceRule {
  id: number;
  rule_id: string;
  name: string;
  description: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  is_active: boolean;
}

export interface ComplianceCheck {
  id: number;
  rfp_id: number;
  bid_id?: number;
  rule_id: string;
  status: ComplianceStatus;
  details: string;
  checked_at: string;
}

export interface AuditLogEntry {
  id: number;
  action: string;
  entity_type: string;
  entity_id: string;
  user: string;
  details: Record<string, unknown>;
  ip_address?: string;
  timestamp: string;
}

// --- Auth ---

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'analyst' | 'viewer';
  avatar_url?: string;
  permissions: string[];
  is_active: boolean;
  last_login?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// --- API Response Wrappers ---

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, unknown>;
}

// --- Notification ---

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  action_url?: string;
  created_at: string;
}

// --- Product Catalog (OEM + Vendor Pool) ---

export interface CatalogProduct {
  id: number;
  sku: string;
  name: string;
  description: string;
  category: string;
  subcategory?: string;
  oem: string;                     // Original Equipment Manufacturer
  brand: string;
  unit_price: number;
  currency: string;
  unit_of_measure: string;
  specifications: Record<string, unknown>;
  certifications: string[];
  is_active: boolean;
  vendors: CatalogVendor[];        // Multiple vendors per product
  price_history: HistoricalPrice[];
  tags: string[];
}

export interface CatalogVendor {
  vendor_id: number;
  name: string;
  tier: VendorTier;
  rating: number;
  unit_price: number;
  lead_time_days: number;
  moq: number;                     // Minimum Order Quantity
  on_time_delivery_rate: number;
  quality_score: number;
  last_quoted_at?: string;
}

export interface HistoricalPrice {
  date: string;
  price: number;
  vendor_name: string;
  vendor_id: number;
  tender_id?: string;
  tender_title?: string;
  quantity: number;
  outcome: 'won' | 'lost' | 'pending' | 'no_bid';
}

// --- RFP Auto-Fill (LHS Tender Req → RHS Prefilled) ---

export interface TenderRequirement {
  id: number;
  line_no: number;
  item_description: string;
  specifications: string;
  quantity: number;
  unit: string;
  delivery_timeline?: string;
  mandatory_certs?: string[];
}

export interface AutoFilledResponse {
  requirement_id: number;
  requirement: TenderRequirement;   // LHS: Original tender requirement
  matched_product: CatalogProduct;  // RHS: Best match from catalog
  match_score: number;              // 0–100
  confidence: 'high' | 'medium' | 'low';
  prefilled_price: number;
  recommended_price: number;        // AI-optimized price
  historical_avg_price: number;
  price_trend: 'rising' | 'falling' | 'stable';
  price_change_pct: number;         // e.g., -16% from 25L to 21L
  win_probability: number;          // 0–100, based on historical data
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: string[];
  vendor_options: CatalogVendor[];  // OEM/vendor pool for this item
  selected_vendor_id?: number;
  notes?: string;
}

export interface TenderPricingAnalytics {
  tender_id: string;
  tender_title: string;
  total_value: number;
  historical_avg_value: number;
  price_delta_pct: number;          // Current vs historical
  overall_win_probability: number;
  risk_summary: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  line_items: AutoFilledResponse[];
  historical_tenders: HistoricalTender[];
}

export interface HistoricalTender {
  tender_id: string;
  title: string;
  date: string;
  total_value: number;
  outcome: 'won' | 'lost' | 'no_bid';
  our_bid_value: number;
  winning_bid_value?: number;
  competitor?: string;
  line_item_count: number;
}

// --- Activity Feed ---

export interface ActivityItem {
  id: number;
  type: 'rfp_uploaded' | 'bid_created' | 'vendor_rated' | 'product_matched' | 'approval_action' | 'pipeline_run' | 'agent_action';
  title: string;
  description: string;
  entity_type: string;
  entity_id: string;
  user?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}
