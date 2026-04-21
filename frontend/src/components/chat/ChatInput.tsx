/**
 * SEINENTAI4US — ChatInput component
 */
import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Square, Sparkles, Settings2, SendHorizonalIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { toggleRagSettings } from '@/store/slices/uiSlice';

interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
  onStop: () => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, isStreaming, onStop, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dispatch = useAppDispatch();
  const ragSettings = useAppSelector((s) => s.chat.ragSettings);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    }
  }, [message]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isStreaming && !disabled) {
      onSend(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-slate-200/60 bg-white/80 backdrop-blur-xl px-4 py-4 sm:py-5">
      {/* RAG settings indicator */}
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-2 mb-2">
          <button
            onClick={() => dispatch(toggleRagSettings())}
            className={cn(
              'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium',
              'transition-all duration-200 cursor-pointer',
              ragSettings.use_agent
                ? 'bg-violet-50 text-violet-600 hover:bg-violet-100'
                : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
            )}
          >
            <Settings2 className="w-3 h-3" />
            Réglages
          </button>
          <AnimatePresence>
            {ragSettings.use_agent && (
              <motion.span
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-violet-50 text-violet-600 text-[10px] font-semibold"
              >
                <Sparkles className="w-3 h-3" />
                Agent IA actif
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Input area */}
        <form onSubmit={handleSubmit} className="relative">
          <div
            className={cn(
              'flex items-end gap-2 bg-white rounded-2xl border border-slate-200',
              'shadow-sm transition-all duration-200',
              'focus-within:border-none focus-within:shadow-md focus-within:shadow-indigo-100/50'
            )}
          >
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Posez votre question..."
              rows={1}
              disabled={disabled}
              className={cn(
                'flex-1 resize-none px-4 py-3 text-sm text-slate-900',
                'bg-transparent border-none outline-none',
                'placeholder:text-slate-400',
                'disabled:opacity-50',
                'max-h-[160px]'
              )}
            />
            <div className="flex items-center gap-1 p-2">
              {isStreaming ? (
                <button
                  type="button"
                  onClick={onStop}
                  className={cn(
                    'p-2 rounded-xl bg-red-500 text-white',
                    'hover:bg-red-600 transition-colors cursor-pointer',
                    'shadow-sm hover:shadow-md'
                  )}
                >
                  <Square className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!message.trim() || disabled}
                  className={cn(
                    'p-2 rounded-xl transition-all duration-200 cursor-pointer',
                    message.trim()
                      ? 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-sm hover:shadow-md hover:shadow-indigo-200'
                      : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  )}
                >
                  <SendHorizonalIcon className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </form>

        <p className="text-[10px] text-slate-400 text-center mt-2">
          Shift+Entrée pour un retour à la ligne • Entrée pour envoyer
        </p>
      </div>
    </div>
  );
}
