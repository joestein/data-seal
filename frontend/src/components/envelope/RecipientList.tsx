import { Badge } from '../common/Badge';
import { formatDateTime } from '../../lib/utils';
import { RECIPIENT_COLORS } from '../../lib/constants';
import type { Recipient } from '../../api/types';

interface RecipientListProps {
  recipients: Recipient[];
}

const STATUS_MAP: Record<string, { bg: string; text: string }> = {
  created: { bg: 'bg-gray-100', text: 'text-gray-700' },
  sent: { bg: 'bg-blue-100', text: 'text-blue-700' },
  delivered: { bg: 'bg-indigo-100', text: 'text-indigo-700' },
  signed: { bg: 'bg-green-100', text: 'text-green-700' },
  declined: { bg: 'bg-red-100', text: 'text-red-700' },
};

export function RecipientList({ recipients }: RecipientListProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Email</th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Role</th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Order</th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Timestamp</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {recipients.map((r, i) => {
            const colors = STATUS_MAP[r.status] ?? STATUS_MAP.created;
            return (
              <tr key={r.id}>
                <td className="whitespace-nowrap px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: RECIPIENT_COLORS[i % RECIPIENT_COLORS.length] }}
                    />
                    <span className="text-sm font-medium text-gray-900">{r.name}</span>
                  </div>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{r.email}</td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 capitalize">{r.role}</td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{r.routing_order}</td>
                <td className="whitespace-nowrap px-6 py-4">
                  <Badge bgColor={colors.bg} color={colors.text}>
                    {r.status}
                  </Badge>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {r.signed_at ? formatDateTime(r.signed_at) : r.declined_at ? formatDateTime(r.declined_at) : '-'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
