import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, FileText, Package, Users, Tag, Clock, X } from 'lucide-react';

interface SearchResult {
  id: string;
  title: string;
  category: 'rfp' | 'product' | 'vendor' | 'bid';
  subtitle: string;
}

const categoryIcons = {
  rfp: <FileText size={14} className="text-electric-cyan" />,
  product: <Package size={14} className="text-neon-emerald" />,
  vendor: <Users size={14} className="text-violet-pulse" />,
  bid: <Tag size={14} className="text-amber-glow" />,
};

const categoryLabels = { rfp: 'RFPs', product: 'Products', vendor: 'Vendors', bid: 'Bids' };

const mockResults: SearchResult[] = [
  { id: 'RFP-2026-0001', title: 'Power Cable Supply — Zone East', category: 'rfp', subtitle: 'High priority · Pricing' },
  { id: 'RFP-2026-0002', title: 'LT Cable 1.1kV Requirements', category: 'rfp', subtitle: 'Medium priority · Draft' },
  { id: 'HAV-XLPE-11-240', title: 'XLPE 11kV 3Cx240 Havells Make', category: 'product', subtitle: 'Havells · ₹1,850/100m' },
  { id: 'POL-PVC-1.1-16', title: 'PVC 1.1kV 4Cx16 Polycab', category: 'product', subtitle: 'Polycab · ₹320/100m' },
  { id: 'V-001', title: 'Havells India Ltd', category: 'vendor', subtitle: 'Rating: 4.8 · Active' },
  { id: 'B-0087', title: 'Bid for Power Cable Supply', category: 'bid', subtitle: 'Havells · ₹58.6L · Approved' },
];

const RECENT_KEY = 'haki-recent-searches';

export default function RFPSearchAutocomplete({
  onClose,
  className = '',
}: {
  onClose?: () => void;
  className?: string;
}) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [activeIdx, setActiveIdx] = useState(-1);
  const [recentSearches, setRecentSearches] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]'); } catch { return []; }
  });
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Debounced search (300ms)
  useEffect(() => {
    if (!query.trim()) { setResults([]); return; }
    const t = setTimeout(() => {
      const q = query.toLowerCase();
      setResults(mockResults.filter((r) =>
        r.title.toLowerCase().includes(q) ||
        r.id.toLowerCase().includes(q) ||
        r.subtitle.toLowerCase().includes(q),
      ));
      setActiveIdx(-1);
    }, 300);
    return () => clearTimeout(t);
  }, [query]);

  const saveRecent = useCallback((term: string) => {
    const next = [term, ...recentSearches.filter((s) => s !== term)].slice(0, 5);
    setRecentSearches(next);
    localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  }, [recentSearches]);

  const handleSelect = (result: SearchResult) => {
    saveRecent(result.title);
    const routes: Record<string, string> = {
      rfp: `/rfps/${result.id}`,
      product: `/products`,
      vendor: `/vendors`,
      bid: `/bids`,
    };
    navigate(routes[result.category] || '/');
    onClose?.();
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx((prev) => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx((prev) => Math.max(prev - 1, -1));
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      const item = results[activeIdx];
      if (item) handleSelect(item);
    } else if (e.key === 'Escape') {
      onClose?.();
    }
  };

  // Scroll active item into view
  useEffect(() => {
    if (activeIdx >= 0 && listRef.current) {
      const el = listRef.current.children[activeIdx] as HTMLElement;
      el?.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIdx]);

  // Focus input
  useEffect(() => { inputRef.current?.focus(); }, []);

  // Group results by category
  const grouped = results.reduce<Record<string, SearchResult[]>>((acc, r) => {
    (acc[r.category] ??= []).push(r);
    return acc;
  }, {});

  const highlightMatch = (text: string) => {
    if (!query.trim()) return text;
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx < 0) return text;
    return (
      <>
        {text.slice(0, idx)}
        <span className="text-electric-cyan font-semibold">{text.slice(idx, idx + query.length)}</span>
        {text.slice(idx + query.length)}
      </>
    );
  };

  return (
    <div className={`w-full max-w-2xl ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search RFPs, products, vendors, bids…"
          className="w-full pl-10 pr-10 py-3 rounded-xl bg-steel-slate/20 border border-steel-slate/30 text-ghost-white placeholder:text-muted-silver/50 focus:outline-none focus:border-electric-cyan/50 focus:ring-1 focus:ring-electric-cyan/30 text-sm transition-colors"
        />
        {query && (
          <button
            onClick={() => setQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-silver hover:text-ghost-white transition-colors"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Results / Recents */}
      <AnimatePresence>
        {(query.trim() || recentSearches.length > 0) && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="mt-2 rounded-xl bg-midnight-blue/95 border border-steel-slate/30 backdrop-blur-xl overflow-hidden max-h-80 overflow-y-auto"
            ref={listRef}
          >
            {/* Recent Searches */}
            {!query.trim() && recentSearches.length > 0 && (
              <div className="p-3">
                <p className="text-xs text-muted-silver uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Clock size={10} /> Recent
                </p>
                {recentSearches.map((term) => (
                  <button
                    key={term}
                    onClick={() => setQuery(term)}
                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-muted-silver hover:text-ghost-white hover:bg-steel-slate/15 transition-colors"
                  >
                    {term}
                  </button>
                ))}
              </div>
            )}

            {/* Search Results */}
            {query.trim() && results.length === 0 && (
              <div className="p-6 text-center text-muted-silver text-sm">
                No results found for &ldquo;{query}&rdquo;
              </div>
            )}

            {Object.entries(grouped).map(([cat, items]) => (
              <div key={cat}>
                <p className="px-4 pt-3 pb-1 text-xs text-muted-silver uppercase tracking-wider flex items-center gap-1.5">
                  {categoryIcons[cat as keyof typeof categoryIcons]} {categoryLabels[cat as keyof typeof categoryLabels]}
                </p>
                {items.map((item) => {
                  const flatIdx = results.indexOf(item);
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleSelect(item)}
                      className={`w-full text-left flex items-center gap-3 px-4 py-2.5 transition-colors ${
                        flatIdx === activeIdx ? 'bg-electric-cyan/10 text-ghost-white' : 'text-muted-silver hover:bg-steel-slate/15 hover:text-ghost-white'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm truncate">{highlightMatch(item.title)}</p>
                        <p className="text-xs text-muted-silver/70 truncate">{item.id} · {item.subtitle}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
