import { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';

interface DropdownFieldProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (value: string) => void;
  options: string[];
}

export function DropdownField({ open, onClose, onSubmit, options }: DropdownFieldProps) {
  const [selected, setSelected] = useState('');

  const handleSubmit = () => {
    if (selected) {
      onSubmit(selected);
      onClose();
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Select an Option" size="sm">
      <div className="space-y-4">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="input-field"
          autoFocus
        >
          <option value="">Choose...</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!selected}>
            Apply
          </Button>
        </div>
      </div>
    </Modal>
  );
}
