import api from './api';
import type { Bid, BidItem, BidApproval, ApiResponse, PaginatedResponse } from '@/types';

export interface BidFilters {
  status?: string;
  rfp_id?: number;
  search?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const bidService = {
  list: async (filters?: BidFilters): Promise<PaginatedResponse<Bid>> => {
    const { data } = await api.get<PaginatedResponse<Bid>>('/bids', { params: filters });
    return data;
  },

  getById: async (id: number): Promise<Bid> => {
    const { data } = await api.get<ApiResponse<Bid>>(`/bids/${id}`);
    return data.data;
  },

  create: async (bid: Partial<Bid>): Promise<Bid> => {
    const { data } = await api.post<ApiResponse<Bid>>('/bids', bid);
    return data.data;
  },

  update: async (id: number, bid: Partial<Bid>): Promise<Bid> => {
    const { data } = await api.put<ApiResponse<Bid>>(`/bids/${id}`, bid);
    return data.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/bids/${id}`);
  },

  addItem: async (bidId: number, item: Partial<BidItem>): Promise<BidItem> => {
    const { data } = await api.post<ApiResponse<BidItem>>(`/bids/${bidId}/items`, item);
    return data.data;
  },

  submit: async (bidId: number): Promise<Bid> => {
    const { data } = await api.post<ApiResponse<Bid>>(`/bids/${bidId}/submit`);
    return data.data;
  },

  requestApproval: async (bidId: number, approvers: string[]): Promise<BidApproval[]> => {
    const { data } = await api.post<ApiResponse<BidApproval[]>>(`/bids/${bidId}/approval/request`, { approvers });
    return data.data;
  },

  approveReject: async (bidId: number, action: 'approve' | 'reject', comments?: string): Promise<BidApproval> => {
    const { data } = await api.post<ApiResponse<BidApproval>>(`/bids/${bidId}/approval/${action}`, { comments });
    return data.data;
  },
};
