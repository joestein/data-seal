import { clsx } from 'clsx';

interface BadgeProps {
  children: React.ReactNode;
  color?: string;
  bgColor?: string;
  className?: string;
}

export function Badge({ children, color, bgColor, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        bgColor || 'bg-gray-100',
        color || 'text-gray-700',
        className,
      )}
    >
      {children}
    </span>
  );
}
