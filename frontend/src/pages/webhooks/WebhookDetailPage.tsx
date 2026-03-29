import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, ExternalLink } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Badge } from '../../components/common/Badge';
import { useWebhook, useTestWebhook, useWebhookDeliveries } from '../../hooks/useWebhooks';
import { formatDateTime } from '../../lib/utils';
import { useUiStore } from '../../stores/uiStore';
import { ROUTES } from '../../lib/routes';

export function WebhookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useUiStore();

  const { data: webhook, isLoading } = useWebhook(id!);
  const { data: deliveries } = useWebhookDeliveries(id!);
  const testWebhook = useTestWebhook();

  if (isLoading || !webhook) return <LoadingSpinner className="py-16" />;

  const handleTest = () => {
    testWebhook.mutate(webhook.id, {
      onSuccess: () => addToast({ type: 'success', message: 'Test event sent' }),
    });
  };

  return (
    <div>
      <button
        onClick={() => navigate(ROUTES.WEBHOOKS)}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Webhooks
      </button>

      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Webhook Details</h1>
          <p className="mt-1 flex items-center gap-2 font-mono text-sm text-gray-600">
            <ExternalLink className="h-4 w-4" />
            {webhook.url}
          </p>
        </div>
        <Button onClick={handleTest} loading={testWebhook.isPending}>
          <Send className="mr-1 h-4 w-4" /> Send Test
        </Button>
      </div>

      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm font-medium text-gray-500">Status</p>
            <Badge
              bgColor={webhook.is_active ? 'bg-green-100' : 'bg-gray-100'}
              color={webhook.is_active ? 'text-green-700' : 'text-gray-500'}
            >
              {webhook.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Events</p>
            <div className="mt-1 flex flex-wrap gap-1">
              {webhook.events.map((evt) => (
                <Badge key={evt}>{evt}</Badge>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Created</p>
            <p className="text-sm text-gray-900">{formatDateTime(webhook.created_at)}</p>
          </div>
        </div>
      </div>

      <h2 className="mb-4 text-lg font-semibold text-gray-900">Delivery Log</h2>
      {!deliveries || deliveries.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">No deliveries yet.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Event</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">HTTP Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Attempts</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {deliveries.map((d) => (
                <tr key={d.id}>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{d.event_type}</td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <Badge
                      bgColor={d.status === 'delivered' ? 'bg-green-100' : d.status === 'failed' ? 'bg-red-100' : 'bg-amber-100'}
                      color={d.status === 'delivered' ? 'text-green-700' : d.status === 'failed' ? 'text-red-700' : 'text-amber-700'}
                    >
                      {d.status}
                    </Badge>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {d.response_status ?? '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {d.attempt_count}/{d.max_attempts}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {formatDateTime(d.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
