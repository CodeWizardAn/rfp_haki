import { create } from 'zustand';
import type { RFP, RFPStatus } from '@/types';

interface RFPState {
  activeRFP: RFP | null;
  filters: {
    status: RFPStatus | 'all';
    priority: string;
    search: string;
  };
  processingRFPIds: Set<number>;

  setActiveRFP: (rfp: RFP | null) => void;
  setFilter: (key: string, value: string) => void;
  resetFilters: () => void;
  addProcessing: (rfpId: number) => void;
  removeProcessing: (rfpId: number) => void;
}

const defaultFilters = { status: 'all' as const, priority: 'all', search: '' };

export const useRFPStore = create<RFPState>()((set) => ({
  activeRFP: null,
  filters: { ...defaultFilters },
  processingRFPIds: new Set(),

  setActiveRFP: (rfp) => set({ activeRFP: rfp }),
  setFilter: (key, value) => set((s) => ({ filters: { ...s.filters, [key]: value } })),
  resetFilters: () => set({ filters: { ...defaultFilters } }),
  addProcessing: (rfpId) =>
    set((s) => ({ processingRFPIds: new Set([...s.processingRFPIds, rfpId]) })),
  removeProcessing: (rfpId) =>
    set((s) => {
      const next = new Set(s.processingRFPIds);
      next.delete(rfpId);
      return { processingRFPIds: next };
    }),
}));
