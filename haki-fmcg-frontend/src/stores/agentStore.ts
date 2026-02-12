import { create } from 'zustand';
import type { AgentStatus, AgentConversation, AgentType } from '@/types';

interface AgentState {
  statuses: AgentStatus[];
  activeConversation: AgentConversation | null;
  conversations: AgentConversation[];
  selectedAgentType: AgentType | null;

  setStatuses: (statuses: AgentStatus[]) => void;
  setActiveConversation: (conv: AgentConversation | null) => void;
  setConversations: (convs: AgentConversation[]) => void;
  setSelectedAgentType: (type: AgentType | null) => void;
  updateConversation: (conv: AgentConversation) => void;
}

export const useAgentStore = create<AgentState>()((set) => ({
  statuses: [],
  activeConversation: null,
  conversations: [],
  selectedAgentType: null,

  setStatuses: (statuses) => set({ statuses }),
  setActiveConversation: (conv) => set({ activeConversation: conv }),
  setConversations: (convs) => set({ conversations: convs }),
  setSelectedAgentType: (type) => set({ selectedAgentType: type }),
  updateConversation: (conv) =>
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.conversation_id === conv.conversation_id ? conv : c,
      ),
      activeConversation:
        s.activeConversation?.conversation_id === conv.conversation_id
          ? conv
          : s.activeConversation,
    })),
}));
