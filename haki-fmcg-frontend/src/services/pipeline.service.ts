import api from './api';
import type { PipelineRun, ApiResponse } from '@/types';

export const pipelineService = {
  list: async (): Promise<PipelineRun[]> => {
    const { data } = await api.get<ApiResponse<PipelineRun[]>>('/pipeline/runs');
    return data.data;
  },

  getById: async (id: number): Promise<PipelineRun> => {
    const { data } = await api.get<ApiResponse<PipelineRun>>(`/pipeline/runs/${id}`);
    return data.data;
  },

  start: async (rfpId: number): Promise<PipelineRun> => {
    const { data } = await api.post<ApiResponse<PipelineRun>>('/pipeline/start', { rfp_id: rfpId });
    return data.data;
  },

  cancel: async (pipelineId: string): Promise<void> => {
    await api.post(`/pipeline/runs/${pipelineId}/cancel`);
  },

  getStatus: async (pipelineId: string): Promise<PipelineRun> => {
    const { data } = await api.get<ApiResponse<PipelineRun>>(`/pipeline/runs/${pipelineId}/status`);
    return data.data;
  },

  retry: async (pipelineId: string, stage?: string): Promise<PipelineRun> => {
    const { data } = await api.post<ApiResponse<PipelineRun>>(`/pipeline/runs/${pipelineId}/retry`, { stage });
    return data.data;
  },
};
