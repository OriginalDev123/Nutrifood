import type { ReactNode } from 'react';

interface PageContainerProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}

export function PageContainer({
  children,
  title,
  subtitle,
  action,
  className = '',
}: PageContainerProps) {
  return (
    <div className={`max-w-7xl mx-auto space-y-6 ${className}`}>
      {(title || action) && (
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="space-y-1">
            {title && (
              <h1 className="text-3xl font-bold tracking-tight text-gray-900">{title}</h1>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500 md:text-base">{subtitle}</p>
            )}
          </div>
          {action && <div className="flex flex-wrap items-center gap-2">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}