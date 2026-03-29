import { FileText, Users, CheckCircle } from 'lucide-react';
import { Button } from '../common/Button';
import { EnvelopeStatusBadge } from '../envelope/EnvelopeStatusBadge';
import { useDocuments } from '../../hooks/useDocuments';
import { useRecipients } from '../../hooks/useRecipients';
import { useSendEnvelope } from '../../hooks/useEnvelopes';
import { useUiStore } from '../../stores/uiStore';
import { formatFileSize } from '../../lib/utils';
import { RECIPIENT_COLORS } from '../../lib/constants';
import type { Envelope } from '../../api/types';

interface StepReviewProps {
  envelope: Envelope;
  onBack: () => void;
  onSent: () => void;
}

export function StepReview({ envelope, onBack, onSent }: StepReviewProps) {
  const { data: documents } = useDocuments(envelope.id);
  const { data: recipients } = useRecipients(envelope.id);
  const send = useSendEnvelope();
  const { addToast } = useUiStore();

  const docs = documents ?? [];
  const recips = recipients ?? [];

  const handleSend = () => {
    send.mutate(envelope.id, {
      onSuccess: () => {
        addToast({ type: 'success', message: 'Envelope sent successfully!' });
        onSent();
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Envelope Summary</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm font-medium text-gray-500">Title</p>
            <p className="text-sm text-gray-900">{envelope.title}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Status</p>
            <EnvelopeStatusBadge status={envelope.status} />
          </div>
          {envelope.message && (
            <div className="col-span-2">
              <p className="text-sm font-medium text-gray-500">Message</p>
              <p className="text-sm text-gray-900">{envelope.message}</p>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-900">
          <FileText className="h-4 w-4" />
          Documents ({docs.length})
        </h3>
        <ul className="space-y-2">
          {docs.map((doc) => (
            <li key={doc.id} className="flex items-center justify-between text-sm">
              <span className="text-gray-900">{doc.filename}</span>
              <span className="text-gray-500">
                {formatFileSize(doc.size_bytes)} - {doc.page_count} page{doc.page_count > 1 ? 's' : ''}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-900">
          <Users className="h-4 w-4" />
          Recipients ({recips.length})
        </h3>
        <ul className="space-y-2">
          {recips.map((r, i) => (
            <li key={r.id} className="flex items-center gap-2 text-sm">
              <div
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: RECIPIENT_COLORS[i % RECIPIENT_COLORS.length] }}
              />
              <span className="font-medium text-gray-900">{r.name}</span>
              <span className="text-gray-500">({r.email})</span>
              <span className="capitalize text-gray-400">{r.role}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack}>
          Back
        </Button>
        <Button onClick={handleSend} loading={send.isPending}>
          <CheckCircle className="mr-2 h-4 w-4" />
          Send Envelope
        </Button>
      </div>
    </div>
  );
}
