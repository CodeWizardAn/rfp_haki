import { RouterProvider } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { queryClient } from '@/lib/queryClient';
import { router } from '@/router';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'rgba(18, 24, 51, 0.9)',
            color: '#E8ECF4',
            border: '1px solid rgba(0, 212, 255, 0.15)',
            backdropFilter: 'blur(12px)',
            borderRadius: '12px',
            fontSize: '14px',
          },
          success: {
            iconTheme: { primary: '#00E68A', secondary: '#0A0E27' },
          },
          error: {
            iconTheme: { primary: '#FF4757', secondary: '#ffffff' },
          },
        }}
      />
    </QueryClientProvider>
  );
}
