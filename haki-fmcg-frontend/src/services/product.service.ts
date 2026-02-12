import api from './api';
import type { Product, ApiResponse, PaginatedResponse } from '@/types';

export interface ProductFilters {
  category?: string;
  brand?: string;
  search?: string;
  min_price?: number;
  max_price?: number;
  is_active?: boolean;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface CatalogFilters {
  page?: number;
  per_page?: number;
  oem?: string;
  category?: string;
  search?: string;
  source?: string; // 'oem' | 'moglix' | 'user' | 'all'
}

export interface CatalogProduct {
  product_code: string;
  name: string;
  oem: string;
  category: string;
  price_per_meter: number | null;
  voltage_rating: string | null;
  conductor_size: number | string | null;
  cores: number | null;
  insulation: string | null;
  conductor_material: string | null;
  standard: string | null;
  quality_score: number | null;
  source: string;
  added_at?: string;
}

export interface CatalogResponse {
  data: CatalogProduct[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  oem_list: string[];
  source_stats: Record<string, number>;
  user_added_count: number;
}

export interface CatalogStats {
  total: number;
  oems: string[];
  source_stats: Record<string, number>;
  user_added: number;
}

export const productService = {
  list: async (filters?: ProductFilters): Promise<PaginatedResponse<Product>> => {
    const { data } = await api.get<PaginatedResponse<Product>>('/products', { params: filters });
    return data;
  },

  getById: async (id: number | string): Promise<Product> => {
    const { data } = await api.get<ApiResponse<Product>>(`/products/${id}`);
    return data.data;
  },

  getBySku: async (sku: string): Promise<Product> => {
    const { data } = await api.get<ApiResponse<Product>>(`/products/${sku}`);
    return data.data;
  },

  search: async (query: string, limit = 20): Promise<Product[]> => {
    const { data } = await api.post<ApiResponse<{ results: Product[] }>>('/products/search', {
      query,
      limit,
    });
    return data.data.results;
  },

  getCategories: async (): Promise<string[]> => {
    const { data } = await api.get<ApiResponse<string[]>>('/products/categories');
    return data.data;
  },

  compare: async (productIds: number[]): Promise<Product[]> => {
    const { data } = await api.post<ApiResponse<Product[]>>('/products/compare', { ids: productIds });
    return data.data;
  },

  // ── New catalog endpoints ──

  getCatalog: async (filters?: CatalogFilters): Promise<CatalogResponse> => {
    const { data } = await api.get<CatalogResponse>('/products/catalog', { params: filters });
    return data;
  },

  getCatalogStats: async (): Promise<CatalogStats> => {
    const { data } = await api.get<ApiResponse<CatalogStats>>('/products/catalog/stats');
    return data.data;
  },

  addProduct: async (product: Partial<CatalogProduct>): Promise<CatalogProduct> => {
    const { data } = await api.post<ApiResponse<CatalogProduct>>('/products/add', product);
    return data.data;
  },

  importCatalog: async (file?: File, url?: string): Promise<{ imported_count: number; products: CatalogProduct[]; source: string }> => {
    if (file) {
      const form = new FormData();
      form.append('file', file);
      const { data } = await api.post('/products/import-catalog', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120_000,
      });
      return (data as any).data;
    } else if (url) {
      const { data } = await api.post('/products/import-catalog', null, {
        params: { url },
        timeout: 120_000,
      });
      return (data as any).data;
    }
    throw new Error('Provide a file or URL');
  },
};
