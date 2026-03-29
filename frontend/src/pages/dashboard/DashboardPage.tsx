import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Inbox, Search } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Pagination } from '../../components/common/Pagination';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { EnvelopeCard } from '../../components/envelope/EnvelopeCard';
import { useEnvelopes } from '../../hooks/useEnvelopes';
import { ROUTES } from '../../lib/routes';
import { PAGE_SIZE, DEBOUNCE_MS } from '../../lib/constants';
import type { EnvelopeStatus } from '../../api/types';

const STATUS_TABS: Array<{ label: string; value: EnvelopeStatus | undefined }> = [
  { label: 'All', value: undefined },
  { label: 'Draft', value: 'created' },
  { label: 'Sent', value: 'sent' },
  { label: 'Delivered', value: 'delivered' },
  { label: 'Completed', value: 'completed' },
  { label: 'Voided', value: 'voided' },
  { label: 'Declined', value: 'declined' },
];

export function DashboardPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<EnvelopeStatus | undefined>();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  const { data, isLoading } = useEnvelopes({
    page,
    page_size: PAGE_SIZE,
    status,
    search: search || undefined,
  });

  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const handleSearchInput = useCallback((value: string) => {
    setSearchInput(value);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setSearch(value);
      setPage(1);
    }, DEBOUNCE_MS);
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Envelopes</h1>
        <Button onClick={() => navigate(ROUTES.ENVELOPE_NEW)}>
          <Plus className="mr-2 h-4 w-4" />
          New Envelope
        </Button>
      </div>

      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.label}
              onClick={() => {
                setStatus(tab.value);
                setPage(1);
              }}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                status === tab.value
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => handleSearchInput(e.target.value)}
            placeholder="Search envelopes..."
            className="input-field pl-9"
          />
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner className="py-16" />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title="No envelopes yet"
          description="Create your first envelope to start sending documents for signing."
          actionLabel="Create Envelope"
          onAction={() => navigate(ROUTES.ENVELOPE_NEW)}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  Recipients
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  Updated
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.items.map((envelope) => (
                <EnvelopeCard key={envelope.id} envelope={envelope} />
              ))}
            </tbody>
          </table>
          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onPageChange={setPage}
          />
        </div>
      )}
    </div>
  );
}
