import { useNavigate } from 'react-router-dom';
import { Users } from 'lucide-react';
import { EnvelopeStatusBadge } from './EnvelopeStatusBadge';
import { formatRelativeTime } from '../../lib/utils';
import { ROUTES } from '../../lib/routes';
import type { Envelope } from '../../api/types';

interface EnvelopeCardProps {
  envelope: Envelope;
}

export function EnvelopeCard({ envelope }: EnvelopeCardProps) {
  const navigate = useNavigate();

  return (
    <tr
      className="cursor-pointer hover:bg-gray-50"
      onClick={() => navigate(ROUTES.ENVELOPE_DETAIL(envelope.id))}
    >
      <td className="whitespace-nowrap px-6 py-4">
        <p className="text-sm font-medium text-gray-900">{envelope.title}</p>
      </td>
      <td className="whitespace-nowrap px-6 py-4">
        <EnvelopeStatusBadge status={envelope.status} />
      </td>
      <td className="whitespace-nowrap px-6 py-4">
        <div className="flex items-center gap-1 text-sm text-gray-500">
          <Users className="h-4 w-4" />
        </div>
      </td>
      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
        {formatRelativeTime(envelope.updated_at)}
      </td>
    </tr>
  );
}
