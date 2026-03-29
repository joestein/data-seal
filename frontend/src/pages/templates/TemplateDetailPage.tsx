import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Modal } from '../../components/common/Modal';
import { useTemplate, useUpdateTemplate, useTemplateDocuments, useTemplateRecipients, useCreateEnvelopeFromTemplate } from '../../hooks/useTemplates';
import { formatFileSize } from '../../lib/utils';
import { useUiStore } from '../../stores/uiStore';
import { ROUTES } from '../../lib/routes';

export function TemplateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useUiStore();

  const { data: template, isLoading } = useTemplate(id!);
  const { data: documents } = useTemplateDocuments(id!);
  const { data: recipients } = useTemplateRecipients(id!);
  const updateTemplate = useUpdateTemplate();
  const createFromTemplate = useCreateEnvelopeFromTemplate();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [showCreateEnvelope, setShowCreateEnvelope] = useState(false);
  const [envelopeTitle, setEnvelopeTitle] = useState('');
  const [recipientMap, setRecipientMap] = useState<Record<string, { name: string; email: string }>>({});

  // Initialize form when template loads
  if (template && !name) {
    setName(template.name);
    setDescription(template.description ?? '');
  }

  if (isLoading || !template) return <LoadingSpinner className="py-16" />;

  const handleSave = () => {
    updateTemplate.mutate(
      { id: template.id, data: { name, description: description || null } },
      { onSuccess: () => addToast({ type: 'success', message: 'Template saved' }) },
    );
  };

  const handleCreateEnvelope = () => {
    createFromTemplate.mutate(
      {
        templateId: template.id,
        data: { title: envelopeTitle, recipients: recipientMap },
      },
      {
        onSuccess: (env) => {
          setShowCreateEnvelope(false);
          navigate(ROUTES.ENVELOPE_DETAIL(env.id));
        },
      },
    );
  };

  const recips = recipients ?? [];
  const docs = documents ?? [];

  return (
    <div>
      <button
        onClick={() => navigate(ROUTES.TEMPLATES)}
        className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Templates
      </button>

      <div className="mb-6 flex items-start justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Edit Template</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => {
            setEnvelopeTitle(template.name);
            const map: Record<string, { name: string; email: string }> = {};
            recips.forEach((r) => { map[r.role_name] = { name: '', email: '' }; });
            setRecipientMap(map);
            setShowCreateEnvelope(true);
          }}>
            Create Envelope
          </Button>
          <Button onClick={handleSave} loading={updateTemplate.isPending}>
            <Save className="mr-1 h-4 w-4" /> Save
          </Button>
        </div>
      </div>

      <div className="space-y-6">
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Input
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Documents ({docs.length})</h3>
          {docs.length === 0 ? (
            <p className="text-sm text-gray-500">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-2">
              {docs.map((doc) => (
                <li key={doc.id} className="flex items-center justify-between text-sm">
                  <span className="text-gray-900">{doc.filename}</span>
                  <span className="text-gray-500">{formatFileSize(doc.size_bytes)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Recipients ({recips.length})</h3>
          {recips.length === 0 ? (
            <p className="text-sm text-gray-500">No recipients defined.</p>
          ) : (
            <ul className="space-y-2">
              {recips.map((r) => (
                <li key={r.id} className="flex items-center gap-4 text-sm">
                  <span className="font-medium text-gray-900">{r.role_name}</span>
                  <span className="text-gray-500 capitalize">{r.role}</span>
                  <span className="text-gray-400">Order: {r.routing_order}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <Modal open={showCreateEnvelope} onClose={() => setShowCreateEnvelope(false)} title="Create Envelope from Template" size="lg">
        <div className="space-y-4">
          <Input
            label="Envelope Title"
            value={envelopeTitle}
            onChange={(e) => setEnvelopeTitle(e.target.value)}
          />
          <h4 className="text-sm font-medium text-gray-700">Map Recipients</h4>
          {recips.map((r) => (
            <div key={r.id} className="grid grid-cols-3 gap-3">
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-600">{r.role_name}</span>
              </div>
              <Input
                placeholder="Name"
                value={recipientMap[r.role_name]?.name ?? ''}
                onChange={(e) =>
                  setRecipientMap((prev) => ({
                    ...prev,
                    [r.role_name]: { ...prev[r.role_name], name: e.target.value },
                  }))
                }
              />
              <Input
                placeholder="Email"
                type="email"
                value={recipientMap[r.role_name]?.email ?? ''}
                onChange={(e) =>
                  setRecipientMap((prev) => ({
                    ...prev,
                    [r.role_name]: { ...prev[r.role_name], email: e.target.value },
                  }))
                }
              />
            </div>
          ))}
          <div className="flex justify-end gap-3 border-t border-gray-200 pt-4">
            <Button variant="secondary" onClick={() => setShowCreateEnvelope(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateEnvelope}
              loading={createFromTemplate.isPending}
              disabled={!envelopeTitle.trim()}
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
