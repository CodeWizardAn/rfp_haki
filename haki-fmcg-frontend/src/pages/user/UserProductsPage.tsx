import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Package,
  Search,
  Grid3X3,
  List,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Plus,
  Upload,
  Link2,
  Building2,
  Zap,
  Database,
  UserPlus,
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileText,
  X,
} from 'lucide-react';
import { Card, Badge, Button, Modal, Input, Spinner } from '@/components/ui';
import { productService, type CatalogProduct, type CatalogResponse, type CatalogFilters } from '@/services/product.service';

// ── Source badge color helper ──
function sourceBadge(source: string) {
  if (source === 'user') return { color: 'cyan' as const, label: 'User Added' };
  if (source === 'imported') return { color: 'purple' as const, label: 'Imported' };
  return { color: 'emerald' as const, label: source?.toUpperCase() || 'OEM' };
}

// ── Add Product Modal ──
function AddProductModal({ open, onClose, onAdded }: { open: boolean; onClose: () => void; onAdded: () => void }) {
  const [form, setForm] = useState({
    name: '', oem: '', category: '', price_per_meter: '',
    voltage_rating: '', conductor_size: '', cores: '',
    insulation: '', conductor_material: '', standard: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!form.name.trim()) { setError('Product name is required'); return; }
    setSaving(true); setError('');
    try {
      await productService.addProduct({
        name: form.name,
        oem: form.oem || 'Custom',
        category: form.category || 'General',
        price_per_meter: form.price_per_meter ? Number(form.price_per_meter) : null,
        voltage_rating: form.voltage_rating || null,
        conductor_size: form.conductor_size ? Number(form.conductor_size) : null,
        cores: form.cores ? Number(form.cores) : null,
        insulation: form.insulation || null,
        conductor_material: form.conductor_material || null,
        standard: form.standard || null,
      });
      setSuccess(true);
      setTimeout(() => { onAdded(); onClose(); setSuccess(false); setForm({ name: '', oem: '', category: '', price_per_meter: '', voltage_rating: '', conductor_size: '', cores: '', insulation: '', conductor_material: '', standard: '' }); }, 800);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to add product');
    } finally { setSaving(false); }
  };

  return (
    <Modal open={open} onClose={onClose} size="lg" title="Add Product" description="Manually add a new product to your catalog">
      <div className="space-y-4">
        {error && <div className="flex items-center gap-2 text-coral-flame text-sm bg-coral-flame/10 px-3 py-2 rounded-lg"><AlertCircle size={14} />{error}</div>}
        {success && <div className="flex items-center gap-2 text-neon-emerald text-sm bg-neon-emerald/10 px-3 py-2 rounded-lg"><CheckCircle2 size={14} />Product added successfully!</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input label="Product Name *" placeholder="e.g. XLPE Cable 3x95mm²" value={form.name} onChange={(e) => set('name', e.target.value)} />
          <Input label="OEM / Brand" placeholder="e.g. Polycab" value={form.oem} onChange={(e) => set('oem', e.target.value)} />
          <Input label="Category" placeholder="e.g. Power Cables" value={form.category} onChange={(e) => set('category', e.target.value)} />
          <Input label="Price per Meter (₹)" placeholder="e.g. 450" type="number" value={form.price_per_meter} onChange={(e) => set('price_per_meter', e.target.value)} />
          <Input label="Voltage Rating" placeholder="e.g. 11kV" value={form.voltage_rating} onChange={(e) => set('voltage_rating', e.target.value)} />
          <Input label="Conductor Size (mm²)" placeholder="e.g. 95" type="number" value={form.conductor_size} onChange={(e) => set('conductor_size', e.target.value)} />
          <Input label="Number of Cores" placeholder="e.g. 3" type="number" value={form.cores} onChange={(e) => set('cores', e.target.value)} />
          <Input label="Insulation Type" placeholder="e.g. XLPE, PVC" value={form.insulation} onChange={(e) => set('insulation', e.target.value)} />
          <Input label="Conductor Material" placeholder="e.g. Copper, Aluminium" value={form.conductor_material} onChange={(e) => set('conductor_material', e.target.value)} />
          <Input label="Standard" placeholder="e.g. IS 7098, IEC 60502" value={form.standard} onChange={(e) => set('standard', e.target.value)} />
        </div>
      </div>
      <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-steel-slate/20">
        <Button variant="ghost" onClick={onClose} disabled={saving}>Cancel</Button>
        <Button variant="primary" onClick={handleSubmit} disabled={saving || success}>
          {saving ? <><Loader2 size={14} className="animate-spin mr-1.5" />Adding...</> : success ? <><CheckCircle2 size={14} className="mr-1.5" />Added!</> : <><Plus size={14} className="mr-1.5" />Add Product</>}
        </Button>
      </div>
    </Modal>
  );
}

// ── Import Catalog Modal ──
function ImportCatalogModal({ open, onClose, onImported }: { open: boolean; onClose: () => void; onImported: (count: number) => void }) {
  const [mode, setMode] = useState<'file' | 'url'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ imported_count: number } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleImport = async () => {
    setError(''); setResult(null); setImporting(true);
    try {
      const res = await productService.importCatalog(mode === 'file' ? file! : undefined, mode === 'url' ? url : undefined);
      setResult(res);
      onImported(res.imported_count);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Import failed');
    } finally { setImporting(false); }
  };

  const canImport = mode === 'file' ? !!file : url.trim().length > 5;

  return (
    <Modal open={open} onClose={onClose} size="lg" title="Connect Product Catalog" description="Import products from a PDF catalog or URL. Our AI will detect and extract products automatically.">
      <div className="space-y-5">
        {/* Mode Tabs */}
        <div className="flex gap-1 p-1 rounded-xl bg-steel-slate/20">
          <button onClick={() => setMode('file')} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-colors ${mode === 'file' ? 'bg-neon-emerald/15 text-neon-emerald' : 'text-muted-silver hover:text-ghost-white'}`}>
            <Upload size={15} />PDF Upload
          </button>
          <button onClick={() => setMode('url')} className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-colors ${mode === 'url' ? 'bg-electric-cyan/15 text-electric-cyan' : 'text-muted-silver hover:text-ghost-white'}`}>
            <Link2 size={15} />Catalog URL
          </button>
        </div>

        {mode === 'file' ? (
          <div>
            <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <div
              onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed border-steel-slate/30 rounded-xl p-8 text-center cursor-pointer hover:border-neon-emerald/30 transition-colors"
            >
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <FileText size={24} className="text-neon-emerald" />
                  <div className="text-left">
                    <p className="text-sm text-ghost-white font-medium">{file.name}</p>
                    <p className="text-xs text-muted-silver">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  <button onClick={(e) => { e.stopPropagation(); setFile(null); }} className="p-1 hover:bg-steel-slate/30 rounded"><X size={14} className="text-muted-silver" /></button>
                </div>
              ) : (
                <>
                  <Upload size={32} className="mx-auto text-steel-slate/50 mb-3" />
                  <p className="text-sm text-ghost-white">Click to upload PDF catalog</p>
                  <p className="text-xs text-muted-silver mt-1">Supports product catalogs, datasheets, and spec sheets</p>
                </>
              )}
            </div>
          </div>
        ) : (
          <Input
            label="Catalog URL"
            placeholder="https://example.com/product-catalog.pdf"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            leftIcon={<Link2 size={14} />}
          />
        )}

        {error && <div className="flex items-center gap-2 text-coral-flame text-sm bg-coral-flame/10 px-3 py-2 rounded-lg"><AlertCircle size={14} />{error}</div>}

        {result && (
          <div className="bg-neon-emerald/10 border border-neon-emerald/20 rounded-xl p-4">
            <div className="flex items-center gap-2 text-neon-emerald font-medium mb-1">
              <CheckCircle2 size={16} />Import Complete
            </div>
            <p className="text-sm text-ghost-white">{result.imported_count} products detected and added to your catalog.</p>
          </div>
        )}

        {importing && (
          <div className="flex items-center gap-3 text-sm text-electric-cyan py-3">
            <Loader2 size={16} className="animate-spin" />
            <span>AI is analyzing your catalog and extracting products... This may take a minute.</span>
          </div>
        )}
      </div>
      <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-steel-slate/20">
        <Button variant="ghost" onClick={onClose} disabled={importing}>Cancel</Button>
        {!result ? (
          <Button variant="primary" onClick={handleImport} disabled={!canImport || importing}>
            {importing ? <><Loader2 size={14} className="animate-spin mr-1.5" />Importing...</> : <><Upload size={14} className="mr-1.5" />Import Catalog</>}
          </Button>
        ) : (
          <Button variant="primary" onClick={() => { onClose(); setResult(null); setFile(null); setUrl(''); }}>Done</Button>
        )}
      </div>
    </Modal>
  );
}

// ── Main Page ──
export default function UserProductsPage() {
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [perPage] = useState(50);
  const [search, setSearch] = useState('');
  const [oem, setOem] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [addOpen, setAddOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const searchTimer = useRef<ReturnType<typeof setTimeout>>();

  // Debounced search
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    searchTimer.current = setTimeout(() => setDebouncedSearch(search), 350);
    return () => clearTimeout(searchTimer.current);
  }, [search]);

  // Fetch catalog
  const fetchCatalog = useCallback(async () => {
    setLoading(true);
    try {
      const filters: CatalogFilters = { page, per_page: perPage };
      if (oem !== 'all') filters.oem = oem;
      if (debouncedSearch) filters.search = debouncedSearch;
      const res = await productService.getCatalog(filters);
      setCatalog(res);
    } catch (e) {
      console.error('Failed to load catalog:', e);
    } finally { setLoading(false); }
  }, [page, perPage, oem, debouncedSearch]);

  useEffect(() => { fetchCatalog(); }, [fetchCatalog]);

  // Reset page on filter change
  useEffect(() => { setPage(1); }, [oem, debouncedSearch]);

  const products = catalog?.data || [];
  const total = catalog?.total || 0;
  const totalPages = catalog?.total_pages || 1;
  const oemList = catalog?.oem_list || [];
  const sourceStats = catalog?.source_stats || {};
  const userAdded = catalog?.user_added_count || 0;

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-h2 text-ghost-white flex items-center gap-3">
            <Package size={28} className="text-neon-emerald" />
            Product Catalog
          </h1>
          <p className="text-body text-muted-silver mt-1">
            {total > 0 ? (
              <><span className="text-neon-emerald font-semibold">{total.toLocaleString()}</span> products from <span className="text-electric-cyan font-medium">{oemList.length}</span> OEMs</>
            ) : 'Loading product catalog...'}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={() => setImportOpen(true)}>
            <Upload size={14} className="mr-1.5" />Connect Catalog
          </Button>
          <Button variant="primary" size="sm" onClick={() => setAddOpen(true)}>
            <Plus size={14} className="mr-1.5" />Add Product
          </Button>
        </div>
      </div>

      {/* ── Stats Bar ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card variant="glass" className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-neon-emerald/10"><Database size={18} className="text-neon-emerald" /></div>
            <div>
              <p className="text-xs text-muted-silver">Total Products</p>
              <p className="text-lg font-bold text-ghost-white">{total.toLocaleString()}</p>
            </div>
          </div>
        </Card>
        <Card variant="glass" className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-electric-cyan/10"><Building2 size={18} className="text-electric-cyan" /></div>
            <div>
              <p className="text-xs text-muted-silver">OEM Brands</p>
              <p className="text-lg font-bold text-ghost-white">{oemList.length}</p>
            </div>
          </div>
        </Card>
        <Card variant="glass" className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10"><Zap size={18} className="text-amber-400" /></div>
            <div>
              <p className="text-xs text-muted-silver">Data Sources</p>
              <p className="text-lg font-bold text-ghost-white">{Object.keys(sourceStats).length}</p>
            </div>
          </div>
        </Card>
        <Card variant="glass" className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10"><UserPlus size={18} className="text-purple-400" /></div>
            <div>
              <p className="text-xs text-muted-silver">User Added</p>
              <p className="text-lg font-bold text-ghost-white">{userAdded}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* ── Search & Filters ── */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[280px] relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-silver" />
          <input
            type="text"
            placeholder="Search by product name, code, or OEM..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-ghost-white placeholder:text-muted-silver/60 focus:outline-none focus:border-neon-emerald/40 transition-colors"
          />
        </div>
        <div className="relative">
          <select
            value={oem}
            onChange={(e) => setOem(e.target.value)}
            className="glass-input pl-3 pr-8 py-2.5 rounded-xl text-sm text-ghost-white bg-transparent appearance-none cursor-pointer"
          >
            <option value="all">All OEMs</option>
            {oemList.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
          <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-silver pointer-events-none" />
        </div>
        <div className="flex items-center gap-1 border-l border-steel-slate/20 pl-3">
          <button onClick={() => setViewMode('grid')} className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-neon-emerald/15 text-neon-emerald' : 'text-muted-silver hover:text-ghost-white'}`}>
            <Grid3X3 size={16} />
          </button>
          <button onClick={() => setViewMode('list')} className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-neon-emerald/15 text-neon-emerald' : 'text-muted-silver hover:text-ghost-white'}`}>
            <List size={16} />
          </button>
        </div>
      </div>

      {/* ── Showing count + Source chips ── */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-sm text-muted-silver">
          Showing <span className="text-ghost-white font-medium">{products.length}</span> of <span className="text-ghost-white font-medium">{total.toLocaleString()}</span> products
          {debouncedSearch && <span className="text-electric-cyan"> matching "{debouncedSearch}"</span>}
        </p>
        <div className="flex items-center gap-2 flex-wrap">
          {Object.entries(sourceStats).map(([src, count]) => (
            <span key={src} className="text-[11px] px-2 py-0.5 rounded-full bg-steel-slate/20 text-muted-silver">
              {src}: {(count as number).toLocaleString()}
            </span>
          ))}
        </div>
      </div>

      {/* ── Loading State ── */}
      {loading && (
        <div className="flex items-center justify-center py-16 gap-3">
          <Spinner size="md" />
          <span className="text-muted-silver text-sm">Loading products...</span>
        </div>
      )}

      {/* ── Product Table (List View) ── */}
      {!loading && viewMode === 'list' && products.length > 0 && (
        <div>
          <Card variant="glass">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-muted-silver border-b border-steel-slate/20">
                    <th className="p-3 font-medium">Code</th>
                    <th className="p-3 font-medium">Product Name</th>
                    <th className="p-3 font-medium">OEM</th>
                    <th className="p-3 font-medium">Category</th>
                    <th className="p-3 font-medium">Conductor</th>
                    <th className="p-3 font-medium">Voltage</th>
                    <th className="p-3 font-medium">Price/m</th>
                    <th className="p-3 font-medium">Source</th>
                  </tr>
                </thead>
                <tbody>
                    {products.map((p, i) => {
                      const sb = sourceBadge(p.source);
                      return (
                        <tr
                          key={`${p.product_code}-${i}`}
                          className="border-b border-steel-slate/10 hover:bg-steel-slate/10 transition-colors"
                        >
                          <td className="p-3 font-mono text-xs text-electric-cyan whitespace-nowrap">{p.product_code}</td>
                          <td className="p-3 text-ghost-white font-medium max-w-[300px] truncate">{p.name}</td>
                          <td className="p-3 text-muted-silver whitespace-nowrap">{p.oem}</td>
                          <td className="p-3 text-muted-silver text-xs">{p.category || '—'}</td>
                          <td className="p-3 text-muted-silver text-xs whitespace-nowrap">
                            {p.conductor_size ? `${p.conductor_size}mm²` : '—'}
                            {p.cores ? ` × ${p.cores}C` : ''}
                            {p.conductor_material ? ` ${p.conductor_material}` : ''}
                          </td>
                          <td className="p-3 text-muted-silver text-xs">{p.voltage_rating || '—'}</td>
                          <td className="p-3 text-ghost-white font-semibold whitespace-nowrap">
                            {p.price_per_meter != null ? `₹${p.price_per_meter.toLocaleString('en-IN')}` : '—'}
                          </td>
                          <td className="p-3">
                            <Badge variant="soft" color={sb.color} size="sm">{sb.label}</Badge>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ── Product Grid View ── */}
      {!loading && viewMode === 'grid' && products.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {products.map((p, i) => {
              const sb = sourceBadge(p.source);
              return (
                <div key={`${p.product_code}-${i}`}>
                  <Card variant="glass" className="h-full flex flex-col hover:border-neon-emerald/20 transition-colors">
                    <div className="h-24 bg-steel-slate/20 rounded-t-xl flex items-center justify-center">
                      <Package size={32} className="text-steel-slate/40" />
                    </div>
                    <div className="p-4 flex flex-col flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-mono text-muted-silver">{p.product_code}</span>
                        <Badge variant="soft" color={sb.color} size="sm">{sb.label}</Badge>
                      </div>
                      <h3 className="text-sm font-semibold text-ghost-white line-clamp-2 mb-2">{p.name}</h3>
                      <div className="flex items-center gap-2 mb-1 text-xs text-muted-silver">
                        <Building2 size={12} /> {p.oem}
                      </div>
                      {p.category && (
                        <p className="text-xs text-muted-silver/70 mb-2">{p.category}</p>
                      )}
                      <div className="flex flex-wrap gap-1 mb-3">
                        {p.voltage_rating && <span className="text-[10px] px-1.5 py-0.5 rounded bg-electric-cyan/10 text-electric-cyan">{p.voltage_rating}</span>}
                        {p.conductor_size && <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400">{p.conductor_size}mm²</span>}
                        {p.insulation && <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400">{p.insulation}</span>}
                      </div>
                      <div className="mt-auto">
                        {p.price_per_meter != null ? (
                          <p className="text-lg font-bold text-ghost-white">₹{p.price_per_meter.toLocaleString('en-IN')}<span className="text-xs text-muted-silver font-normal">/m</span></p>
                        ) : (
                          <p className="text-sm text-muted-silver italic">Price on request</p>
                        )}
                      </div>
                    </div>
                  </Card>
                </div>
              );
            })}
        </div>
      )}

      {/* ── Empty State ── */}
      {!loading && products.length === 0 && (
        <div className="text-center py-16">
          <Package size={48} className="mx-auto text-steel-slate/40 mb-4" />
          <p className="text-ghost-white font-medium mb-1">No products found</p>
          <p className="text-sm text-muted-silver mb-4">
            {debouncedSearch ? `No results for "${debouncedSearch}". Try a different search term.` : 'Your product catalog is empty.'}
          </p>
          <div className="flex items-center justify-center gap-3">
            <Button variant="outline" size="sm" onClick={() => setImportOpen(true)}>
              <Upload size={14} className="mr-1.5" />Import Catalog
            </Button>
            <Button variant="primary" size="sm" onClick={() => setAddOpen(true)}>
              <Plus size={14} className="mr-1.5" />Add Product
            </Button>
          </div>
        </div>
      )}

      {/* ── Pagination ── */}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-muted-silver">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg glass-input text-ghost-white disabled:opacity-30 hover:bg-steel-slate/30 transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            {/* Page numbers */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let num: number;
              if (totalPages <= 5) num = i + 1;
              else if (page <= 3) num = i + 1;
              else if (page >= totalPages - 2) num = totalPages - 4 + i;
              else num = page - 2 + i;
              return (
                <button
                  key={num}
                  onClick={() => setPage(num)}
                  className={`w-8 h-8 rounded-lg text-xs font-medium transition-colors ${page === num ? 'bg-neon-emerald/20 text-neon-emerald' : 'text-muted-silver hover:text-ghost-white hover:bg-steel-slate/30'}`}
                >
                  {num}
                </button>
              );
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg glass-input text-ghost-white disabled:opacity-30 hover:bg-steel-slate/30 transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* ── Modals ── */}
      <AddProductModal open={addOpen} onClose={() => setAddOpen(false)} onAdded={fetchCatalog} />
      <ImportCatalogModal open={importOpen} onClose={() => setImportOpen(false)} onImported={() => fetchCatalog()} />
    </div>
  );
}
