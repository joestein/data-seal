import { useState } from 'react';
import { Modal } from '../common/Modal';
import { Input } from '../common/Input';
import { Button } from '../common/Button';

interface TextFieldInputProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (value: string) => void;
  placeholder?: string | null;
}

export function TextFieldInput({ open, onClose, onSubmit, placeholder }: TextFieldInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = () => {
    if (value.trim()) {
      onSubmit(value.trim());
      setValue('');
      onClose();
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Enter Text" size="sm">
      <div className="space-y-4">
        <Input
          label="Value"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder ?? 'Enter value'}
          autoFocus
        />
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!value.trim()}>
            Apply
          </Button>
        </div>
      </div>
    </Modal>
  );
}
