import { useState, useCallback, useRef, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { FileSignature, ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { SigningFieldOverlay } from '../../components/signing/SigningFieldOverlay';
import { SignatureModal } from '../../components/signing/SignatureModal';
import { TextFieldInput } from '../../components/signing/TextFieldInput';
import { DropdownField } from '../../components/signing/DropdownField';
import { DeclineModal } from '../../components/signing/DeclineModal';
import {
  useSigningSession,
  useSubmitFieldValue,
  useCompleteSigning,
  useDeclineSigning,
} from '../../hooks/useSigning';
import { useUiStore } from '../../stores/uiStore';
import type { SigningField } from '../../api/types';

export function SigningPage() {
  const { token } = useParams<{ token: string }>();
  const { data: session, isLoading, error, refetch } = useSigningSession(token!);
  const submitField = useSubmitFieldValue(token!);
  const completeSigning = useCompleteSigning(token!);
  const declineSigning = useDeclineSigning(token!);
  const { addToast } = useUiStore();

  const [currentDocIdx, setCurrentDocIdx] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [activeField, setActiveField] = useState<SigningField | null>(null);
  const [showSignature, setShowSignature] = useState(false);
  const [showText, setShowText] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showDecline, setShowDecline] = useState(false);
  const [completed, setCompleted] = useState(false);
  const pageImageRef = useRef<HTMLDivElement>(null);

  // All fields across all documents
  const allFields = useMemo(() => session?.documents.flatMap((d) => d.fields) ?? [], [session]);
  const filledCount = allFields.filter((f) => f.value !== null).length;
  const requiredCount = allFields.filter((f) => f.is_required).length;
  const filledRequiredCount = allFields.filter((f) => f.is_required && f.value !== null).length;
  const canFinish = filledRequiredCount === requiredCount;

  const currentDoc = session?.documents[currentDocIdx];
  const pageFields = currentDoc?.fields.filter((f) => f.page_number === currentPage) ?? [];

  const handleFieldClick = useCallback(
    (fieldId: string) => {
      const field = allFields.find((f) => f.id === fieldId);
      if (!field) return;
      setActiveField(field);

      switch (field.type) {
        case 'signature':
        case 'initials':
          setShowSignature(true);
          break;
        case 'text':
          setShowText(true);
          break;
        case 'date_signed':
          // Auto-fill with current date
          submitField.mutate(
            { fieldId: field.id, value: new Date().toISOString().split('T')[0] },
            { onSuccess: () => refetch() },
          );
          break;
        case 'checkbox':
          submitField.mutate(
            { fieldId: field.id, value: field.value === 'true' ? 'false' : 'true' },
            { onSuccess: () => refetch() },
          );
          break;
        case 'dropdown':
          setShowDropdown(true);
          break;
      }
    },
    [allFields, submitField, refetch],
  );

  const handleSignatureApply = (value: string) => {
    if (!activeField) return;
    submitField.mutate(
      { fieldId: activeField.id, value },
      { onSuccess: () => refetch() },
    );
  };

  const handleTextApply = (value: string) => {
    if (!activeField) return;
    submitField.mutate(
      { fieldId: activeField.id, value },
      { onSuccess: () => refetch() },
    );
  };

  const handleDropdownApply = (value: string) => {
    if (!activeField) return;
    submitField.mutate(
      { fieldId: activeField.id, value },
      { onSuccess: () => refetch() },
    );
  };

  const handleComplete = () => {
    completeSigning.mutate(undefined, {
      onSuccess: () => {
        setCompleted(true);
        addToast({ type: 'success', message: 'Signing complete!' });
      },
    });
  };

  const handleDecline = (reason?: string) => {
    declineSigning.mutate(reason, {
      onSuccess: () => {
        setCompleted(true);
        addToast({ type: 'info', message: 'You have declined to sign.' });
      },
    });
  };

  // Construct authenticated image URL
  const pageImageUrl = currentDoc
    ? `/api/v1/signing/${token}/documents/${currentDoc.id}/pages/${currentPage}`
    : '';

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="flex h-screen flex-col items-center justify-center">
        <FileSignature className="mb-4 h-12 w-12 text-gray-400" />
        <h1 className="text-xl font-semibold text-gray-900">Invalid Signing Link</h1>
        <p className="mt-2 text-sm text-gray-500">
          This link may have expired or already been used.
        </p>
      </div>
    );
  }

  if (completed) {
    return (
      <div className="flex h-screen flex-col items-center justify-center">
        <div className="mb-4 rounded-full bg-green-100 p-4">
          <Check className="h-8 w-8 text-green-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Thank you!</h1>
        <p className="mt-2 text-sm text-gray-500">
          Your response has been recorded. You can close this window.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-gray-100">
      {/* Top bar */}
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
        <div className="flex items-center gap-2">
          <FileSignature className="h-6 w-6 text-brand-600" />
          <span className="font-semibold text-gray-900">{session.envelope.title}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">Powered by DataSeal</span>
          <Button variant="secondary" size="sm" onClick={() => setShowDecline(true)}>
            Decline
          </Button>
        </div>
      </header>

      {/* Document viewer */}
      <div className="flex-1 overflow-auto p-4">
        {session.documents.length > 1 && (
          <div className="mb-3 flex gap-2">
            {session.documents.map((doc, idx) => (
              <button
                key={doc.id}
                onClick={() => {
                  setCurrentDocIdx(idx);
                  setCurrentPage(1);
                }}
                className={`rounded px-3 py-1 text-sm ${
                  idx === currentDocIdx
                    ? 'bg-brand-100 text-brand-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-200'
                }`}
              >
                {doc.filename}
              </button>
            ))}
          </div>
        )}

        {currentDoc && (
          <>
            <div className="mb-2 flex items-center justify-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-gray-600">
                Page {currentPage} of {currentDoc.page_count}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={currentPage >= currentDoc.page_count}
                onClick={() => setCurrentPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            <div
              ref={pageImageRef}
              className="relative mx-auto max-w-4xl rounded-lg bg-white shadow-lg"
            >
              <img
                src={pageImageUrl}
                alt={`Page ${currentPage}`}
                className="w-full"
              />
              {pageFields.map((field) => (
                <SigningFieldOverlay
                  key={field.id}
                  field={field}
                  onClick={handleFieldClick}
                />
              ))}
            </div>
          </>
        )}
      </div>

      {/* Bottom bar */}
      <footer className="flex items-center justify-between border-t border-gray-200 bg-white px-6 py-3">
        <span className="text-sm text-gray-600">
          {filledCount} of {allFields.length} fields completed
          {requiredCount > 0 && ` (${filledRequiredCount}/${requiredCount} required)`}
        </span>
        <Button
          onClick={handleComplete}
          disabled={!canFinish}
          loading={completeSigning.isPending}
        >
          <Check className="mr-1 h-4 w-4" />
          Finish
        </Button>
      </footer>

      {/* Modals */}
      <SignatureModal
        open={showSignature}
        onClose={() => setShowSignature(false)}
        onApply={handleSignatureApply}
        isInitials={activeField?.type === 'initials'}
      />
      <TextFieldInput
        open={showText}
        onClose={() => setShowText(false)}
        onSubmit={handleTextApply}
        placeholder={activeField?.placeholder}
      />
      <DropdownField
        open={showDropdown}
        onClose={() => setShowDropdown(false)}
        onSubmit={handleDropdownApply}
        options={activeField?.dropdown_options ?? []}
      />
      <DeclineModal
        open={showDecline}
        onClose={() => setShowDecline(false)}
        onDecline={handleDecline}
        loading={declineSigning.isPending}
      />
    </div>
  );
}
