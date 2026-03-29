import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EnvelopeStatusBadge } from '../../components/envelope/EnvelopeStatusBadge';
import type { EnvelopeStatus } from '../../api/types';

const ALL_STATUSES: EnvelopeStatus[] = [
  'created',
  'sent',
  'delivered',
  'signed',
  'completed',
  'voided',
  'declined',
];

describe('EnvelopeStatusBadge', () => {
  it('should render the status capitalized', () => {
    render(<EnvelopeStatusBadge status="created" />);
    expect(screen.getByText('Created')).toBeInTheDocument();
  });

  it('should render for every possible status without crashing', () => {
    ALL_STATUSES.forEach((status) => {
      const { unmount } = render(<EnvelopeStatusBadge status={status} />);
      const expectedText = status.charAt(0).toUpperCase() + status.slice(1);
      expect(screen.getByText(expectedText)).toBeInTheDocument();
      unmount();
    });
  });

  it('should display "Completed" for completed status', () => {
    render(<EnvelopeStatusBadge status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('should display "Voided" for voided status', () => {
    render(<EnvelopeStatusBadge status="voided" />);
    expect(screen.getByText('Voided')).toBeInTheDocument();
  });
});
