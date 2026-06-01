import api from './api';
import type {
  DashboardStats,
  RFPAnalytics,
  BidAnalytics,
  WinLossPrediction,
  ActivityItem,
  ApiResponse,
  PaginatedResponse,
} from '@/types';

export const analyticsService = {
  getDashboardStats: async (): Promise<DashboardStats> => {
    const { data } = await api.get<ApiResponse<DashboardStats>>('/analytics/dashboard');
    return data.data;
  },

  getRFPAnalytics: async (period?: string): Promise<RFPAnalytics> => {
    const { data } = await api.get<ApiResponse<RFPAnalytics>>('/analytics/rfps', {
      params: { period },
    });
    return data.data;
  },

  getBidAnalytics: async (period?: string): Promise<BidAnalytics> => {
    const { data } = await api.get<ApiResponse<BidAnalytics>>('/analytics/bids', {
      params: { period },
    });
    return data.data;
  },

  getActivityFeed: async (page = 1, perPage = 20): Promise<PaginatedResponse<ActivityItem>> => {
    const { data } = await api.get<PaginatedResponse<ActivityItem>>('/analytics/activity', {
      params: { page, per_page: perPage },
    });
    return data;
  },

  getSystemHealth: async () => {
    const { data } = await api.get<ApiResponse<Record<string, unknown>>>('/analytics/system-health');
    return data.data;
  },

  getPerformanceMetrics: async () => {
    const { data } = await api.get<ApiResponse<Record<string, unknown>>>('/analytics/performance');
    return data.data;
  },

  getWinLossPrediction: async (): Promise<WinLossPrediction> => {
    const { data } = await api.get<ApiResponse<WinLossPrediction>>('/analytics/win-loss-prediction');
    return data.data;
  },
};
