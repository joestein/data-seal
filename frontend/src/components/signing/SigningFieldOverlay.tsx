import { clsx } from 'clsx';
import { Check, PenLine, Fingerprint, Calendar, Type, CheckSquare, ChevronDown } from 'lucide-react';
import type { SigningField } from '../../api/types';

interface SigningFieldOverlayProps {
  field: SigningField;
  onClick: (fieldId: string) => void;
}

const ICONS = {
  signature: PenLine,
  initials: Fingerprint,
  date_signed: Calendar,
  text: Type,
  checkbox: CheckSquare,
  dropdown: ChevronDown,
};

export function SigningFieldOverlay({ field, onClick }: SigningFieldOverlayProps) {
  const isFilled = !!field.value;
  const Icon = ICONS[field.type];

  return (
    <button
      onClick={() => onClick(field.id)}
      className={clsx(
        'absolute flex items-center justify-center rounded border-2 transition-all',
        isFilled
          ? 'border-green-400 bg-green-50/80'
          : field.is_required
            ? 'border-blue-400 bg-blue-50/80 field-pulse cursor-pointer hover:border-blue-600'
            : 'border-gray-300 bg-gray-50/80 cursor-pointer hover:border-gray-500',
      )}
      style={{
        left: `${field.x_position}%`,
        top: `${field.y_position}%`,
        width: `${field.width}%`,
        height: `${field.height}%`,
      }}
      aria-label={`${field.type} field${field.is_required ? ' (required)' : ''}`}
    >
      {isFilled ? (
        <div className="flex items-center gap-1">
          <Check className="h-3 w-3 text-green-600" />
          {field.type === 'text' && (
            <span className="truncate text-xs text-gray-700">{field.value}</span>
          )}
          {field.type === 'checkbox' && (
            <CheckSquare className="h-4 w-4 text-green-600" />
          )}
        </div>
      ) : (
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Icon className="h-3 w-3" />
          <span className="hidden sm:inline">{field.placeholder ?? field.type}</span>
        </div>
      )}
    </button>
  );
}
