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
  Eye,
  Check,
  ChevronsUpDown,
  Sparkles,
  Regex,
} from 'lucide-react';
import { Card, Badge, Button, Modal, Input, Spinner } from '@/components/ui';
import {
  productService,
  type CatalogResponse,
  type CatalogFilters,
  type ImportPreviewResponse,
} from '@/services/product.service';

// ── Source badge color helper ──
function sourceBadge(source: string) {
  if (source === 'user' || source === 'User Added') return { color: 'cyan' as const, label: 'User Added' };
  if (source === 'imported' || source === 'PDF Import') return { color: 'purple' as const, label: 'PDF Import' };
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
          <Input label="Price (₹) — enter /m or /100m as applicable" placeholder="e.g. 450 per m or 45000 per 100m" type="number" value={form.price_per_meter} onChange={(e) => set('price_per_meter', e.target.value)} />
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

// ── Import Catalog Modal (Two-Step: Extract → Preview → Confirm) ──
function ImportCatalogModal({ open, onClose, onImported }: { open: boolean; onClose: () => void; onImported: (count: number) => void }) {
  const [mode, setMode] = useState<'file' | 'url'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [step, setStep] = useState<'upload' | 'extracting' | 'preview' | 'confirming' | 'done'>('upload');
  const [error, setError] = useState('');
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [importedCount, setImportedCount] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      setStep('upload'); setError(''); setPreview(null); setSelected(new Set());
      setImportedCount(0); setFile(null); setUrl('');
    }
  }, [open]);

  // ── Step 1: Extract from PDF/URL ──
  const handleExtract = async () => {
    setError(''); setStep('extracting');
    try {
      const res = await productService.importCatalog(
        mode === 'file' ? file! : undefined,
        mode === 'url' ? url : undefined,
        false // preview mode
      );
      // If it's a preview response (has extraction_id)
      const data = res as ImportPreviewResponse;
      if (data.extraction_id && data.preview) {
        setPreview(data);
        // Select all by default
        setSelected(new Set(data.preview.map((p) => p.product_code)));
        setStep('preview');
      } else {
        // Fallback: auto-confirmed (legacy)
        const legacy = res as any;
        setImportedCount(legacy.imported_count || 0);
        onImported(legacy.imported_count || 0);
        setStep('done');
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Extraction failed');
      setStep('upload');
    }
  };

  // ── Step 2: Confirm selected products ──
  const handleConfirm = async () => {
    if (!preview) return;
    setStep('confirming'); setError('');
    try {
      const selectedCodes = Array.from(selected);
      const res = await productService.confirmImport(preview.extraction_id, selectedCodes);
      setImportedCount(res.imported_count);
      onImported(res.imported_count);
      setStep('done');
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Import confirmation failed');
      setStep('preview');
    }
  };

  const toggleProduct = (code: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code); else next.add(code);
      return next;
    });
  };
  const toggleAll = () => {
    if (!preview) return;
    if (selected.size === preview.preview.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(preview.preview.map((p) => p.product_code)));
    }
  };

  const canExtract = mode === 'file' ? !!file : url.trim().length > 5;

  return (
    <Modal open={open} onClose={onClose} size="xl" title="Import Product Catalog from PDF" description="Upload a PDF catalog and our AI will extract products automatically.">
      <div className="space-y-5">

        {/* ── Step: Upload ── */}
        {step === 'upload' && (
          <>
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
          </>
        )}

        {/* ── Step: Extracting (loading) ── */}
        {step === 'extracting' && (
          <div className="flex flex-col items-center gap-4 py-12">
            <div className="relative">
              <Loader2 size={40} className="text-electric-cyan animate-spin" />
              <Sparkles size={16} className="absolute -top-1 -right-1 text-amber-400 animate-pulse" />
            </div>
            <div className="text-center">
              <p className="text-ghost-white font-medium">Analyzing PDF Catalog...</p>
              <p className="text-sm text-muted-silver mt-1">AI is reading your catalog and detecting products. This may take up to a minute.</p>
            </div>
            <div className="flex gap-6 text-xs text-muted-silver">
              <span className="flex items-center gap-1.5"><FileText size={12} className="text-neon-emerald" />Extracting text</span>
              <span className="flex items-center gap-1.5"><Eye size={12} className="text-electric-cyan" />Detecting products</span>
              <span className="flex items-center gap-1.5"><Database size={12} className="text-amber-400" />Parsing specs</span>
            </div>
          </div>
        )}

        {/* ── Step: Preview extracted products ── */}
        {step === 'preview' && preview && (
          <>
            {/* Summary bar */}
            <div className="flex items-center justify-between bg-steel-slate/15 rounded-xl p-3">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-neon-emerald" />
                  <span className="text-sm text-ghost-white font-medium">
                    {preview.total_detected} products detected
                  </span>
                </div>
                <Badge variant="soft" color={preview.extraction_method === 'ai' ? 'cyan' : 'amber'} size="sm">
                  {preview.extraction_method === 'ai' ? <><Sparkles size={10} className="mr-1" />AI Extracted</> : <><Regex size={10} className="mr-1" />Pattern Match</>}
                </Badge>
                {preview.page_count > 0 && (
                  <span className="text-xs text-muted-silver">{preview.page_count} pages</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button onClick={toggleAll} className="flex items-center gap-1.5 text-xs text-electric-cyan hover:text-electric-cyan/80 transition-colors">
                  <ChevronsUpDown size={12} />
                  {selected.size === preview.preview.length ? 'Deselect All' : 'Select All'}
                </button>
                <span className="text-xs text-muted-silver">
                  {selected.size} of {preview.preview.length} selected
                </span>
              </div>
            </div>

            {/* Product preview table */}
            <div className="max-h-[400px] overflow-y-auto rounded-xl border border-steel-slate/20">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-deep-space-blue z-10">
                  <tr className="text-left text-xs text-muted-silver border-b border-steel-slate/20">
                    <th className="p-2.5 w-8">
                      <input
                        type="checkbox"
                        checked={selected.size === preview.preview.length}
                        onChange={toggleAll}
                        className="rounded border-steel-slate/40 text-neon-emerald focus:ring-neon-emerald/30"
                      />
                    </th>
                    <th className="p-2.5 font-medium">Product Name</th>
                    <th className="p-2.5 font-medium">OEM</th>
                    <th className="p-2.5 font-medium">Category</th>
                    <th className="p-2.5 font-medium">Size</th>
                    <th className="p-2.5 font-medium">Voltage</th>
                    <th className="p-2.5 font-medium">Material</th>
                    <th className="p-2.5 font-medium">Price/100m</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.preview.map((p) => {
                    const isSelected = selected.has(p.product_code);
                    return (
                      <tr
                        key={p.product_code}
                        onClick={() => toggleProduct(p.product_code)}
                        className={`border-b border-steel-slate/10 cursor-pointer transition-colors ${isSelected ? 'bg-neon-emerald/5 hover:bg-neon-emerald/10' : 'opacity-50 hover:bg-steel-slate/10'}`}
                      >
                        <td className="p-2.5">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleProduct(p.product_code)}
                            className="rounded border-steel-slate/40 text-neon-emerald focus:ring-neon-emerald/30"
                          />
                        </td>
                        <td className="p-2.5 text-ghost-white font-medium max-w-[220px] truncate">{p.name}</td>
                        <td className="p-2.5 text-muted-silver text-xs">{p.oem || '—'}</td>
                        <td className="p-2.5 text-muted-silver text-xs">{p.category || '—'}</td>
                        <td className="p-2.5 text-muted-silver text-xs">{p.conductor_size ? `${p.conductor_size}mm²` : '—'}</td>
                        <td className="p-2.5 text-muted-silver text-xs">{p.voltage_rating || '—'}</td>
                        <td className="p-2.5 text-muted-silver text-xs">{p.conductor_material || '—'}</td>
                        <td className="p-2.5 text-ghost-white font-semibold text-xs">
                          {p.price_per_meter != null ? `₹${Number(p.price_per_meter).toLocaleString('en-IN')}${(p as any).price_unit && (p as any).price_unit !== 'm' ? `/${(p as any).price_unit}` : '/m'}` : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* ── Step: Confirming ── */}
        {step === 'confirming' && (
          <div className="flex flex-col items-center gap-3 py-10">
            <Loader2 size={32} className="text-neon-emerald animate-spin" />
            <p className="text-sm text-ghost-white">Adding {selected.size} products to your catalog...</p>
          </div>
        )}

        {/* ── Step: Done ── */}
        {step === 'done' && (
          <div className="bg-neon-emerald/10 border border-neon-emerald/20 rounded-xl p-6 text-center">
            <CheckCircle2 size={32} className="mx-auto text-neon-emerald mb-3" />
            <p className="text-ghost-white font-semibold text-lg">{importedCount} Products Added!</p>
            <p className="text-sm text-muted-silver mt-1">
              Products have been extracted from the PDF and added to your catalog.
              They are now available for RFP matching and search.
            </p>
          </div>
        )}

        {/* ── Error ── */}
        {error && (
          <div className="flex items-center gap-2 text-coral-flame text-sm bg-coral-flame/10 px-3 py-2 rounded-lg">
            <AlertCircle size={14} />{error}
          </div>
        )}
      </div>

      {/* ── Footer Actions ── */}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-steel-slate/20">
        <div>
          {step === 'preview' && (
            <Button variant="ghost" size="sm" onClick={() => { setStep('upload'); setPreview(null); }}>
              <Upload size={14} className="mr-1.5" />Upload Different File
            </Button>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={onClose} disabled={step === 'extracting' || step === 'confirming'}>Cancel</Button>
          {step === 'upload' && (
            <Button variant="primary" onClick={handleExtract} disabled={!canExtract}>
              <Eye size={14} className="mr-1.5" />Extract Products
            </Button>
          )}
          {step === 'preview' && (
            <Button variant="primary" onClick={handleConfirm} disabled={selected.size === 0}>
              <Check size={14} className="mr-1.5" />Add {selected.size} Products to Catalog
            </Button>
          )}
          {step === 'done' && (
            <Button variant="primary" onClick={() => { onClose(); }}>Done</Button>
          )}
        </div>
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
                    <th className="p-3 font-medium">Price/100m</th>
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
                            {p.price_per_meter != null ? `₹${p.price_per_meter.toLocaleString('en-IN')}${(p as any).price_unit && (p as any).price_unit !== 'm' ? `/${(p as any).price_unit}` : '/m'}` : '—'}
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
                          <p className="text-lg font-bold text-ghost-white">₹{p.price_per_meter.toLocaleString('en-IN')}<span className="text-xs text-muted-silver font-normal">{(p as any).price_unit && (p as any).price_unit !== 'm' ? `/${(p as any).price_unit}` : '/m'}</span></p>
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
