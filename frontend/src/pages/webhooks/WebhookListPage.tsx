import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Webhook, Trash2 } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Modal } from '../../components/common/Modal';
import { Input } from '../../components/common/Input';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { ConfirmDialog } from '../../components/common/ConfirmDialog';
import { Badge } from '../../components/common/Badge';
import { useWebhooks, useCreateWebhook, useDeleteWebhook, useUpdateWebhook } from '../../hooks/useWebhooks';
import { truncateUrl, formatDate } from '../../lib/utils';
import { WEBHOOK_EVENT_TYPES } from '../../lib/constants';
import { ROUTES } from '../../lib/routes';

export function WebhookListPage() {
  const navigate = useNavigate();
  const { data: webhooks, isLoading } = useWebhooks();
  const createWebhook = useCreateWebhook();
  const deleteWebhook = useDeleteWebhook();
  const updateWebhook = useUpdateWebhook();

  const [showCreate, setShowCreate] = useState(false);
  const [url, setUrl] = useState('');
  const [events, setEvents] = useState<string[]>([]);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const toggleEvent = (evt: string) => {
    setEvents((prev) => prev.includes(evt) ? prev.filter((e) => e !== evt) : [...prev, evt]);
  };

  const handleCreate = () => {
    createWebhook.mutate(
      { url, events, is_active: true },
      {
        onSuccess: (wh) => {
          setShowCreate(false);
          setUrl('');
          setEvents([]);
          navigate(ROUTES.WEBHOOK_DETAIL(wh.id));
        },
      },
    );
  };

  if (isLoading) return <LoadingSpinner className="py-16" />;

  const list = webhooks ?? [];

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Webhooks</h1>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" /> New Webhook
        </Button>
      </div>

      {list.length === 0 ? (
        <EmptyState
          icon={Webhook}
          title="No webhooks"
          description="Create a webhook endpoint to receive real-time notifications about envelope events."
          actionLabel="Create Webhook"
          onAction={() => setShowCreate(true)}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">URL</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Events</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Created</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {list.map((wh) => (
                <tr
                  key={wh.id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => navigate(ROUTES.WEBHOOK_DETAIL(wh.id))}
                >
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-mono text-gray-900">
                    {truncateUrl(wh.url)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {wh.events.slice(0, 3).map((evt) => (
                        <Badge key={evt}>{evt}</Badge>
                      ))}
                      {wh.events.length > 3 && (
                        <Badge>+{wh.events.length - 3}</Badge>
                      )}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        updateWebhook.mutate({ id: wh.id, data: { is_active: !wh.is_active } });
                      }}
                    >
                      <Badge
                        bgColor={wh.is_active ? 'bg-green-100' : 'bg-gray-100'}
                        color={wh.is_active ? 'text-green-700' : 'text-gray-500'}
                      >
                        {wh.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </button>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {formatDate(wh.created_at)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right">
                    <button
                      onClick={(e) => { e.stopPropagation(); setDeleteId(wh.id); }}
                      className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                      aria-label="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Webhook" size="lg">
        <div className="space-y-4">
          <Input label="Endpoint URL" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/webhook" />
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">Events</label>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={events.length === WEBHOOK_EVENT_TYPES.length}
                  onChange={() => setEvents(events.length === WEBHOOK_EVENT_TYPES.length ? [] : [...WEBHOOK_EVENT_TYPES])}
                  className="h-4 w-4 rounded border-gray-300 text-brand-600"
                />
                <span className="text-sm font-medium text-gray-700">All Events</span>
              </label>
              {WEBHOOK_EVENT_TYPES.map((evt) => (
                <label key={evt} className="flex items-center gap-2 pl-6">
                  <input
                    type="checkbox"
                    checked={events.includes(evt)}
                    onChange={() => toggleEvent(evt)}
                    className="h-4 w-4 rounded border-gray-300 text-brand-600"
                  />
                  <span className="text-sm text-gray-600">{evt}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!url.trim() || events.length === 0} loading={createWebhook.isPending}>Create</Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => { if (deleteId) deleteWebhook.mutate(deleteId); setDeleteId(null); }}
        title="Delete Webhook"
        message="This will delete the webhook and all its delivery logs."
        confirmLabel="Delete"
        loading={deleteWebhook.isPending}
      />
    </div>
  );
}
