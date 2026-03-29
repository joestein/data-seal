interface CheckboxFieldProps {
  checked: boolean;
  onToggle: (value: string) => void;
}

export function CheckboxField({ checked, onToggle }: CheckboxFieldProps) {
  return (
    <button
      onClick={() => onToggle(checked ? 'false' : 'true')}
      className="flex items-center justify-center"
      aria-label="Toggle checkbox"
    >
      <input
        type="checkbox"
        checked={checked}
        readOnly
        className="h-5 w-5 rounded border-gray-300 text-brand-600 pointer-events-none"
      />
    </button>
  );
}
