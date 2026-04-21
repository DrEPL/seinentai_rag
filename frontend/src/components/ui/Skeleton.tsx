/**
 * SEINENTAI4US — Skeleton loader
 */
import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export default function Skeleton({
  className,
  variant = 'text',
  width,
  height,
}: SkeletonProps) {
  return (
    <div
      className={cn(
        'skeleton',
        variant === 'circular' && 'rounded-full',
        variant === 'text' && 'rounded-md h-4',
        variant === 'rectangular' && 'rounded-xl',
        className
      )}
      style={{ width, height }}
    />
  );
}

/** Chat message skeleton */
export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={cn('flex gap-3 px-4', isUser ? 'flex-row-reverse' : 'flex-row')}>
      <Skeleton variant="circular" width={36} height={36} />
      <div className={cn('flex flex-col gap-2', isUser ? 'items-end' : 'items-start')}>
        <Skeleton width={200} height={16} />
        <Skeleton width={300} height={16} />
        <Skeleton width={150} height={16} />
      </div>
    </div>
  );
}

/** Document card skeleton */
export function DocumentCardSkeleton() {
  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton variant="rectangular" width={40} height={40} />
        <div className="flex-1 space-y-2">
          <Skeleton width="60%" height={16} />
          <Skeleton width="40%" height={12} />
        </div>
      </div>
    </div>
  );
}

/** Sidebar session skeleton */
export function SessionSkeleton() {
  return (
    <div className="px-3 py-2 space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-3 py-2.5">
          <Skeleton variant="circular" width={20} height={20} />
          <Skeleton width="70%" height={14} />
        </div>
      ))}
    </div>
  );
}
