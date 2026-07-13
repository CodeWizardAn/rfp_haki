import { AlertTriangle, CheckCircle2, RotateCcw, Bug } from 'lucide-react';
import { Button, Card, Badge } from '@/components/ui';

export interface FailedRun {
  id: string;
  numericId?: number;
  rfpId: string;
  errorMessage?: string | null;
  startedAt: string;
}

interface PipelineErrorRecoveryProps {
  failedRuns: FailedRun[];
  onRetry: (numericId: number) => void;
  isRetrying?: boolean;
}

export default function PipelineErrorRecovery({ failedRuns, onRetry, isRetrying }: PipelineErrorRecoveryProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <Bug size={16} className="text-coral-flame" />
        <h3 className="text-sm font-semibold text-ghost-white">Error Recovery</h3>
        {failedRuns.length > 0 && <Badge variant="solid" color="red" size="sm">{failedRuns.length}</Badge>}
      </div>

      {failedRuns.length === 0 ? (
        <Card variant="glass" className="p-4 flex items-center gap-3">
          <CheckCircle2 size={16} className="text-neon-emerald" />
          <p className="text-sm text-muted-silver">No failed pipeline runs — everything's healthy.</p>
        </Card>
      ) : (
        failedRuns.map((run) => (
          <Card key={run.id} variant="glass" className="border border-coral-flame/30">
            <div className="flex items-start gap-3 p-3">
              <div className="w-8 h-8 rounded-lg bg-coral-flame/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <AlertTriangle size={14} className="text-coral-flame" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-semibold text-ghost-white">{run.id}</span>
                  <span className="text-[10px] text-muted-silver font-mono">RFP {run.rfpId}</span>
                </div>
                <p className="text-xs text-muted-silver mt-0.5">{run.errorMessage || 'Pipeline run failed (no error detail recorded)'}</p>
                <p className="text-[10px] text-muted-silver mt-1">Started {run.startedAt}</p>
              </div>
              {run.numericId != null && (
                <Button
                  size="sm"
                  variant="primary"
                  leftIcon={<RotateCcw size={12} />}
                  onClick={() => onRetry(run.numericId!)}
                  loading={isRetrying}
                >
                  Retry
                </Button>
              )}
            </div>
          </Card>
        ))
      )}
    </div>
  );
}
