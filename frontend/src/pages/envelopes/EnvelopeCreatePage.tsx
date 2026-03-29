import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { WizardStepper } from '../../components/wizard/WizardStepper';
import { StepDocuments } from '../../components/wizard/StepDocuments';
import { StepRecipients } from '../../components/wizard/StepRecipients';
import { StepFieldPlacement } from '../../components/wizard/StepFieldPlacement';
import { StepReview } from '../../components/wizard/StepReview';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { useCreateEnvelope, useEnvelope, useUpdateEnvelope } from '../../hooks/useEnvelopes';
import { ROUTES } from '../../lib/routes';

export function EnvelopeCreatePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [envelopeId, setEnvelopeId] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');

  const createEnvelope = useCreateEnvelope();
  const updateEnvelope = useUpdateEnvelope();
  const { data: envelope } = useEnvelope(envelopeId ?? '');

  // Create envelope on mount if we don't have one yet
  useEffect(() => {
    if (!envelopeId && !createEnvelope.isPending && !createEnvelope.isSuccess) {
      createEnvelope.mutate(
        { title: 'Untitled Envelope' },
        { onSuccess: (env) => setEnvelopeId(env.id) },
      );
    }
  }, [envelopeId, createEnvelope]);

  const handleNextFromDocs = () => {
    if (!envelopeId) return;
    // Save title/message
    updateEnvelope.mutate(
      { id: envelopeId, data: { title: title.trim() || 'Untitled', message: message || null } },
      { onSuccess: () => setStep(1) },
    );
  };

  if (!envelopeId || !envelope) {
    return <LoadingSpinner className="py-16" />;
  }

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-gray-900">Create Envelope</h1>
      <WizardStepper currentStep={step} />

      {step === 0 && (
        <StepDocuments
          envelopeId={envelopeId}
          title={title}
          message={message}
          onTitleChange={setTitle}
          onMessageChange={setMessage}
          onNext={handleNextFromDocs}
        />
      )}
      {step === 1 && (
        <StepRecipients
          envelopeId={envelopeId}
          onNext={() => setStep(2)}
          onBack={() => setStep(0)}
        />
      )}
      {step === 2 && (
        <StepFieldPlacement
          envelopeId={envelopeId}
          onNext={() => setStep(3)}
          onBack={() => setStep(1)}
        />
      )}
      {step === 3 && (
        <StepReview
          envelope={envelope}
          onBack={() => setStep(2)}
          onSent={() => navigate(ROUTES.ENVELOPE_DETAIL(envelopeId))}
        />
      )}
    </div>
  );
}
