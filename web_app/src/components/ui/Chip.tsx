import { forwardRef } from 'react';
import type { HTMLAttributes } from 'react';

interface ChipProps extends HTMLAttributes<HTMLSpanElement> {
  label: string;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  onRemove?: () => void;
}

const variantStyles = {
  default: 'bg-gray-100 text-gray-700 border-gray-200',
  success: 'bg-green-100 text-green-700 border-green-200',
  warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  error: 'bg-red-100 text-red-700 border-red-200',
  info: 'bg-blue-100 text-blue-700 border-blue-200',
};

export const Chip = forwardRef<HTMLSpanElement, ChipProps>(
  ({ label, variant = 'default', onRemove, className = '', ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={`
          inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border
          ${variantStyles[variant]}
          ${className}
        `}
        {...props}
      >
        {label}
        {onRemove && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="ml-1 hover:bg-black/10 rounded-full p-0.5"
          >
            &times;
          </button>
        )}
      </span>
    );
  }
);

Chip.displayName = 'Chip';