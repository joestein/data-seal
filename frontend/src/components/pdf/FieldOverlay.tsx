import { clsx } from 'clsx';
import { FieldTypeIcon } from '../fields/FieldTypeIcon';
import { RECIPIENT_COLORS } from '../../lib/constants';
import type { DocumentField, Recipient } from '../../api/types';

interface FieldOverlayProps {
  field: DocumentField;
  recipients: Recipient[];
}

export function FieldOverlay({ field, recipients }: FieldOverlayProps) {
  const recipientIdx = recipients.findIndex((r) => r.id === field.recipient_id);
  const color = RECIPIENT_COLORS[recipientIdx % RECIPIENT_COLORS.length] || '#3b82f6';

  return (
    <div
      className={clsx(
        'absolute flex items-center justify-center rounded border text-xs',
        field.value ? 'border-green-400 bg-green-50' : 'border-dashed',
      )}
      style={{
        left: `${field.x_position}%`,
        top: `${field.y_position}%`,
        width: `${field.width}%`,
        height: `${field.height}%`,
        borderColor: field.value ? undefined : color,
        backgroundColor: field.value ? undefined : color + '15',
      }}
    >
      <FieldTypeIcon type={field.type} className="h-3 w-3 opacity-60" />
    </div>
  );
}
