import api from './api';
import type { AgentConversation, AgentStatus, AgentMessage, ApiResponse } from '@/types';
import type { AgentType } from '@/types';

export const agentService = {
  getStatuses: async (): Promise<AgentStatus[]> => {
    const { data } = await api.get<ApiResponse<AgentStatus[]>>('/agents/status');
    return data.data;
  },

  getConversations: async (agentType?: AgentType): Promise<AgentConversation[]> => {
    const { data } = await api.get<ApiResponse<AgentConversation[]>>('/agents/conversations', {
      params: { agent_type: agentType },
    });
    return data.data;
  },

  getConversation: async (id: string): Promise<AgentConversation> => {
    const { data } = await api.get<ApiResponse<AgentConversation>>(`/agents/conversations/${id}`);
    return data.data;
  },

  sendMessage: async (conversationId: string, message: string): Promise<AgentMessage> => {
    const { data } = await api.post<ApiResponse<AgentMessage>>(
      `/agents/conversations/${conversationId}/messages`,
      { content: message },
    );
    return data.data;
  },

  startWorkflow: async (rfpId: number): Promise<AgentConversation> => {
    const { data } = await api.post<ApiResponse<AgentConversation>>('/agents/workflow/start', {
      rfp_id: rfpId,
    });
    return data.data;
  },
};
