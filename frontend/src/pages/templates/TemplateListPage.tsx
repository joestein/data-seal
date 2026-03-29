import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Layers, Trash2 } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Modal } from '../../components/common/Modal';
import { Input } from '../../components/common/Input';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { ConfirmDialog } from '../../components/common/ConfirmDialog';
import { useTemplates, useCreateTemplate, useDeleteTemplate } from '../../hooks/useTemplates';
import { formatDate } from '../../lib/utils';
import { ROUTES } from '../../lib/routes';

export function TemplateListPage() {
  const navigate = useNavigate();
  const { data: templates, isLoading } = useTemplates();
  const createTemplate = useCreateTemplate();
  const deleteTemplate = useDeleteTemplate();

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleCreate = () => {
    createTemplate.mutate(
      { name, description: description || undefined },
      {
        onSuccess: (t) => {
          setShowCreate(false);
          setName('');
          setDescription('');
          navigate(ROUTES.TEMPLATE_DETAIL(t.id));
        },
      },
    );
  };

  if (isLoading) return <LoadingSpinner className="py-16" />;

  const list = templates ?? [];

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Templates</h1>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" /> New Template
        </Button>
      </div>

      {list.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="No templates"
          description="Create a template to quickly generate envelopes with pre-configured documents and fields."
          actionLabel="Create Template"
          onAction={() => setShowCreate(true)}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Created</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {list.map((t) => (
                <tr
                  key={t.id}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => navigate(ROUTES.TEMPLATE_DETAIL(t.id))}
                >
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    {t.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {t.description || '-'}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {formatDate(t.created_at)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteId(t.id);
                      }}
                      className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                      aria-label={`Delete ${t.name}`}
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

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Template">
        <div className="space-y-4">
          <Input
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Template name"
          />
          <Input
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description"
          />
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={!name.trim()} loading={createTemplate.isPending}>
              Create
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => {
          if (deleteId) deleteTemplate.mutate(deleteId);
          setDeleteId(null);
        }}
        title="Delete Template"
        message="Are you sure? This cannot be undone."
        confirmLabel="Delete"
        loading={deleteTemplate.isPending}
      />
    </div>
  );
}
