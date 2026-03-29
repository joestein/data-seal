import { useState, useEffect, useCallback } from 'react';
import { FileText, Trash2, Loader2 } from 'lucide-react';
import { FileUpload } from '../common/FileUpload';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { useUploadDocument, useDeleteDocument, useDocuments } from '../../hooks/useDocuments';
import { formatFileSize } from '../../lib/utils';
import type { Document } from '../../api/types';

interface StepDocumentsProps {
  envelopeId: string;
  title: string;
  message: string;
  onTitleChange: (title: string) => void;
  onMessageChange: (message: string) => void;
  onNext: () => void;
}

export function StepDocuments({
  envelopeId,
  title,
  message,
  onTitleChange,
  onMessageChange,
  onNext,
}: StepDocumentsProps) {
  const { data: documents, refetch } = useDocuments(envelopeId);
  const upload = useUploadDocument(envelopeId);
  const remove = useDeleteDocument(envelopeId);
  const [polling, setPolling] = useState<Set<string>>(new Set());

  const handleUpload = useCallback(
    (files: File[]) => {
      files.forEach((file) => {
        upload.mutate(file, {
          onSuccess: (doc: Document) => {
            if (doc.page_count === 0) {
              setPolling((prev) => new Set(prev).add(doc.id));
            }
          },
        });
      });
    },
    [upload],
  );

  // Poll documents being processed
  useEffect(() => {
    if (polling.size === 0) return;
    const interval = setInterval(() => {
      refetch().then(({ data }) => {
        if (!data) return;
        const stillProcessing = new Set<string>();
        for (const doc of data) {
          if (polling.has(doc.id) && doc.page_count === 0) {
            stillProcessing.add(doc.id);
          }
        }
        setPolling(stillProcessing);
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [polling, refetch]);

  const docs = documents ?? [];
  const canProceed = docs.length > 0 && title.trim().length > 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Envelope Title"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="Enter a title for this envelope"
          required
        />
        <Input
          label="Message (optional)"
          value={message}
          onChange={(e) => onMessageChange(e.target.value)}
          placeholder="Message to recipients"
        />
      </div>

      <FileUpload onFilesSelected={handleUpload} multiple disabled={upload.isPending} />

      {docs.length > 0 && (
        <div className="rounded-lg border border-gray-200">
          <ul className="divide-y divide-gray-200">
            {docs.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{doc.filename}</p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(doc.size_bytes)}
                      {doc.page_count > 0
                        ? ` - ${doc.page_count} page${doc.page_count > 1 ? 's' : ''}`
                        : ''}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {polling.has(doc.id) && (
                    <span className="flex items-center gap-1 text-xs text-amber-600">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Processing...
                    </span>
                  )}
                  <button
                    onClick={() => remove.mutate(doc.id)}
                    className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600"
                    aria-label={`Remove ${doc.filename}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex justify-end">
        <Button onClick={onNext} disabled={!canProceed}>
          Next: Recipients
        </Button>
      </div>
    </div>
  );
}
