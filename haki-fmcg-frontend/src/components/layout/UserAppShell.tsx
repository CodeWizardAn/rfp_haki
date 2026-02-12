import { Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';
import { UserSidebar } from './UserSidebar';
import { UserTopBar } from './UserTopBar';
import { useUIStore } from '@/stores';

export function UserAppShell() {
  const { sidebarCollapsed } = useUIStore();

  return (
    <div className="min-h-screen bg-deep-navy">
      <UserSidebar />

      <motion.div
        animate={{ marginLeft: sidebarCollapsed ? 64 : 240 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="flex flex-col min-h-screen"
      >
        <UserTopBar />

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </motion.div>
    </div>
  );
}
