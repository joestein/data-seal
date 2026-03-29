import { useCallback, useRef, useState } from 'react';
import { Upload } from 'lucide-react';
import { clsx } from 'clsx';
import { MAX_FILE_SIZE_BYTES, ACCEPTED_FILE_TYPES } from '../../lib/constants';
import { useUiStore } from '../../stores/uiStore';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  multiple?: boolean;
  accept?: string;
  disabled?: boolean;
}

export function FileUpload({
  onFilesSelected,
  multiple = false,
  accept = '.pdf',
  disabled,
}: FileUploadProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { addToast } = useUiStore();

  const validateAndEmit = useCallback(
    (files: FileList | File[]) => {
      const valid: File[] = [];
      for (const file of Array.from(files)) {
        if (!ACCEPTED_FILE_TYPES.includes(file.type)) {
          addToast({ type: 'error', message: `${file.name}: Only PDF files are accepted` });
          continue;
        }
        if (file.size > MAX_FILE_SIZE_BYTES) {
          addToast({ type: 'error', message: `${file.name}: File exceeds 25 MB limit` });
          continue;
        }
        valid.push(file);
      }
      if (valid.length > 0) {
        onFilesSelected(valid);
      }
    },
    [onFilesSelected, addToast],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (disabled) return;
      validateAndEmit(e.dataTransfer.files);
    },
    [disabled, validateAndEmit],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={clsx(
        'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors',
        dragOver ? 'border-brand-400 bg-brand-50' : 'border-gray-300 hover:border-gray-400',
        disabled && 'cursor-not-allowed opacity-50',
      )}
      role="button"
      tabIndex={0}
      aria-label="Upload PDF files"
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
    >
      <Upload className="mb-3 h-8 w-8 text-gray-400" />
      <p className="text-sm font-medium text-gray-700">
        Drop PDF files here or click to browse
      </p>
      <p className="mt-1 text-xs text-gray-500">PDF files up to 25 MB</p>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={(e) => {
          if (e.target.files) {
            validateAndEmit(e.target.files);
            e.target.value = '';
          }
        }}
      />
    </div>
  );
}
