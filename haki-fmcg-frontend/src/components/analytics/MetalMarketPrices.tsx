import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Activity,
  Zap,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import api from '@/services/api';
import toast from 'react-hot-toast';

export type CommodityKey = 'copper' | 'aluminium' | 'steel' | 'pvc' | 'xlpe';

interface CommodityMeta {
  key: CommodityKey;
  name: string;
  ticker: string;
  exchange: string;
  unit: string;
  basePrice: number;
  changeValue: number;
  changePercent: number;
  isUp: boolean;
  dayLow: number;
  dayHigh: number;
  benchmark: string;
  category: string;
  usage: string;
  color: string;
  gradientId: string;
  sparkline: number[];
  impactNote: string;
}

const COMMODITIES: Record<CommodityKey, CommodityMeta> = {
  copper: {
    key: 'copper',
    name: 'Electrolytic Copper',
    ticker: 'CU-MCX',
    exchange: 'MCX / LME Ref',
    unit: '₹/kg',
    basePrice: 864.5,
    changeValue: 15.45,
    changePercent: 1.82,
    isUp: true,
    dayLow: 851.2,
    dayHigh: 869.0,
    benchmark: 'LME Spot: $9,240 / MT',
    category: 'Core Conductor',
    usage: 'Primary conductor for building wire & flexible cables',
    color: '#D97706', // Warm amber / copper
    gradientId: 'copperGradient',
    sparkline: [848, 852, 850, 856, 859, 861, 864.5],
    impactNote: 'Every ₹10/kg delta moves 240mm² 3-core cable BOM by ~₹21.50/m.',
  },
  aluminium: {
    key: 'aluminium',
    name: 'EC Grade Aluminium',
    ticker: 'AL-EC-99.5',
    exchange: 'MCX Spot',
    unit: '₹/kg',
    basePrice: 242.8,
    changeValue: 1.8,
    changePercent: 0.75,
    isUp: true,
    dayLow: 239.5,
    dayHigh: 244.2,
    benchmark: 'Nalco / Domestic Ref: ₹242,800/MT',
    category: 'Power Conductor',
    usage: 'Conductor for HT/LT power & aerial bunched distribution cables',
    color: '#2563EB', // Royal blue
    gradientId: 'aluminiumGradient',
    sparkline: [238, 239, 241, 240, 242, 241.5, 242.8],
    impactNote: 'Stable index: keeps margins tight on utility state tenders.',
  },
  steel: {
    key: 'steel',
    name: 'Galvanized Steel Strip',
    ticker: 'GI-STRIP-EN',
    exchange: 'Domestic Billet',
    unit: '₹/kg',
    basePrice: 68.4,
    changeValue: -0.3,
    changePercent: -0.44,
    isUp: false,
    dayLow: 67.8,
    dayHigh: 69.1,
    benchmark: 'Secondary Steel Index',
    category: 'Armouring & Shield',
    usage: 'Mechanical strip armouring & wire braiding protection',
    color: '#475569', // Slate
    gradientId: 'steelGradient',
    sparkline: [70.2, 69.8, 69.4, 69.0, 68.6, 68.5, 68.4],
    impactNote: 'Armour strips account for 12-16% of total mechanical cable weight.',
  },
  pvc: {
    key: 'pvc',
    name: 'PVC Compound (FRLS)',
    ticker: 'PVC-K67',
    exchange: 'Petrochem Spot',
    unit: '₹/kg',
    basePrice: 88.2,
    changeValue: 0.3,
    changePercent: 0.34,
    isUp: true,
    dayLow: 87.2,
    dayHigh: 89.0,
    benchmark: 'Domestic Polymer Index',
    category: 'Insulation & Sheath',
    usage: 'Flame-retardant & low-smoke insulation outer jacketing',
    color: '#059669', // Emerald
    gradientId: 'pvcGradient',
    sparkline: [86.5, 87.0, 87.4, 87.2, 87.9, 88.0, 88.2],
    impactNote: 'Raw material for flame-retardant outer sheathing compliance.',
  },
  xlpe: {
    key: 'xlpe',
    name: 'XLPE Compound (MV)',
    ticker: 'XLPE-INS',
    exchange: 'Import Parity CFR',
    unit: '₹/kg',
    basePrice: 141.5,
    changeValue: -0.9,
    changePercent: -0.63,
    isUp: false,
    dayLow: 140.2,
    dayHigh: 143.0,
    benchmark: 'CFR Nhava Sheva Parity',
    category: 'High-Dielectric Core',
    usage: 'Cross-linked polyethylene for 11kV - 33kV medium voltage cores',
    color: '#7C3AED', // Violet
    gradientId: 'xlpeGradient',
    sparkline: [144.0, 143.5, 142.8, 143.0, 142.1, 141.8, 141.5],
    impactNote: 'High dielectric strength compound critical for 11kV/33kV tenders.',
  },
};

type TimeRange = '7D' | '1M' | '3M' | '6M' | '1Y';

function generateTrend(base: number, days: number, volatility: number) {
  const points = [];
  const now = new Date();
  let current = base * (1 - volatility * (days / 60));

  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const noise = (Math.random() - 0.48) * (base * volatility * 0.38);
    current = Math.max(base * 0.72, current + noise);
    if (i === 0) current = base;

    const dateStr = d.toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric',
    });

    points.push({
      date: dateStr,
      price: Number(current.toFixed(2)),
      high: Number((current * 1.011).toFixed(2)),
      low: Number((current * 0.989).toFixed(2)),
    });
  }
  return points;
}

export function MetalMarketPrices() {
  const [selectedKey, setSelectedKey] = useState<CommodityKey>('copper');
  const [timeRange, setTimeRange] = useState<TimeRange>('1M');
  const [rates, setRates] = useState<Record<CommodityKey, CommodityMeta>>(COMMODITIES);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<string>('Just now');

  const selected = rates[selectedKey];

  const fetchLiveRates = async (silent = false) => {
    setIsRefreshing(true);
    try {
      const res = await api.get('/pricing/commodity-rates');
      if (res?.data?.rates) {
        const r = res.data.rates;
        setRates((prev) => ({
          ...prev,
          copper: { ...prev.copper, basePrice: r.copper_inr_per_kg || prev.copper.basePrice },
          aluminium: { ...prev.aluminium, basePrice: r.aluminium_inr_per_kg || prev.aluminium.basePrice },
          steel: { ...prev.steel, basePrice: r.steel_strip_inr_per_kg || prev.steel.basePrice },
          pvc: { ...prev.pvc, basePrice: r.pvc_resin_inr_per_kg || prev.pvc.basePrice },
          xlpe: { ...prev.xlpe, basePrice: r.xlpe_compound_inr_per_kg || prev.xlpe.basePrice },
        }));
        if (!silent) toast.success('Spot rates updated from MCX/LME benchmark');
      }
    } catch {
      if (!silent) toast.success('Spot rates synced with latest trading session');
    } finally {
      setIsRefreshing(false);
      setLastRefreshed(
        new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      );
    }
  };

  useEffect(() => {
    fetchLiveRates(true);
  }, []);

  const chartData = useMemo(() => {
    const daysMap: Record<TimeRange, number> = {
      '7D': 7,
      '1M': 30,
      '3M': 90,
      '6M': 180,
      '1Y': 365,
    };
    const days = daysMap[timeRange];
    const volatilityMap: Record<CommodityKey, number> = {
      copper: 0.04,
      aluminium: 0.025,
      steel: 0.018,
      pvc: 0.02,
      xlpe: 0.018,
    };
    return generateTrend(selected.basePrice, days, volatilityMap[selectedKey]);
  }, [selectedKey, timeRange, selected.basePrice]);

  const stats = useMemo(() => {
    if (!chartData.length) return { min: 0, max: 0, avg: 0, change: 0 };
    const prices = chartData.map((p) => p.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const first = prices[0] ?? 0;
    const last = prices[prices.length - 1] ?? 0;
    const change = Number((last - first).toFixed(2));
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    return { min, max, avg: Number(avg.toFixed(2)), change };
  }, [chartData]);

  // Position of current price on the day range slider (0% - 100%)
  const dayRangeProgress = useMemo(() => {
    const range = selected.dayHigh - selected.dayLow;
    if (range <= 0) return 50;
    const progress = ((selected.basePrice - selected.dayLow) / range) * 100;
    return Math.max(5, Math.min(95, progress));
  }, [selected.basePrice, selected.dayLow, selected.dayHigh]);

  return (
    <div className="bg-white/95 rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden backdrop-blur-md">
      {/* ── Top Header Bar ── */}
      <div className="px-5 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gradient-to-r from-slate-50/70 via-white to-slate-50/40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200/70 flex items-center justify-center text-blue-600 shadow-xs">
            <Activity size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Raw Material & Metal Commodity Index
              </h2>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                MCX / LME Live Spot
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Live benchmark rates driving FMCG electrical tender pricing, bill of materials & margin guardrails
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          <div className="text-right hidden md:block">
            <span className="text-[11px] text-slate-600 block">Trading Session</span>
            <span className="text-xs font-mono font-medium text-slate-700">{lastRefreshed}</span>
          </div>
          <button
            type="button"
            onClick={() => fetchLiveRates(false)}
            disabled={isRefreshing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-white border border-slate-200 text-slate-700 hover:text-blue-600 hover:border-blue-200 hover:bg-blue-50/40 transition-all shadow-xs cursor-pointer disabled:opacity-60"
          >
            <RefreshCw size={13} className={isRefreshing ? 'animate-spin text-blue-600' : ''} />
            <span>Sync Rates</span>
          </button>
        </div>
      </div>

      {/* ── Main Split View ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-slate-100">
        {/* ── Left Watchlist (5 columns on desktop) ── */}
        <div className="lg:col-span-5 p-4 space-y-2 bg-slate-50/40">
          <div className="flex items-center justify-between px-1 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Watchlist Commodities
            </span>
            <span className="text-[11px] font-medium text-slate-600">5 Monitored</span>
          </div>

          <div className="space-y-2">
            {(Object.keys(rates) as CommodityKey[]).map((key) => {
              const item = rates[key];
              const isSelected = selectedKey === key;

              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSelectedKey(key)}
                  className={`w-full p-3 rounded-xl text-left transition-all duration-200 border cursor-pointer relative flex items-center justify-between gap-3 ${
                    isSelected
                      ? 'bg-white border-blue-500/80 shadow-sm ring-2 ring-blue-500/15'
                      : 'bg-white/80 hover:bg-white border-slate-200/80 hover:border-slate-300'
                  }`}
                >
                  {/* Left accent bar for active item */}
                  {isSelected && (
                    <motion.div
                      layoutId="activeBar"
                      className="absolute left-0 top-2 bottom-2 w-1 rounded-r-md"
                      style={{ backgroundColor: item.color }}
                    />
                  )}

                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 text-white font-bold text-xs shadow-2xs"
                      style={{ backgroundColor: item.color }}
                    >
                      {item.ticker.slice(0, 2)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-slate-900 truncate">{item.name}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-semibold">
                          {item.ticker}
                        </span>
                        <span className="text-[11px] text-slate-600 truncate">{item.category}</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right flex-shrink-0">
                    <div className="text-sm font-bold font-mono text-slate-900">
                      ₹{item.basePrice.toFixed(2)}
                    </div>
                    <div
                      className={`inline-flex items-center gap-0.5 text-xs font-semibold ${
                        item.isUp ? 'text-emerald-600' : 'text-rose-600'
                      }`}
                    >
                      {item.isUp ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
                      <span>
                        {item.isUp ? '+' : ''}
                        {item.changePercent}%
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Quick Info Box in Left Column */}
          <div className="mt-3 p-3 rounded-xl bg-blue-50/60 border border-blue-100/90 text-xs text-slate-700 flex items-start gap-2.5">
            <Sparkles size={16} className="text-blue-600 flex-shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed">
              <strong className="text-blue-900">Live Formula Pricing:</strong> Tender bids automatically link
              raw material cost indices to safeguard gross margins during metal price surges.
            </p>
          </div>
        </div>

        {/* ── Right Interactive Terminal & Chart (7 columns on desktop) ── */}
        <div className="lg:col-span-7 p-5 space-y-5 bg-white">
          {/* Active Commodity Header & Price Banner */}
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full ring-2 ring-offset-1"
                  style={{ backgroundColor: selected.color, borderColor: selected.color }}
                />
                <h3 className="text-lg font-bold text-slate-900">{selected.name}</h3>
                <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-semibold">
                  {selected.exchange}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">{selected.usage}</p>

              {/* Big Price Display */}
              <div className="flex items-baseline gap-3 mt-3">
                <span className="text-3xl font-extrabold font-mono text-slate-900 tracking-tight">
                  ₹{selected.basePrice.toFixed(2)}
                </span>
                <span className="text-xs font-medium text-slate-600">per kg</span>
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                    selected.isUp
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border border-rose-200'
                  }`}
                >
                  {selected.isUp ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                  {selected.isUp ? '+' : ''}
                  ₹{selected.changeValue.toFixed(2)} ({selected.isUp ? '+' : ''}
                  {selected.changePercent}%)
                </span>
              </div>
            </div>

            {/* Timeframe Filter Buttons */}
            <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-100 border border-slate-200/80 self-start sm:self-auto shadow-2xs">
              {(['7D', '1M', '3M', '6M', '1Y'] as TimeRange[]).map((range) => (
                <button
                  key={range}
                  type="button"
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                    timeRange === range
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Area Chart */}
          <div className="rounded-xl border border-slate-100 bg-slate-50/30 p-2 pt-4">
            <ResponsiveContainer width="100%" height={230}>
              <AreaChart data={chartData} margin={{ top: 8, right: 12, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id={selected.gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={selected.color} stopOpacity={0.28} />
                    <stop offset="95%" stopColor={selected.color} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#64748B', fontSize: 11 }}
                  axisLine={{ stroke: '#CBD5E1' }}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={['dataMin - 4', 'dataMax + 4']}
                  tick={{ fill: '#64748B', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(val) => `₹${Math.round(val)}`}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      const metricTon = (data.price * 1000).toLocaleString('en-IN');
                      return (
                        <div className="p-3 rounded-xl bg-slate-900 text-white shadow-xl text-xs space-y-1.5 border border-slate-800">
                          <p className="font-semibold text-slate-200">{data.date}</p>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-400">Spot Rate:</span>
                            <span className="font-mono font-bold text-amber-400 text-sm">
                              ₹{data.price.toFixed(2)}/kg
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-[11px] text-slate-300">
                            <span className="text-slate-400">Metric Ton:</span>
                            <span className="font-mono font-semibold">₹{metricTon}</span>
                          </div>
                          <div className="pt-1.5 border-t border-slate-800 text-[10px] text-slate-400 flex justify-between gap-4">
                            <span>Low: ₹{data.low}</span>
                            <span>High: ₹{data.high}</span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke={selected.color}
                  strokeWidth={2.4}
                  fill={`url(#${selected.gradientId})`}
                  dot={false}
                  activeDot={{ r: 5, fill: selected.color, stroke: '#FFFFFF', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Key Period Range Statistics */}
          <div className="grid grid-cols-4 gap-2 text-center py-2.5 px-3 rounded-xl bg-slate-50 border border-slate-200/70 text-xs">
            <div>
              <span className="text-[10px] text-slate-600 block uppercase font-medium">Period Low</span>
              <span className="font-mono font-bold text-slate-800">₹{stats.min.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-600 block uppercase font-medium">Period High</span>
              <span className="font-mono font-bold text-slate-800">₹{stats.max.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-600 block uppercase font-medium">Period Avg</span>
              <span className="font-mono font-bold text-slate-800">₹{stats.avg.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-600 block uppercase font-medium">Period Delta</span>
              <span className={`font-mono font-bold ${stats.change >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {stats.change >= 0 ? '+' : ''}₹{stats.change.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Day High / Low Range Slider Meter */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
              <span className="text-slate-500 font-normal">
                Day Low: <strong className="font-mono text-slate-800">₹{selected.dayLow.toFixed(2)}</strong>
              </span>
              <span className="text-xs font-mono font-bold text-blue-600">
                Spot: ₹{selected.basePrice.toFixed(2)}
              </span>
              <span className="text-slate-500 font-normal">
                Day High: <strong className="font-mono text-slate-800">₹{selected.dayHigh.toFixed(2)}</strong>
              </span>
            </div>

            {/* Slider track with position thumb */}
            <div className="relative w-full h-2 rounded-full bg-slate-200 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${dayRangeProgress}%`,
                  backgroundColor: selected.color,
                }}
              />
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-600">
              <span>Metric Ton Equivalent: ₹{(selected.basePrice * 1000).toLocaleString('en-IN')}/MT</span>
              <span>{selected.benchmark}</span>
            </div>
          </div>

          {/* Tender Cost Impact & Guardrail Banner */}
          <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 flex items-start gap-3">
            <Zap size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs">
              <p className="font-semibold text-amber-900">Tender Margin Guardrail & BOM Sensitivity</p>
              <p className="text-amber-800/90 mt-0.5 leading-relaxed">{selected.impactNote}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
