import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '@/stores';

export function useKeyboardShortcuts() {
  const navigate = useNavigate();
  const { setCommandPaletteOpen, setShortcutsOpen } = useUIStore();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Do not trigger shortcuts when typing inside form fields
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.tagName === 'SELECT' ||
          target.isContentEditable)
      ) {
        return;
      }

      const isCmd = e.metaKey || e.ctrlKey;

      if (e.key === '?') {
        e.preventDefault();
        setShortcutsOpen(true);
        return;
      }

      if (isCmd && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
        return;
      }

      if (isCmd && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        navigate('/rfps/upload');
        return;
      }

      if (isCmd && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        navigate('/bids/create');
        return;
      }

      if (isCmd && e.key.toLowerCase() === 'p') {
        e.preventDefault();
        navigate('/pipeline');
        return;
      }

      if (e.key >= '1' && e.key <= '9') {
        const idx = Number(e.key);
        const routes = ['/', '/rfps', '/pipeline', '/agents', '/products', '/bids', '/vendors', '/analytics', '/compliance'];
        const route = routes[idx - 1];
        if (route) {
          navigate(route);
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navigate, setCommandPaletteOpen, setShortcutsOpen]);
}
