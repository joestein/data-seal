import { useState, useCallback, useEffect, useMemo } from 'react';
import { PdfViewer } from '../pdf/PdfViewer';
import { PdfPageCanvas } from '../pdf/PdfPageCanvas';
import { FieldPalette } from '../fields/FieldPalette';
import { FieldConfigPanel } from '../fields/FieldConfigPanel';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { useDocuments } from '../../hooks/useDocuments';
import { useRecipients } from '../../hooks/useRecipients';
import { useFields, useCreateField, useUpdateField, useDeleteField } from '../../hooks/useFields';
import { getPageImageUrl } from '../../api/documents';
import { FIELD_DEFAULT_SIZES } from '../../lib/constants';
import type { FieldType } from '../../api/types';

interface StepFieldPlacementProps {
  envelopeId: string;
  onNext: () => void;
  onBack: () => void;
}

export function StepFieldPlacement({ envelopeId, onNext, onBack }: StepFieldPlacementProps) {
  const { data: documents } = useDocuments(envelopeId);
  const { data: recipients } = useRecipients(envelopeId);

  const [selectedDocIdx, setSelectedDocIdx] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedFieldId, setSelectedFieldId] = useState<string | null>(null);
  const [selectedRecipientId, setSelectedRecipientId] = useState<string | null>(null);
  const [draggingFieldType, setDraggingFieldType] = useState<FieldType | null>(null);

  const docs = documents ?? [];
  const recips = useMemo(() => recipients ?? [], [recipients]);
  const currentDoc = docs[selectedDocIdx];

  const { data: fields } = useFields(envelopeId, currentDoc?.id ?? '');
  const createField = useCreateField(envelopeId, currentDoc?.id ?? '');
  const updateField = useUpdateField(envelopeId, currentDoc?.id ?? '');
  const deleteField = useDeleteField(envelopeId, currentDoc?.id ?? '');

  // Default to first signer
  useEffect(() => {
    if (!selectedRecipientId && recips.length > 0) {
      const signer = recips.find((r) => r.role !== 'cc');
      if (signer) setSelectedRecipientId(signer.id);
    }
  }, [recips, selectedRecipientId]);

  const pageFields = (fields ?? []).filter((f) => f.page_number === currentPage);
  const selectedField = (fields ?? []).find((f) => f.id === selectedFieldId) ?? null;

  const handleDropNewField = useCallback(
    (type: FieldType, xPct: number, yPct: number) => {
      if (!selectedRecipientId || !currentDoc) return;
      const defaults = FIELD_DEFAULT_SIZES[type];
      createField.mutate({
        recipient_id: selectedRecipientId,
        type,
        page_number: currentPage,
        x_position: xPct,
        y_position: yPct,
        width: defaults.width,
        height: defaults.height,
        is_required: true,
      });
    },
    [selectedRecipientId, currentDoc, currentPage, createField],
  );

  const handleFieldDragEnd = useCallback(
    (fieldId: string, xPct: number, yPct: number) => {
      updateField.mutate({
        fieldId,
        data: { x_position: xPct, y_position: yPct },
      });
    },
    [updateField],
  );

  const handleFieldResizeEnd = useCallback(
    (fieldId: string, xPct: number, yPct: number, wPct: number, hPct: number) => {
      updateField.mutate({
        fieldId,
        data: {
          x_position: xPct,
          y_position: yPct,
          width: wPct,
          height: hPct,
        },
      });
    },
    [updateField],
  );

  const handleFieldUpdate = useCallback(
    (fieldId: string, updates: Record<string, unknown>) => {
      updateField.mutate({ fieldId, data: updates });
    },
    [updateField],
  );

  const handleFieldDelete = useCallback(
    (fieldId: string) => {
      deleteField.mutate(fieldId);
      setSelectedFieldId(null);
    },
    [deleteField],
  );

  // Keyboard shortcut for deleting selected field
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Delete' && selectedFieldId) {
        handleFieldDelete(selectedFieldId);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [selectedFieldId, handleFieldDelete]);

  if (!currentDoc) {
    return <LoadingSpinner className="py-16" />;
  }

  const imageUrl = getPageImageUrl(envelopeId, currentDoc.id, currentPage);

  return (
    <div className="space-y-4">
      {docs.length > 1 && (
        <div className="flex gap-2">
          {docs.map((doc, idx) => (
            <button
              key={doc.id}
              onClick={() => {
                setSelectedDocIdx(idx);
                setCurrentPage(1);
                setSelectedFieldId(null);
              }}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                idx === selectedDocIdx
                  ? 'bg-brand-100 text-brand-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {doc.filename}
            </button>
          ))}
        </div>
      )}

      <div className="flex gap-4">
        <FieldPalette
          recipients={recips}
          selectedRecipientId={selectedRecipientId}
          onRecipientChange={setSelectedRecipientId}
          onFieldDragStart={setDraggingFieldType}
        />

        <div className="flex-1">
          <PdfViewer
            currentPage={currentPage}
            totalPages={currentDoc.page_count}
            onPageChange={(p) => {
              setCurrentPage(p);
              setSelectedFieldId(null);
            }}
          >
            <PdfPageCanvas
              imageUrl={imageUrl}
              fields={pageFields}
              recipients={recips}
              selectedFieldId={selectedFieldId}
              onSelectField={setSelectedFieldId}
              onFieldDragEnd={handleFieldDragEnd}
              onFieldResizeEnd={handleFieldResizeEnd}
              onDropNewField={handleDropNewField}
              draggingFieldType={draggingFieldType}
            />
          </PdfViewer>
        </div>

        <FieldConfigPanel
          field={selectedField}
          recipients={recips}
          onUpdate={handleFieldUpdate}
          onDelete={handleFieldDelete}
        />
      </div>

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onNext}>Next: Review</Button>
      </div>
    </div>
  );
}
