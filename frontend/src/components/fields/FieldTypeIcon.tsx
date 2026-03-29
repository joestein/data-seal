import { PenLine, Type, Calendar, CheckSquare, ChevronDown, Fingerprint } from 'lucide-react';
import type { FieldType } from '../../api/types';

const ICONS: Record<FieldType, React.ElementType> = {
  signature: PenLine,
  initials: Fingerprint,
  date_signed: Calendar,
  text: Type,
  checkbox: CheckSquare,
  dropdown: ChevronDown,
};

interface FieldTypeIconProps {
  type: FieldType;
  className?: string;
}

export function FieldTypeIcon({ type, className = 'h-4 w-4' }: FieldTypeIconProps) {
  const Icon = ICONS[type];
  return <Icon className={className} />;
}
