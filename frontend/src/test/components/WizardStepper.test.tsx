import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WizardStepper } from '../../components/wizard/WizardStepper';

const STEPS = ['Documents', 'Recipients', 'Fields', 'Review'];

describe('WizardStepper', () => {
  it('should render all 4 step labels', () => {
    render(<WizardStepper currentStep={0} />);
    STEPS.forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it('should show step numbers for future steps when on step 0', () => {
    render(<WizardStepper currentStep={0} />);
    // Steps 1, 2, 3, 4 (1-based) shown as numbers for pending steps
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('should not show checkmarks when on step 0 (nothing completed)', () => {
    const { container } = render(<WizardStepper currentStep={0} />);
    // Check icons are lucide SVGs - when done steps have check icon
    // On step 0 there are no completed steps so no check svgs
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBe(0);
  });

  it('should show checkmarks for completed steps', () => {
    const { container } = render(<WizardStepper currentStep={2} />);
    // Steps 0 and 1 are done (idx < currentStep=2), they should have check icons
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBe(2);
  });

  it('should render nav with aria-label for accessibility', () => {
    render(<WizardStepper currentStep={0} />);
    expect(screen.getByRole('navigation', { name: 'Wizard progress' })).toBeInTheDocument();
  });

  it('should render an ordered list', () => {
    render(<WizardStepper currentStep={0} />);
    expect(screen.getByRole('list')).toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(4);
  });

  it('should handle last step (step 3) without crashing', () => {
    render(<WizardStepper currentStep={3} />);
    expect(screen.getByText('Review')).toBeInTheDocument();
  });

  it('should handle completed state (all steps done) without crashing', () => {
    const { container } = render(<WizardStepper currentStep={4} />);
    // All 4 steps done: 4 check icons
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBe(4);
  });
});
