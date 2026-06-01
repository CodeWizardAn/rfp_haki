import api from './api';
import type { RFP, RFPRequirement, ApiResponse, PaginatedResponse } from '@/types';

export interface RFPFilters {
  status?: string;
  priority?: string;
  search?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const rfpService = {
  list: async (filters?: RFPFilters): Promise<PaginatedResponse<RFP>> => {
    const { data } = await api.get<PaginatedResponse<RFP>>('/rfps', { params: filters });
    return data;
  },

  getById: async (id: number): Promise<RFP> => {
    const { data } = await api.get<ApiResponse<RFP>>(`/rfps/${id}`);
    return data.data;
  },

  create: async (rfp: Partial<RFP>): Promise<RFP> => {
    const { data } = await api.post<ApiResponse<RFP>>('/rfps', rfp);
    return data.data;
  },

  update: async (id: number, rfp: Partial<RFP>): Promise<RFP> => {
    const { data } = await api.put<ApiResponse<RFP>>(`/rfps/${id}`, rfp);
    return data.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/rfps/${id}`);
  },

  uploadFile: async (file: File): Promise<RFP> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<ApiResponse<RFP>>('/rfps/upload', formData, {
      timeout: 120_000,                          // 2 min for PDF processing
    });
    return data.data;
  },

  getRequirements: async (rfpId: number): Promise<RFPRequirement[]> => {
    const { data } = await api.get<ApiResponse<RFPRequirement[]>>(`/rfps/${rfpId}/requirements`);
    return data.data;
  },

  startProcessing: async (rfpId: number): Promise<void> => {
    await api.post(`/rfps/${rfpId}/process`);
  },

  /**
   * Comprehensive RFP analysis: extract → parse → match against 22k+ OEM products.
   * Returns requirements, BOQ, OEM summary, top-3 products per requirement.
   */
  analyzeRFP: async (
    file: File,
    options?: {
      include_calculations?: boolean;
      include_recommendations?: boolean;
      include_budget?: boolean;
      include_win_loss?: boolean;
      cable_length?: number;
      application?: string;
    },
  ): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams();
    if (options?.include_calculations !== undefined)
      params.set('include_calculations', String(options.include_calculations));
    if (options?.include_recommendations !== undefined)
      params.set('include_recommendations', String(options.include_recommendations));
    if (options?.include_budget !== undefined)
      params.set('include_budget', String(options.include_budget));
    if (options?.include_win_loss !== undefined)
      params.set('include_win_loss', String(options.include_win_loss));
    if (options?.cable_length !== undefined)
      params.set('cable_length', String(options.cable_length));
    if (options?.application)
      params.set('application', options.application);

    const qs = params.toString();
    const url = `/rfps/analyze${qs ? `?${qs}` : ''}`;

    const { data } = await api.post(url, formData, {
      timeout: 300_000, // 5 min safe margin — heavy ops are background
    });
    return data.data ?? data;
  },
};
