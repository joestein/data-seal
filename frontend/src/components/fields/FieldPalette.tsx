import { FieldTypeIcon } from './FieldTypeIcon';
import { FIELD_TYPE_LABELS } from '../../lib/constants';
import type { FieldType, Recipient } from '../../api/types';
import { RECIPIENT_COLORS } from '../../lib/constants';

const FIELD_TYPES: FieldType[] = [
  'signature',
  'initials',
  'date_signed',
  'text',
  'checkbox',
  'dropdown',
];

interface FieldPaletteProps {
  recipients: Recipient[];
  selectedRecipientId: string | null;
  onRecipientChange: (id: string) => void;
  onFieldDragStart: (type: FieldType) => void;
}

export function FieldPalette({
  recipients,
  selectedRecipientId,
  onRecipientChange,
  onFieldDragStart,
}: FieldPaletteProps) {
  const signers = recipients.filter((r) => r.role !== 'cc');

  return (
    <div className="w-52 space-y-4 rounded-lg border border-gray-200 bg-white p-4">
      <div>
        <label className="mb-1 block text-xs font-medium uppercase text-gray-500">
          Assign to
        </label>
        <select
          value={selectedRecipientId ?? ''}
          onChange={(e) => onRecipientChange(e.target.value)}
          className="input-field text-sm"
        >
          {signers.map((r, i) => (
            <option key={r.id} value={r.id}>
              {RECIPIENT_COLORS[i % RECIPIENT_COLORS.length] ? '' : ''}{r.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="mb-2 block text-xs font-medium uppercase text-gray-500">
          Field Types
        </label>
        <div className="space-y-1">
          {FIELD_TYPES.map((type) => (
            <button
              key={type}
              draggable
              onDragStart={() => onFieldDragStart(type)}
              className="flex w-full items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700 hover:border-brand-300 hover:bg-brand-50 cursor-grab active:cursor-grabbing"
            >
              <FieldTypeIcon type={type} className="h-4 w-4 text-gray-500" />
              {FIELD_TYPE_LABELS[type]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
