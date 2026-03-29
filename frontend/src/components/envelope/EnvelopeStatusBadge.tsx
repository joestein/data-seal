import { Badge } from '../common/Badge';
import { STATUS_COLORS } from '../../lib/constants';
import type { EnvelopeStatus } from '../../api/types';

interface EnvelopeStatusBadgeProps {
  status: EnvelopeStatus;
}

export function EnvelopeStatusBadge({ status }: EnvelopeStatusBadgeProps) {
  const colors = STATUS_COLORS[status];
  return (
    <Badge bgColor={colors.bg} color={colors.text}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}
