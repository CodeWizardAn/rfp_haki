import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { Modal, Input, Badge } from '@/components/ui';
import { useUIStore } from '@/stores';

const quickActions = [
  { label: 'Dashboard', path: '/', group: 'Navigation' },
  { label: 'RFPs', path: '/rfps', group: 'Navigation' },
  { label: 'Upload RFP', path: '/rfps/upload', group: 'Actions' },
  { label: 'Pipeline', path: '/pipeline', group: 'Navigation' },
  { label: 'Agents', path: '/agents', group: 'Navigation' },
  { label: 'Products', path: '/products', group: 'Navigation' },
  { label: 'Create Bid', path: '/bids/create', group: 'Actions' },
  { label: 'Vendors', path: '/vendors', group: 'Navigation' },
  { label: 'Analytics', path: '/analytics', group: 'Navigation' },
  { label: 'Compliance', path: '/compliance', group: 'Navigation' },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const results = useMemo(() => {
    if (!query) return quickActions;
    const q = query.toLowerCase();
    return quickActions.filter((a) => a.label.toLowerCase().includes(q));
  }, [query]);

  return (
    <Modal
      open={commandPaletteOpen}
      onClose={() => setCommandPaletteOpen(false)}
      size="md"
      title="Command Palette"
      description="Search across modules and quick actions"
    >
      <div className="space-y-4">
        <Input
          placeholder="Search..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          leftIcon={<Search size={16} />}
          autoFocus
        />

        <div className="space-y-2 max-h-72 overflow-y-auto">
          {results.map((item) => (
            <button
              key={item.path}
              onClick={() => {
                navigate(item.path);
                setCommandPaletteOpen(false);
                setQuery('');
              }}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-steel-slate/15 hover:bg-steel-slate/25 transition-colors"
            >
              <span className="text-sm text-ghost-white">{item.label}</span>
              <Badge variant="soft" color="cyan" size="sm">
                {item.group}
              </Badge>
            </button>
          ))}
        </div>
      </div>
    </Modal>
  );
}
