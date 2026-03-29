import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Download, Send, XCircle, RefreshCw, ArrowLeft } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ConfirmDialog } from '../../components/common/ConfirmDialog';
import { Modal } from '../../components/common/Modal';
import { EnvelopeStatusBadge } from '../../components/envelope/EnvelopeStatusBadge';
import { EnvelopeTimeline } from '../../components/envelope/EnvelopeTimeline';
import { RecipientList } from '../../components/envelope/RecipientList';
import { AuditTrailViewer } from '../../components/envelope/AuditTrailViewer';
import {
  useEnvelope,
  useSendEnvelope,
  useVoidEnvelope,
  useResendEnvelope,
  useAuditTrail,
  useDeleteEnvelope,
} from '../../hooks/useEnvelopes';
import { useDocuments } from '../../hooks/useDocuments';
import { useRecipients } from '../../hooks/useRecipients';
import { downloadCompleted, downloadCertificate } from '../../api/envelopes';
import { formatDateTime, formatFileSize, downloadBlob } from '../../lib/utils';
import { useUiStore } from '../../stores/uiStore';
import { ROUTES } from '../../lib/routes';

type Tab = 'recipients' | 'documents' | 'audit';

export function EnvelopeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useUiStore();

  const { data: envelope, isLoading } = useEnvelope(id!);
  const { data: documents } = useDocuments(id!);
  const { data: recipients } = useRecipients(id!);
  const { data: auditEvents } = useAuditTrail(id!);

  const sendEnvelope = useSendEnvelope();
  const voidEnvelope = useVoidEnvelope();
  const resendEnvelope = useResendEnvelope();
  const deleteEnvelope = useDeleteEnvelope();

  const [activeTab, setActiveTab] = useState<Tab>('recipients');
  const [showVoidModal, setShowVoidModal] = useState(false);
  const [voidReason, setVoidReason] = useState('');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  if (isLoading || !envelope) {
    return <LoadingSpinner className="py-16" />;
  }

  const handleVoid = () => {
    voidEnvelope.mutate(
      { id: envelope.id, data: { reason: voidReason } },
      {
        onSuccess: () => {
          setShowVoidModal(false);
          addToast({ type: 'success', message: 'Envelope voided' });
        },
      },
    );
  };

  const handleDelete = () => {
    deleteEnvelope.mutate(envelope.id, {
      onSuccess: () => {
        navigate(ROUTES.DASHBOARD);
        addToast({ type: 'success', message: 'Envelope deleted' });
      },
    });
  };

  const handleDownloadCompleted = async () => {
    const blob = await downloadCompleted(envelope.id);
    downloadBlob(blob, `${envelope.title}-completed.pdf`);
  };

  const handleDownloadCertificate = async () => {
    const blob = await downloadCertificate(envelope.id);
    downloadBlob(blob, `${envelope.title}-certificate.pdf`);
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'recipients', label: `Recipients (${recipients?.length ?? 0})` },
    { key: 'documents', label: `Documents (${documents?.length ?? 0})` },
    { key: 'audit', label: 'Audit Trail' },
  ];

  return (
    <div>
      <button
        onClick={() => navigate(ROUTES.DASHBOARD)}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Dashboard
      </button>

      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{envelope.title}</h1>
            <EnvelopeStatusBadge status={envelope.status} />
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Created {formatDateTime(envelope.created_at)} | Updated {formatDateTime(envelope.updated_at)}
          </p>
          <div className="mt-3">
            <EnvelopeTimeline currentStatus={envelope.status} />
          </div>
        </div>

        <div className="flex gap-2">
          {envelope.status === 'created' && (
            <>
              <Button
                onClick={() =>
                  sendEnvelope.mutate(envelope.id, {
                    onSuccess: () => addToast({ type: 'success', message: 'Envelope sent!' }),
                  })
                }
                loading={sendEnvelope.isPending}
              >
                <Send className="mr-1 h-4 w-4" /> Send
              </Button>
              <Button variant="danger" onClick={() => setShowDeleteDialog(true)}>
                Delete
              </Button>
            </>
          )}
          {(envelope.status === 'sent' || envelope.status === 'delivered') && (
            <>
              <Button
                variant="secondary"
                onClick={() =>
                  resendEnvelope.mutate(envelope.id, {
                    onSuccess: () => addToast({ type: 'success', message: 'Emails resent' }),
                  })
                }
                loading={resendEnvelope.isPending}
              >
                <RefreshCw className="mr-1 h-4 w-4" /> Resend
              </Button>
              <Button variant="danger" onClick={() => setShowVoidModal(true)}>
                <XCircle className="mr-1 h-4 w-4" /> Void
              </Button>
            </>
          )}
          {envelope.status === 'completed' && (
            <>
              <Button variant="secondary" onClick={handleDownloadCompleted}>
                <Download className="mr-1 h-4 w-4" /> Download PDF
              </Button>
              <Button variant="secondary" onClick={handleDownloadCertificate}>
                <Download className="mr-1 h-4 w-4" /> Certificate
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="mb-4 border-b border-gray-200">
        <div className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`border-b-2 pb-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'border-brand-600 text-brand-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'recipients' && <RecipientList recipients={recipients ?? []} />}
      {activeTab === 'documents' && (
        <div className="rounded-lg border border-gray-200 bg-white">
          <ul className="divide-y divide-gray-200">
            {(documents ?? []).map((doc) => (
              <li key={doc.id} className="flex items-center justify-between px-6 py-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(doc.size_bytes)} - {doc.page_count} page
                    {doc.page_count > 1 ? 's' : ''}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
      {activeTab === 'audit' && <AuditTrailViewer events={auditEvents ?? []} />}

      <Modal open={showVoidModal} onClose={() => setShowVoidModal(false)} title="Void Envelope">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            This will cancel the envelope and notify all recipients.
          </p>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Reason</label>
            <textarea
              className="input-field"
              rows={3}
              value={voidReason}
              onChange={(e) => setVoidReason(e.target.value)}
              placeholder="Enter a reason for voiding..."
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowVoidModal(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleVoid}
              loading={voidEnvelope.isPending}
              disabled={!voidReason.trim()}
            >
              Void Envelope
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="Delete Envelope"
        message="Are you sure you want to delete this envelope? This action cannot be undone."
        confirmLabel="Delete"
        loading={deleteEnvelope.isPending}
      />
    </div>
  );
}
