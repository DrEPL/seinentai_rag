/**
 * SEINENTAI4US — Badge component
 */
import { cn } from '@/lib/utils';
import { getStatusStyles } from '@/lib/utils';
import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'status';
  status?: string;
  className?: string;
  dot?: boolean;
}

const variantStyles: Record<string, string> = {
  default: 'bg-slate-100 text-slate-700',
  success: 'bg-emerald-50 text-emerald-700',
  warning: 'bg-amber-50 text-amber-700',
  danger: 'bg-red-50 text-red-700',
  info: 'bg-blue-50 text-blue-700',
};

export default function Badge({
  children,
  variant = 'default',
  status,
  className,
  dot = false,
}: BadgeProps) {
  if (variant === 'status' && status) {
    const styles = getStatusStyles(status);
    return (
      <span className={cn('badge', styles.bg, styles.text, className)}>
        {dot && <span className={cn('w-1.5 h-1.5 rounded-full', styles.dot)} />}
        {children}
      </span>
    );
  }

  return (
    <span className={cn('badge', variantStyles[variant], className)}>
      {dot && (
        <span
          className={cn(
            'w-1.5 h-1.5 rounded-full',
            variant === 'success' && 'bg-emerald-500',
            variant === 'warning' && 'bg-amber-500',
            variant === 'danger' && 'bg-red-500',
            variant === 'info' && 'bg-blue-500',
            variant === 'default' && 'bg-slate-400'
          )}
        />
      )}
      {children}
    </span>
  );
}
