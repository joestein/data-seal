import { useState } from 'react';
import { Plus, Zap, Trash2, Copy, ExternalLink } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Modal } from '../../components/common/Modal';
import { Input } from '../../components/common/Input';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { ConfirmDialog } from '../../components/common/ConfirmDialog';
import { Badge } from '../../components/common/Badge';
import { usePowerForms, useCreatePowerForm, useUpdatePowerForm, useDeletePowerForm } from '../../hooks/usePowerForms';
import { useTemplates } from '../../hooks/useTemplates';
import { formatDate, slugify, copyToClipboard } from '../../lib/utils';
import { useUiStore } from '../../stores/uiStore';

export function PowerFormListPage() {
  const { data: powerforms, isLoading } = usePowerForms();
  const { data: templates } = useTemplates();
  const createPowerForm = useCreatePowerForm();
  const updatePowerForm = useUpdatePowerForm();
  const deletePowerForm = useDeletePowerForm();
  const { addToast } = useUiStore();

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [templateId, setTemplateId] = useState('');
  const [maxUses, setMaxUses] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleCreate = () => {
    createPowerForm.mutate(
      {
        template_id: templateId,
        name,
        slug,
        max_uses: maxUses ? Number(maxUses) : undefined,
      },
      {
        onSuccess: () => {
          setShowCreate(false);
          setName('');
          setSlug('');
          setTemplateId('');
          setMaxUses('');
          addToast({ type: 'success', message: 'PowerForm created' });
        },
      },
    );
  };

  const handleToggleActive = (id: string, currentActive: boolean) => {
    updatePowerForm.mutate({ id, data: { is_active: !currentActive } });
  };

  if (isLoading) return <LoadingSpinner className="py-16" />;

  const list = powerforms ?? [];

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">PowerForms</h1>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" /> New PowerForm
        </Button>
      </div>

      {list.length === 0 ? (
        <EmptyState
          icon={Zap}
          title="No PowerForms"
          description="Create a PowerForm to let external users submit signed documents via a public link."
          actionLabel="Create PowerForm"
          onAction={() => setShowCreate(true)}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Slug</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Uses</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Created</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {list.map((pf) => (
                <tr key={pf.id}>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">{pf.name}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 font-mono">/p/{pf.slug}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {pf.use_count}{pf.max_uses ? ` / ${pf.max_uses}` : ''}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <button onClick={() => handleToggleActive(pf.id, pf.is_active)}>
                      <Badge
                        bgColor={pf.is_active ? 'bg-green-100' : 'bg-gray-100'}
                        color={pf.is_active ? 'text-green-700' : 'text-gray-500'}
                      >
                        {pf.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </button>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{formatDate(pf.created_at)}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => {
                          copyToClipboard(`${window.location.origin}/p/${pf.slug}`);
                          addToast({ type: 'info', message: 'URL copied!' });
                        }}
                        className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                        aria-label="Copy URL"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <a
                        href={`/p/${pf.slug}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                        aria-label="Open"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                      <button
                        onClick={() => setDeleteId(pf.id)}
                        className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                        aria-label="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create PowerForm">
        <div className="space-y-4">
          <Input label="Name" value={name} onChange={(e) => { setName(e.target.value); setSlug(slugify(e.target.value)); }} placeholder="PowerForm name" />
          <Input label="Slug" value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="url-slug" />
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Template</label>
            <select value={templateId} onChange={(e) => setTemplateId(e.target.value)} className="input-field">
              <option value="">Select a template...</option>
              {(templates ?? []).map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
          <Input label="Max Uses (optional)" type="number" value={maxUses} onChange={(e) => setMaxUses(e.target.value)} placeholder="Unlimited" />
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!name.trim() || !slug.trim() || !templateId} loading={createPowerForm.isPending}>Create</Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => { if (deleteId) deletePowerForm.mutate(deleteId); setDeleteId(null); }}
        title="Delete PowerForm"
        message="Are you sure? This cannot be undone."
        confirmLabel="Delete"
        loading={deletePowerForm.isPending}
      />
    </div>
  );
}
