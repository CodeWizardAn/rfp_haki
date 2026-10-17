import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Activity,
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
  category: string;
  usage: string;
  color: string;
  gradientId: string;
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
    category: 'Core Conductor',
    usage: 'Primary conductor for building wire & flexible cables',
    color: '#D97706', // Copper Amber
    gradientId: 'copperGradient',
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
    category: 'Power Conductor',
    usage: 'Conductor for HT/LT power & aerial bunched distribution cables',
    color: '#2563EB', // Royal Blue
    gradientId: 'aluminiumGradient',
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
    category: 'Armouring & Shield',
    usage: 'Mechanical strip armouring & wire braiding protection',
    color: '#475569', // Slate
    gradientId: 'steelGradient',
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
    category: 'Insulation & Sheath',
    usage: 'Flame-retardant & low-smoke insulation outer jacketing',
    color: '#059669', // Emerald
    gradientId: 'pvcGradient',
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
    category: 'High-Dielectric Core',
    usage: 'Cross-linked polyethylene for 11kV - 33kV medium voltage cores',
    color: '#7C3AED', // Violet
    gradientId: 'xlpeGradient',
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

  const selected = rates[selectedKey];

  useEffect(() => {
    const fetchLiveRates = async () => {
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
        }
      } catch {
        // Fallback to initial benchmarks
      }
    };
    fetchLiveRates();
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

  return (
    <div className="bg-white/95 rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden backdrop-blur-md">
      {/* ── Header ── */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3 bg-gradient-to-r from-slate-50/70 via-white to-slate-50/40">
        <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200/70 flex items-center justify-center text-blue-600 shadow-xs">
          <Activity size={20} />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight">
            Raw Material & Metal Commodity Index
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Benchmark raw material spot rates powering wire & cable tender cost modeling
          </p>
        </div>
      </div>

      {/* ── Main Split View ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-slate-100">
        {/* ── Left Watchlist (5 columns on desktop) ── */}
        <div className="lg:col-span-5 p-4 space-y-2 bg-slate-50/40 flex flex-col justify-between">
          <div className="flex items-center justify-between px-1 mb-1">
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
        </div>

        {/* ── Right Interactive Terminal & Chart (7 columns on desktop) ── */}
        <div className="lg:col-span-7 p-5 space-y-4 bg-white flex flex-col justify-between">
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
          <div className="rounded-xl border border-slate-100 bg-slate-50/30 p-2 pt-4 flex-1 min-h-[260px]">
            <ResponsiveContainer width="100%" height="100%" minHeight={260}>
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
        </div>
      </div>
    </div>
  );
}
