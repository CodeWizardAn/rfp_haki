import type {
  CatalogProduct,
  TenderRequirement,
  AutoFilledResponse,
  TenderPricingAnalytics,
  HistoricalTender,
  HistoricalPrice,
} from '@/types';

// ─── Mock Data: Product Catalog with OEM + Vendor Pool ───

const CATALOG_PRODUCTS: CatalogProduct[] = [
  {
    id: 1,
    sku: 'HAK-XLPE-240',
    name: 'XLPE Insulated Power Cable 240mm²',
    description: '3-core XLPE insulated, PVC sheathed, armoured power cable',
    category: 'Power Cables',
    subcategory: 'XLPE',
    oem: 'Polycab India Ltd',
    brand: 'Polycab',
    unit_price: 2450,
    currency: 'INR',
    unit_of_measure: 'meter',
    specifications: { cores: 3, size_mm2: 240, voltage_kv: 11, armoured: true },
    certifications: ['IS 7098', 'IEC 60502', 'BIS'],
    is_active: true,
    vendors: [
      { vendor_id: 1, name: 'Polycab India Ltd', tier: 'platinum', rating: 4.8, unit_price: 2450, lead_time_days: 14, moq: 500, on_time_delivery_rate: 96, quality_score: 95, last_quoted_at: '2026-01-15' },
      { vendor_id: 2, name: 'Havells India Ltd', tier: 'platinum', rating: 4.7, unit_price: 2520, lead_time_days: 12, moq: 300, on_time_delivery_rate: 94, quality_score: 93, last_quoted_at: '2026-01-20' },
      { vendor_id: 3, name: 'Finolex Cables', tier: 'gold', rating: 4.5, unit_price: 2380, lead_time_days: 18, moq: 1000, on_time_delivery_rate: 91, quality_score: 90, last_quoted_at: '2026-01-10' },
    ],
    price_history: [
      { date: '2025-03-01', price: 2100, vendor_name: 'Polycab', vendor_id: 1, tender_id: 'T-2025-001', tender_title: 'MSEDCL HT Cable Supply', quantity: 5000, outcome: 'won' },
      { date: '2025-06-15', price: 2250, vendor_name: 'Polycab', vendor_id: 1, tender_id: 'T-2025-014', tender_title: 'PGCIL Transmission Line', quantity: 8000, outcome: 'won' },
      { date: '2025-09-20', price: 2350, vendor_name: 'Havells', vendor_id: 2, tender_id: 'T-2025-028', tender_title: 'NHPC Cable Package', quantity: 3000, outcome: 'lost' },
      { date: '2025-12-01', price: 2420, vendor_name: 'Polycab', vendor_id: 1, tender_id: 'T-2025-041', tender_title: 'BSES Distribution Upgrade', quantity: 6000, outcome: 'won' },
      { date: '2026-01-15', price: 2450, vendor_name: 'Polycab', vendor_id: 1, tender_id: 'T-2026-003', tender_title: 'Kerala KSEB Expansion', quantity: 4000, outcome: 'pending' },
    ],
    tags: ['XLPE', 'power', 'armoured', '11kV'],
  },
  {
    id: 2,
    sku: 'HAK-XLPE-400',
    name: 'XLPE Insulated Power Cable 400mm²',
    description: '3-core XLPE insulated, PVC sheathed, armoured power cable',
    category: 'Power Cables',
    subcategory: 'XLPE',
    oem: 'Havells India Ltd',
    brand: 'Havells',
    unit_price: 3120,
    currency: 'INR',
    unit_of_measure: 'meter',
    specifications: { cores: 3, size_mm2: 400, voltage_kv: 33, armoured: true },
    certifications: ['IS 7098', 'IEC 60502', 'BIS', 'NABL'],
    is_active: true,
    vendors: [
      { vendor_id: 2, name: 'Havells India Ltd', tier: 'platinum', rating: 4.7, unit_price: 3120, lead_time_days: 16, moq: 200, on_time_delivery_rate: 94, quality_score: 93, last_quoted_at: '2026-01-22' },
      { vendor_id: 1, name: 'Polycab India Ltd', tier: 'platinum', rating: 4.8, unit_price: 3200, lead_time_days: 14, moq: 300, on_time_delivery_rate: 96, quality_score: 95, last_quoted_at: '2026-01-18' },
      { vendor_id: 4, name: 'KEI Industries', tier: 'gold', rating: 4.4, unit_price: 3050, lead_time_days: 20, moq: 500, on_time_delivery_rate: 89, quality_score: 88, last_quoted_at: '2025-12-28' },
    ],
    price_history: [
      { date: '2025-02-10', price: 2800, vendor_name: 'Havells', vendor_id: 2, tender_id: 'T-2025-002', tender_title: 'GETCO 400kV Substation', quantity: 2000, outcome: 'won' },
      { date: '2025-05-22', price: 2900, vendor_name: 'KEI', vendor_id: 4, tender_id: 'T-2025-011', tender_title: 'APTRANSCO Line Extension', quantity: 4000, outcome: 'lost' },
      { date: '2025-08-15', price: 3000, vendor_name: 'Havells', vendor_id: 2, tender_id: 'T-2025-023', tender_title: 'MPPTCL Cable Supply', quantity: 1500, outcome: 'won' },
      { date: '2025-11-10', price: 3080, vendor_name: 'Havells', vendor_id: 2, tender_id: 'T-2025-037', tender_title: 'Adani Green Energy', quantity: 6000, outcome: 'won' },
      { date: '2026-01-22', price: 3120, vendor_name: 'Havells', vendor_id: 2, tender_id: 'T-2026-005', tender_title: 'TANGEDCO Upgrade', quantity: 3000, outcome: 'pending' },
    ],
    tags: ['XLPE', 'power', 'armoured', '33kV', 'HT'],
  },
  {
    id: 3,
    sku: 'HAK-PVC-16C',
    name: 'PVC Control Cable 16-core 1.5mm²',
    description: 'Multi-core PVC insulated control cable',
    category: 'Control Cables',
    subcategory: 'PVC',
    oem: 'Finolex Cables Ltd',
    brand: 'Finolex',
    unit_price: 890,
    currency: 'INR',
    unit_of_measure: 'meter',
    specifications: { cores: 16, size_mm2: 1.5, voltage_kv: 1.1, armoured: false },
    certifications: ['IS 1554', 'IEC 60227', 'BIS'],
    is_active: true,
    vendors: [
      { vendor_id: 3, name: 'Finolex Cables', tier: 'gold', rating: 4.5, unit_price: 890, lead_time_days: 10, moq: 1000, on_time_delivery_rate: 91, quality_score: 90, last_quoted_at: '2026-01-25' },
      { vendor_id: 5, name: 'RR Kabel', tier: 'silver', rating: 4.2, unit_price: 860, lead_time_days: 12, moq: 500, on_time_delivery_rate: 87, quality_score: 85, last_quoted_at: '2026-01-12' },
      { vendor_id: 1, name: 'Polycab India Ltd', tier: 'platinum', rating: 4.8, unit_price: 920, lead_time_days: 8, moq: 200, on_time_delivery_rate: 96, quality_score: 95, last_quoted_at: '2026-01-28' },
    ],
    price_history: [
      { date: '2025-04-01', price: 950, vendor_name: 'Finolex', vendor_id: 3, tender_id: 'T-2025-005', tender_title: 'BHEL Instrumentation', quantity: 10000, outcome: 'won' },
      { date: '2025-07-10', price: 930, vendor_name: 'RR Kabel', vendor_id: 5, tender_id: 'T-2025-017', tender_title: 'NTPC Barh Phase II', quantity: 5000, outcome: 'lost' },
      { date: '2025-10-05', price: 910, vendor_name: 'Finolex', vendor_id: 3, tender_id: 'T-2025-031', tender_title: 'IOCL Refinery Control', quantity: 8000, outcome: 'won' },
      { date: '2026-01-05', price: 890, vendor_name: 'Finolex', vendor_id: 3, tender_id: 'T-2026-001', tender_title: 'GAIL Pipeline Control', quantity: 12000, outcome: 'pending' },
    ],
    tags: ['PVC', 'control', '16-core', 'instrumentation'],
  },
  {
    id: 4,
    sku: 'HAK-FR-25',
    name: 'FR Insulated Cable 25mm²',
    description: 'Flame retardant, low smoke, halogen-free cable',
    category: 'Fire Safety Cables',
    subcategory: 'FRLS',
    oem: 'KEI Industries Ltd',
    brand: 'KEI',
    unit_price: 1680,
    currency: 'INR',
    unit_of_measure: 'meter',
    specifications: { cores: 4, size_mm2: 25, voltage_kv: 1.1, flame_retardant: true, halogen_free: true },
    certifications: ['IS 7098', 'IEC 60332', 'BS 6387', 'BIS'],
    is_active: true,
    vendors: [
      { vendor_id: 4, name: 'KEI Industries', tier: 'gold', rating: 4.4, unit_price: 1680, lead_time_days: 15, moq: 1000, on_time_delivery_rate: 89, quality_score: 88, last_quoted_at: '2026-01-20' },
      { vendor_id: 2, name: 'Havells India Ltd', tier: 'platinum', rating: 4.7, unit_price: 1750, lead_time_days: 10, moq: 500, on_time_delivery_rate: 94, quality_score: 93, last_quoted_at: '2026-01-18' },
      { vendor_id: 6, name: 'Universal Cables', tier: 'silver', rating: 4.1, unit_price: 1620, lead_time_days: 22, moq: 2000, on_time_delivery_rate: 85, quality_score: 82, last_quoted_at: '2025-12-15' },
    ],
    price_history: [
      { date: '2025-01-15', price: 1380, vendor_name: 'KEI', vendor_id: 4, tender_id: 'T-2025-000', tender_title: 'Metro Phase III Tunnel', quantity: 15000, outcome: 'won' },
      { date: '2025-04-20', price: 1450, vendor_name: 'KEI', vendor_id: 4, tender_id: 'T-2025-006', tender_title: 'Airport Terminal 3 Build', quantity: 8000, outcome: 'won' },
      { date: '2025-07-25', price: 1520, vendor_name: 'Havells', vendor_id: 2, tender_id: 'T-2025-018', tender_title: 'Hospital Safety Upgrade', quantity: 3000, outcome: 'lost' },
      { date: '2025-10-30', price: 1600, vendor_name: 'KEI', vendor_id: 4, tender_id: 'T-2025-033', tender_title: 'Data Center Fire Safety', quantity: 10000, outcome: 'won' },
      { date: '2026-01-20', price: 1680, vendor_name: 'KEI', vendor_id: 4, tender_id: 'T-2026-004', tender_title: 'High-rise Complex Wiring', quantity: 20000, outcome: 'pending' },
    ],
    tags: ['FR', 'FRLS', 'fire-safety', 'halogen-free'],
  },
  {
    id: 5,
    sku: 'HAK-ACSR-150',
    name: 'ACSR Conductor 150mm² (Panther)',
    description: 'Aluminium Conductor Steel Reinforced – Panther equivalent',
    category: 'Overhead Conductors',
    subcategory: 'ACSR',
    oem: 'Sterlite Technologies',
    brand: 'Sterlite',
    unit_price: 420,
    currency: 'INR',
    unit_of_measure: 'meter',
    specifications: { material: 'Aluminium/Steel', size_mm2: 150, stranding: '30/7', breaking_load_kn: 68 },
    certifications: ['IS 398', 'IEC 61089', 'BIS'],
    is_active: true,
    vendors: [
      { vendor_id: 7, name: 'Sterlite Technologies', tier: 'gold', rating: 4.3, unit_price: 420, lead_time_days: 21, moq: 10000, on_time_delivery_rate: 88, quality_score: 87, last_quoted_at: '2026-01-08' },
      { vendor_id: 8, name: 'Apar Industries', tier: 'gold', rating: 4.3, unit_price: 410, lead_time_days: 25, moq: 15000, on_time_delivery_rate: 86, quality_score: 86, last_quoted_at: '2025-12-20' },
    ],
    price_history: [
      { date: '2025-03-10', price: 380, vendor_name: 'Sterlite', vendor_id: 7, tender_id: 'T-2025-003', tender_title: 'PGCIL 765kV Line', quantity: 50000, outcome: 'won' },
      { date: '2025-06-20', price: 395, vendor_name: 'Apar', vendor_id: 8, tender_id: 'T-2025-013', tender_title: 'UPPTCL Distribution', quantity: 30000, outcome: 'lost' },
      { date: '2025-09-15', price: 405, vendor_name: 'Sterlite', vendor_id: 7, tender_id: 'T-2025-027', tender_title: 'RVPNL Rajasthan Grid', quantity: 40000, outcome: 'won' },
      { date: '2026-01-08', price: 420, vendor_name: 'Sterlite', vendor_id: 7, tender_id: 'T-2026-002', tender_title: 'Green Energy Corridor', quantity: 60000, outcome: 'pending' },
    ],
    tags: ['ACSR', 'overhead', 'conductor', 'Panther'],
  },
];

// ─── Mock: Current Tender with Auto-Fill ───

const MOCK_TENDER_REQUIREMENTS: TenderRequirement[] = [
  { id: 1, line_no: 1, item_description: 'HT XLPE Cable 3C x 240 sq mm, 11kV grade, armoured', specifications: '3-core, XLPE insulated, IS 7098 Part 1, PVC outer sheath, galvanised strip armoured', quantity: 5000, unit: 'meters', delivery_timeline: '60 days', mandatory_certs: ['IS 7098', 'BIS'] },
  { id: 2, line_no: 2, item_description: 'HT XLPE Cable 3C x 400 sq mm, 33kV grade, armoured', specifications: '3-core, XLPE insulated, IS 7098 Part 1, 33kV grade, copper conductor', quantity: 2000, unit: 'meters', delivery_timeline: '90 days', mandatory_certs: ['IS 7098', 'IEC 60502', 'BIS'] },
  { id: 3, line_no: 3, item_description: 'Control Cable 16C x 1.5 sq mm, PVC insulated', specifications: '16-core, PVC insulated, IS 1554, unarmoured, for instrumentation', quantity: 8000, unit: 'meters', delivery_timeline: '45 days', mandatory_certs: ['IS 1554', 'BIS'] },
  { id: 4, line_no: 4, item_description: 'FR Cable 4C x 25 sq mm, FRLS grade', specifications: '4-core, flame retardant, low smoke halogen free, IEC 60332', quantity: 10000, unit: 'meters', delivery_timeline: '75 days', mandatory_certs: ['IEC 60332', 'BS 6387'] },
  { id: 5, line_no: 5, item_description: 'ACSR Conductor Panther equivalent 150 sq mm', specifications: 'Aluminium conductor steel reinforced, IS 398, 30/7 stranding', quantity: 25000, unit: 'meters', delivery_timeline: '120 days', mandatory_certs: ['IS 398', 'IEC 61089'] },
];

// ─── Auto-fill engine: matches tender LHS → catalog RHS ───

function computeWinProbability(priceHistory: HistoricalPrice[], currentPrice: number): number {
  const completedTenders = priceHistory.filter((h) => h.outcome === 'won' || h.outcome === 'lost');
  if (completedTenders.length === 0) return 50;

  const wonTenders = completedTenders.filter((h) => h.outcome === 'won');
  const baseWinRate = (wonTenders.length / completedTenders.length) * 100;

  // Price deviation factor: if current price is much higher than historical avg, lower probability
  const avgHistPrice = completedTenders.reduce((s, h) => s + h.price, 0) / completedTenders.length;
  const priceDelta = ((currentPrice - avgHistPrice) / avgHistPrice) * 100;

  // Every 5% above avg → lose 8% win probability; every 5% below → gain 5%
  let adjustment = 0;
  if (priceDelta > 0) {
    adjustment = -(priceDelta / 5) * 8;
  } else {
    adjustment = -(priceDelta / 5) * 5;
  }

  return Math.max(5, Math.min(98, Math.round(baseWinRate + adjustment)));
}

function computeRiskLevel(winProb: number, priceChangePct: number): 'low' | 'medium' | 'high' | 'critical' {
  if (winProb < 25 || priceChangePct > 30) return 'critical';
  if (winProb < 45 || priceChangePct > 20) return 'high';
  if (winProb < 65 || priceChangePct > 10) return 'medium';
  return 'low';
}

function computeRiskFactors(product: CatalogProduct, currentPrice: number, winProb: number): string[] {
  const factors: string[] = [];
  const history = product.price_history.filter((h) => h.outcome !== 'pending');
  if (history.length === 0) return ['No historical data available'];

  const avgPrice = history.reduce((s, h) => s + h.price, 0) / history.length;
  const pctChange = ((currentPrice - avgPrice) / avgPrice) * 100;

  if (pctChange > 15) factors.push(`Price ${pctChange.toFixed(0)}% above historical average (₹${avgPrice.toFixed(0)}/unit)`);
  if (pctChange > 25) factors.push('Significant price inflation – competitors may undercut');

  const recentLosses = history.filter((h) => h.outcome === 'lost');
  if (recentLosses.length > 0) factors.push(`Lost ${recentLosses.length} of ${history.length} past tenders for this item`);

  if (winProb < 40) factors.push('Win probability below 40% – consider price reduction');
  if (product.vendors.length < 2) factors.push('Single vendor dependency – supply risk');

  const bestVendorPrice = Math.min(...product.vendors.map((v) => v.unit_price));
  if (currentPrice > bestVendorPrice * 1.1) factors.push(`Better vendor pricing available (₹${bestVendorPrice}/unit)`);

  if (factors.length === 0) factors.push('No significant risk factors identified');
  return factors;
}

function autoFillRFP(requirements: TenderRequirement[]): AutoFilledResponse[] {
  // Simple matching: map each requirement to the best catalog product
  const mapping: [number, number][] = [
    [1, 1], // HT XLPE 240 → product 1
    [2, 2], // HT XLPE 400 → product 2
    [3, 3], // Control Cable 16C → product 3
    [4, 4], // FR Cable 25mm → product 4
    [5, 5], // ACSR 150 → product 5
  ];

  return mapping.map(([reqId, prodId]) => {
    const req = requirements.find((r) => r.id === reqId)!;
    const product = CATALOG_PRODUCTS.find((p) => p.id === prodId)!;

    const completedHistory = product.price_history.filter((h) => h.outcome !== 'pending');
    const avgHistPrice = completedHistory.length > 0
      ? completedHistory.reduce((s, h) => s + h.price, 0) / completedHistory.length
      : product.unit_price;

    const currentPrice = product.unit_price;
    const priceChangePct = ((currentPrice - avgHistPrice) / avgHistPrice) * 100;
    const winProb = computeWinProbability(product.price_history, currentPrice);
    const riskLevel = computeRiskLevel(winProb, Math.abs(priceChangePct));
    const riskFactors = computeRiskFactors(product, currentPrice, winProb);

    // Determine price trend
    const prices = product.price_history.map((h) => h.price);
    let priceTrend: 'rising' | 'falling' | 'stable' = 'stable';
    if (prices.length >= 2) {
      const recent = prices[prices.length - 1] ?? 0;
      const older = prices[0] ?? 1;
      const change = ((recent - older) / older) * 100;
      if (change > 3) priceTrend = 'rising';
      else if (change < -3) priceTrend = 'falling';
    }

    // Recommended price: slightly undercut if win probability is low
    let recommendedPrice = currentPrice;
    if (winProb < 50) recommendedPrice = Math.round(currentPrice * 0.95);
    else if (winProb < 70) recommendedPrice = Math.round(currentPrice * 0.98);

    return {
      requirement_id: req.id,
      requirement: req,
      matched_product: product,
      match_score: [95, 93, 91, 88, 90][reqId - 1] ?? 85,
      confidence: winProb > 65 ? 'high' : winProb > 40 ? 'medium' : 'low',
      prefilled_price: currentPrice,
      recommended_price: recommendedPrice,
      historical_avg_price: Math.round(avgHistPrice),
      price_trend: priceTrend,
      price_change_pct: Math.round(priceChangePct * 10) / 10,
      win_probability: winProb,
      risk_level: riskLevel,
      risk_factors: riskFactors,
      vendor_options: product.vendors,
      selected_vendor_id: product.vendors[0]?.vendor_id,
    };
  });
}

// ─── Mock Historical Tenders ───

const HISTORICAL_TENDERS: HistoricalTender[] = [
  { tender_id: 'T-2025-001', title: 'MSEDCL HT Cable Supply', date: '2025-03-01', total_value: 2500000, outcome: 'won', our_bid_value: 2500000, winning_bid_value: 2500000, line_item_count: 4 },
  { tender_id: 'T-2025-014', title: 'PGCIL Transmission Line', date: '2025-06-15', total_value: 2180000, outcome: 'won', our_bid_value: 2180000, winning_bid_value: 2180000, line_item_count: 3 },
  { tender_id: 'T-2025-023', title: 'MPPTCL Cable Supply', date: '2025-08-15', total_value: 1950000, outcome: 'won', our_bid_value: 1950000, winning_bid_value: 1950000, line_item_count: 5 },
  { tender_id: 'T-2025-028', title: 'NHPC Cable Package', date: '2025-09-20', total_value: 2100000, outcome: 'lost', our_bid_value: 2100000, winning_bid_value: 1890000, competitor: 'Competitor A', line_item_count: 4 },
  { tender_id: 'T-2025-037', title: 'Adani Green Energy', date: '2025-11-10', total_value: 2800000, outcome: 'won', our_bid_value: 2800000, winning_bid_value: 2800000, line_item_count: 6 },
  { tender_id: 'T-2025-041', title: 'BSES Distribution Upgrade', date: '2025-12-01', total_value: 2100000, outcome: 'won', our_bid_value: 2100000, winning_bid_value: 2100000, line_item_count: 3 },
];

// ─── Service ───

export const tenderPricingService = {
  /** Get all catalog products with OEM + vendor pool */
  getCatalog: async (): Promise<CatalogProduct[]> => {
    // In production: const { data } = await api.get<ApiResponse<CatalogProduct[]>>('/catalog/products');
    return CATALOG_PRODUCTS;
  },

  /** Get catalog product by ID */
  getCatalogProduct: async (id: number): Promise<CatalogProduct | undefined> => {
    return CATALOG_PRODUCTS.find((p) => p.id === id);
  },

  /** Auto-fill RFP: LHS (tender requirements) → RHS (prefilled response from catalog) */
  autoFillTender: async (requirements: TenderRequirement[]): Promise<AutoFilledResponse[]> => {
    // In production: const { data } = await api.post<ApiResponse<AutoFilledResponse[]>>('/tender/auto-fill', { requirements });
    return autoFillRFP(requirements);
  },

  /** Get full tender pricing analytics with historical comparison */
  getTenderAnalytics: async (tenderId?: string): Promise<TenderPricingAnalytics> => {
    const lineItems = autoFillRFP(MOCK_TENDER_REQUIREMENTS);
    const totalValue = lineItems.reduce((s, li) => s + li.prefilled_price * li.requirement.quantity, 0);
    const avgHistValue = lineItems.reduce((s, li) => s + li.historical_avg_price * li.requirement.quantity, 0);
    const priceDeltaPct = ((totalValue - avgHistValue) / avgHistValue) * 100;
    const overallWinProb = Math.round(lineItems.reduce((s, li) => s + li.win_probability, 0) / lineItems.length);

    return {
      tender_id: tenderId || 'T-2026-010',
      tender_title: 'MSEDCL Cable & Conductor Supply 2026-Q1',
      total_value: totalValue,
      historical_avg_value: avgHistValue,
      price_delta_pct: Math.round(priceDeltaPct * 10) / 10,
      overall_win_probability: overallWinProb,
      risk_summary: {
        low: lineItems.filter((li) => li.risk_level === 'low').length,
        medium: lineItems.filter((li) => li.risk_level === 'medium').length,
        high: lineItems.filter((li) => li.risk_level === 'high').length,
        critical: lineItems.filter((li) => li.risk_level === 'critical').length,
      },
      line_items: lineItems,
      historical_tenders: HISTORICAL_TENDERS,
    };
  },

  /** Get mock tender requirements (simulating PDF extraction) */
  getTenderRequirements: async (): Promise<TenderRequirement[]> => {
    return MOCK_TENDER_REQUIREMENTS;
  },

  /** Get historical tenders for comparison */
  getHistoricalTenders: async (): Promise<HistoricalTender[]> => {
    return HISTORICAL_TENDERS;
  },
};
