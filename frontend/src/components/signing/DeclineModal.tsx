import { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface DeclineModalProps {
  open: boolean;
  onClose: () => void;
  onDecline: (reason?: string) => void;
  loading?: boolean;
}

export function DeclineModal({ open, onClose, onDecline, loading }: DeclineModalProps) {
  const [reason, setReason] = useState('');

  return (
    <Modal open={open} onClose={onClose} title="Decline to Sign" size="md">
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Are you sure you want to decline signing this document? This action cannot be undone.
        </p>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Reason (optional)
          </label>
          <textarea
            className="input-field"
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Enter a reason for declining..."
          />
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={() => onDecline(reason || undefined)}
            loading={loading}
          >
            Decline
          </Button>
        </div>
      </div>
    </Modal>
  );
}
