/**
 * SEINENTAI4US — Toggle switch
 */
import { cn } from '@/lib/utils';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  size?: 'sm' | 'md';
  className?: string;
  labelClassName?: string;
}

export default function Toggle({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  size = 'md',
  className,
  labelClassName,
}: ToggleProps) {
  const trackSize = size === 'sm' ? 'w-8 h-[18px]' : 'w-10 h-[22px]';
  const thumbSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4.5 h-4.5';
  const thumbTranslate = size === 'sm' ? 'translate-x-3.5' : 'translate-x-[18px]';

  return (
    <label
      className={cn(
        'flex items-center gap-3 cursor-pointer select-none group',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      <button
        role="switch"
        type="button"
        aria-checked={checked}
        onClick={() => !disabled && onChange(!checked)}
        className={cn(
          'relative inline-flex flex-shrink-0 rounded-full transition-colors duration-200',
          trackSize,
          checked ? 'bg-emerald-500' : 'bg-slate-200',
          !disabled && 'group-hover:shadow-md',
          'cursor-pointer'
        )}
      >
        <span
          className={cn(
            'absolute top-[2px] left-[2px] bg-white rounded-full shadow-sm transition-transform duration-200',
            thumbSize,
            checked && thumbTranslate
          )}
        />
      </button>
      {(label || description) && (
        <div className="flex flex-col">
          {label && (
            <span className={cn("text-sm font-medium text-slate-700", labelClassName)}>
              {label}
            </span>
          )}
          {description && <span className="text-xs text-slate-500">{description}</span>}
        </div>
      )}
    </label>
  );
}
