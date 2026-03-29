import { Check } from 'lucide-react';
import { clsx } from 'clsx';

const STEPS = ['Documents', 'Recipients', 'Fields', 'Review'];

interface WizardStepperProps {
  currentStep: number;
}

export function WizardStepper({ currentStep }: WizardStepperProps) {
  return (
    <nav className="mb-8" aria-label="Wizard progress">
      <ol className="flex items-center gap-2">
        {STEPS.map((label, idx) => {
          const done = idx < currentStep;
          const active = idx === currentStep;
          return (
            <li key={label} className="flex items-center gap-2">
              <div className="flex items-center gap-2">
                <div
                  className={clsx(
                    'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium',
                    done
                      ? 'bg-brand-600 text-white'
                      : active
                        ? 'border-2 border-brand-600 text-brand-600'
                        : 'border border-gray-300 text-gray-400',
                  )}
                >
                  {done ? <Check className="h-4 w-4" /> : idx + 1}
                </div>
                <span
                  className={clsx(
                    'text-sm font-medium',
                    done || active ? 'text-brand-700' : 'text-gray-400',
                  )}
                >
                  {label}
                </span>
              </div>
              {idx < STEPS.length - 1 && (
                <div
                  className={clsx('h-0.5 w-12', done ? 'bg-brand-600' : 'bg-gray-200')}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
