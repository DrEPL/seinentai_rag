/**
 * SEINENTAI4US — Popover component
 */
import { useRef, useEffect, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface PopoverProps {
  isOpen: boolean;
  onClose: () => void;
  trigger: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
  align?: 'left' | 'right' | 'center';
  position?: 'top' | 'bottom';
}

export default function Popover({
  isOpen,
  onClose,
  trigger,
  children,
  className,
  contentClassName,
  align = 'left',
  position = 'top',
}: PopoverProps) {
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  const alignmentClasses = {
    left: 'left-0 origin-bottom-left',
    right: 'right-0 origin-bottom-right',
    center: 'left-1/2 -translate-x-1/2 origin-bottom',
  };

  const positionClasses = {
    top: 'bottom-full mb-2',
    bottom: 'top-full mt-2',
  };

  return (
    <div className={cn('relative inline-block', className)} ref={popoverRef}>
      {trigger}
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: position === 'top' ? 10 : -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: position === 'top' ? 10 : -10, scale: 0.95 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className={cn(
              'absolute z-50 min-w-[280px]',
              alignmentClasses[align],
              positionClasses[position],
              contentClassName
            )}
          >
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
