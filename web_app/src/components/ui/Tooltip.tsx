import type { ReactNode } from 'react';

interface TooltipProps {
  children: ReactNode;
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ children, content, position = 'top' }: TooltipProps) {
  const positionStyles = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-1',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-1',
    left: 'right-full top-1/2 -translate-y-1/2 mr-1',
    right: 'left-full top-1/2 -translate-y-1/2 ml-1',
  };

  return (
    <div className="relative group inline-block">
      {children}
      <div
        className={`
          absolute ${positionStyles[position]} hidden group-hover:block
          px-2 py-1 text-xs text-white bg-gray-800 rounded whitespace-nowrap z-10
        `}
      >
        {content}
      </div>
    </div>
  );
}