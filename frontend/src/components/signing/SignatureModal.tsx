import { useState, useRef } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { SignatureCanvas } from './SignatureCanvas';

type Tab = 'type' | 'draw' | 'upload';

interface SignatureModalProps {
  open: boolean;
  onClose: () => void;
  onApply: (value: string) => void;
  isInitials?: boolean;
}

const TABS: { key: Tab; label: string }[] = [
  { key: 'type', label: 'Type' },
  { key: 'draw', label: 'Draw' },
  { key: 'upload', label: 'Upload' },
];

export function SignatureModal({ open, onClose, onApply, isInitials }: SignatureModalProps) {
  const [tab, setTab] = useState<Tab>('type');
  const [typedText, setTypedText] = useState('');
  const [drawnData, setDrawnData] = useState<string | null>(null);
  const [uploadedData, setUploadedData] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleApply = () => {
    if (tab === 'type' && typedText.trim()) {
      onApply(`typed:${typedText.trim()}`);
    } else if (tab === 'draw' && drawnData) {
      onApply(drawnData);
    } else if (tab === 'upload' && uploadedData) {
      onApply(uploadedData);
    }
    onClose();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setUploadedData(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const canApply =
    (tab === 'type' && typedText.trim().length > 0) ||
    (tab === 'draw' && drawnData !== null) ||
    (tab === 'upload' && uploadedData !== null);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isInitials ? 'Add Your Initials' : 'Add Your Signature'}
      size="lg"
    >
      <div className="space-y-4">
        <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
          {TABS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === 'type' && (
          <div className="space-y-3">
            <Input
              label={isInitials ? 'Your initials' : 'Your full name'}
              value={typedText}
              onChange={(e) => setTypedText(e.target.value)}
              placeholder={isInitials ? 'J.D.' : 'John Doe'}
              autoFocus
            />
            {typedText && (
              <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-gray-50 p-6">
                <span
                  className="text-2xl italic text-gray-900"
                  style={{ fontFamily: 'cursive' }}
                >
                  {typedText}
                </span>
              </div>
            )}
          </div>
        )}

        {tab === 'draw' && (
          <SignatureCanvas
            onSave={setDrawnData}
            width={isInitials ? 200 : 500}
            height={isInitials ? 100 : 200}
          />
        )}

        {tab === 'upload' && (
          <div className="space-y-3">
            <Button
              variant="secondary"
              onClick={() => fileRef.current?.click()}
              className="w-full"
            >
              Choose Image
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg"
              className="hidden"
              onChange={handleFileUpload}
            />
            {uploadedData && (
              <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-gray-50 p-4">
                <img
                  src={uploadedData}
                  alt="Uploaded signature"
                  className="max-h-24 max-w-full"
                />
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end gap-3 border-t border-gray-200 pt-4">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleApply} disabled={!canApply}>
            Apply
          </Button>
        </div>
      </div>
    </Modal>
  );
}
