import { Check } from 'lucide-react';
import { clsx } from 'clsx';
import type { EnvelopeStatus } from '../../api/types';

const STEPS: EnvelopeStatus[] = ['created', 'sent', 'delivered', 'completed'];

interface EnvelopeTimelineProps {
  currentStatus: EnvelopeStatus;
}

export function EnvelopeTimeline({ currentStatus }: EnvelopeTimelineProps) {
  const currentIdx = STEPS.indexOf(currentStatus);
  const isTerminal = currentStatus === 'voided' || currentStatus === 'declined';

  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, idx) => {
        const done = !isTerminal && idx <= currentIdx;
        return (
          <div key={step} className="flex items-center gap-2">
            <div
              className={clsx(
                'flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium',
                done
                  ? 'bg-brand-600 text-white'
                  : 'border border-gray-300 bg-white text-gray-400',
              )}
            >
              {done ? <Check className="h-4 w-4" /> : idx + 1}
            </div>
            <span
              className={clsx(
                'text-xs font-medium capitalize',
                done ? 'text-brand-700' : 'text-gray-400',
              )}
            >
              {step}
            </span>
            {idx < STEPS.length - 1 && (
              <div
                className={clsx(
                  'h-0.5 w-8',
                  done && idx < currentIdx ? 'bg-brand-600' : 'bg-gray-200',
                )}
              />
            )}
          </div>
        );
      })}
      {isTerminal && (
        <div className="ml-2 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 text-red-700">
            !
          </div>
          <span className="text-xs font-medium capitalize text-red-700">{currentStatus}</span>
        </div>
      )}
    </div>
  );
}
