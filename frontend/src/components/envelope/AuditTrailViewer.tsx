import { Clock } from 'lucide-react';
import { formatDateTime } from '../../lib/utils';
import type { AuditEvent } from '../../api/types';

interface AuditTrailViewerProps {
  events: AuditEvent[];
}

export function AuditTrailViewer({ events }: AuditTrailViewerProps) {
  if (events.length === 0) {
    return <p className="py-8 text-center text-sm text-gray-500">No audit events yet.</p>;
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {events.map((event, idx) => (
          <li key={event.id}>
            <div className="relative pb-8">
              {idx < events.length - 1 && (
                <span className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200" />
              )}
              <div className="relative flex items-start gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100">
                  <Clock className="h-4 w-4 text-gray-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-900">{event.description}</p>
                  <div className="mt-1 flex flex-wrap gap-4 text-xs text-gray-500">
                    <span>{formatDateTime(event.created_at)}</span>
                    {event.ip_address && <span>IP: {event.ip_address}</span>}
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
