import { Trash2 } from 'lucide-react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { FieldTypeIcon } from './FieldTypeIcon';
import { FIELD_TYPE_LABELS } from '../../lib/constants';
import type { DocumentField, Recipient } from '../../api/types';

interface FieldConfigPanelProps {
  field: DocumentField | null;
  recipients: Recipient[];
  onUpdate: (fieldId: string, updates: Record<string, unknown>) => void;
  onDelete: (fieldId: string) => void;
}

export function FieldConfigPanel({ field, recipients, onUpdate, onDelete }: FieldConfigPanelProps) {
  if (!field) {
    return (
      <div className="w-64 rounded-lg border border-gray-200 bg-white p-4">
        <p className="text-sm text-gray-500">Select a field on the canvas to edit its properties.</p>
      </div>
    );
  }

  const recipient = recipients.find((r) => r.id === field.recipient_id);

  return (
    <div className="w-64 space-y-4 rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center gap-2">
        <FieldTypeIcon type={field.type} className="h-5 w-5 text-brand-600" />
        <h3 className="text-sm font-semibold text-gray-900">
          {FIELD_TYPE_LABELS[field.type]}
        </h3>
      </div>

      <div>
        <p className="text-xs font-medium text-gray-500">Assigned to</p>
        <p className="text-sm text-gray-900">{recipient?.name ?? 'Unknown'}</p>
      </div>

      <div className="flex items-center justify-between">
        <label className="text-sm text-gray-700">Required</label>
        <input
          type="checkbox"
          checked={field.is_required}
          onChange={(e) => onUpdate(field.id, { is_required: e.target.checked })}
          className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
        />
      </div>

      {(field.type === 'text' || field.type === 'signature') && (
        <Input
          label="Placeholder"
          value={field.placeholder ?? ''}
          onChange={(e) => onUpdate(field.id, { placeholder: e.target.value || null })}
          placeholder="Placeholder text"
        />
      )}

      {field.type === 'text' && (
        <Input
          label="Validation Rule"
          value={field.validation_rule ?? ''}
          onChange={(e) => onUpdate(field.id, { validation_rule: e.target.value || null })}
          placeholder="e.g., regex pattern"
        />
      )}

      {field.type === 'dropdown' && (
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Options</label>
          <textarea
            className="input-field text-sm"
            rows={3}
            value={(field.dropdown_options ?? []).join('\n')}
            onChange={(e) =>
              onUpdate(field.id, {
                dropdown_options: e.target.value.split('\n').filter(Boolean),
              })
            }
            placeholder="One option per line"
          />
        </div>
      )}

      <div className="border-t border-gray-200 pt-4">
        <p className="mb-2 text-xs text-gray-500">
          Position: ({field.x_position.toFixed(1)}%, {field.y_position.toFixed(1)}%) |
          Size: {field.width.toFixed(1)}% x {field.height.toFixed(1)}%
        </p>
        <Button
          variant="danger"
          size="sm"
          onClick={() => onDelete(field.id)}
          className="w-full"
        >
          <Trash2 className="mr-1 h-4 w-4" />
          Delete Field
        </Button>
      </div>
    </div>
  );
}
