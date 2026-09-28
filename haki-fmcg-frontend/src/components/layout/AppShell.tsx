import { Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { useUIStore } from '@/stores';
import { CommandPalette, ShortcutOverlay } from '@/components/common';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

export function AppShell() {
  const { sidebarCollapsed } = useUIStore();
  useKeyboardShortcuts();

  return (
    <div className="min-h-screen bg-faded-grid text-slate-900">
      <Sidebar />

      <motion.div
        animate={{ marginLeft: sidebarCollapsed ? 64 : 240 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="flex flex-col min-h-screen"
      >
        <TopBar />

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </motion.div>

      <CommandPalette />
      <ShortcutOverlay />
    </div>
  );
}
