import { Modal } from '@/components/ui';
import { useUIStore } from '@/stores';

const shortcuts = [
  { keys: '⌘ + K', action: 'Global Search' },
  { keys: '⌘ + N', action: 'New RFP' },
  { keys: '⌘ + B', action: 'New Bid' },
  { keys: '⌘ + P', action: 'Pipeline View' },
  { keys: '1-9', action: 'Navigate to section' },
  { keys: '?', action: 'Shortcut Help' },
];

export function ShortcutOverlay() {
  const { shortcutsOpen, setShortcutsOpen } = useUIStore();

  return (
    <Modal open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} size="sm" title="Keyboard Shortcuts">
      <div className="space-y-3">
        {shortcuts.map((s) => (
          <div key={s.keys} className="flex items-center justify-between bg-steel-slate/20 rounded-lg px-3 py-2">
            <span className="text-sm text-ghost-white font-medium">{s.action}</span>
            <kbd className="text-xs text-muted-silver bg-steel-slate/40 px-2 py-1 rounded">
              {s.keys}
            </kbd>
          </div>
        ))}
      </div>
    </Modal>
  );
}
