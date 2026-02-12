import { create } from 'zustand';
import type { PipelineRun, PipelineStage } from '@/types';

interface PipelineState {
  activePipelines: PipelineRun[];
  selectedPipeline: PipelineRun | null;
  liveStage: PipelineStage | null;

  setActivePipelines: (runs: PipelineRun[]) => void;
  setSelectedPipeline: (run: PipelineRun | null) => void;
  updatePipeline: (run: PipelineRun) => void;
  setLiveStage: (stage: PipelineStage | null) => void;
}

export const usePipelineStore = create<PipelineState>()((set) => ({
  activePipelines: [],
  selectedPipeline: null,
  liveStage: null,

  setActivePipelines: (runs) => set({ activePipelines: runs }),
  setSelectedPipeline: (run) => set({ selectedPipeline: run }),
  updatePipeline: (run) =>
    set((s) => ({
      activePipelines: s.activePipelines.map((p) => (p.id === run.id ? run : p)),
      selectedPipeline: s.selectedPipeline?.id === run.id ? run : s.selectedPipeline,
    })),
  setLiveStage: (stage) => set({ liveStage: stage }),
}));
