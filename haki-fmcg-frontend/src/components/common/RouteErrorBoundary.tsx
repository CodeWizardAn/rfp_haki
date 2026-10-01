import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';
import { RefreshCw, Home, AlertOctagon } from 'lucide-react';
import { Button } from '@/components/ui';
import { HakiLogo } from '@/components/common';

export function RouteErrorBoundary() {
  const error = useRouteError();
  const errorMessage = error instanceof Error ? error.message : '';
  const isChunkError =
    errorMessage.includes('dynamically imported module') ||
    errorMessage.includes('Failed to fetch') ||
    errorMessage.includes('Importing a module script failed');

  const handleReload = () => {
    // Bust browser cache by reloading with cache-busting timestamp
    window.location.href = window.location.pathname + '?v=' + Date.now();
  };

  return (
    <div className="min-h-screen flex items-center justify-center gradient-hero p-6">
      <div className="w-full max-w-lg glass-card-elevated p-8 text-center relative z-10 flex flex-col items-center">
        <HakiLogo size="xl" asLink to="/" />

        <div className="w-14 h-14 rounded-2xl bg-violet-pulse/15 border border-violet-pulse/30 flex items-center justify-center my-6 text-violet-pulse shadow-[0_0_25px_rgba(124,58,237,0.25)]">
          {isChunkError ? <RefreshCw className="animate-spin" size={28} /> : <AlertOctagon size={28} />}
        </div>

        <h1 className="text-2xl font-bold font-heading text-ghost-white mb-2">
          {isChunkError ? 'New Version Available' : 'Something went wrong'}
        </h1>

        <p className="text-sm text-muted-silver max-w-sm mb-6 leading-relaxed">
          {isChunkError
            ? 'A fresh update was just deployed. Please refresh to load the latest components and features.'
            : isRouteErrorResponse(error)
            ? `${error.status} — ${error.statusText}`
            : errorMessage || 'An unexpected error occurred while loading this view.'}
        </p>

        <div className="flex items-center gap-3 w-full justify-center">
          <Button variant="primary" onClick={handleReload} className="gap-2">
            <RefreshCw size={16} />
            Refresh App
          </Button>

          <Link to="/">
            <Button variant="secondary" className="gap-2">
              <Home size={16} />
              Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default RouteErrorBoundary;
