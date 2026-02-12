import api from './api';
import type { Vendor, ApiResponse, PaginatedResponse } from '@/types';

export interface VendorFilters {
  tier?: string;
  category?: string;
  search?: string;
  is_active?: boolean;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const vendorService = {
  list: async (filters?: VendorFilters): Promise<PaginatedResponse<Vendor>> => {
    const { data } = await api.get<PaginatedResponse<Vendor>>('/vendors', { params: filters });
    return data;
  },

  getById: async (id: number): Promise<Vendor> => {
    const { data } = await api.get<ApiResponse<Vendor>>(`/vendors/${id}`);
    return data.data;
  },

  create: async (vendor: Partial<Vendor>): Promise<Vendor> => {
    const { data } = await api.post<ApiResponse<Vendor>>('/vendors', vendor);
    return data.data;
  },

  update: async (id: number, vendor: Partial<Vendor>): Promise<Vendor> => {
    const { data } = await api.put<ApiResponse<Vendor>>(`/vendors/${id}`, vendor);
    return data.data;
  },

  getRankings: async (): Promise<Vendor[]> => {
    const { data } = await api.get<ApiResponse<Vendor[]>>('/vendors/rankings');
    return data.data;
  },
};
