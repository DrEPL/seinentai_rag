/**
 * SEINENTAI4US — ChatInput component
 */
import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Square, Sparkles, Settings2, SendHorizonalIcon, BrainCircuitIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import Popover from '@/components/ui/Popover';
import RagSettings from '@/components/chat/RagSettings';

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
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

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
    <div className="w-full max-w-4xl mx-auto px-4 pb-6 pt-2">
      <div className={cn(
        "relative rounded-[32px] border border-white/40 bg-white/70 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.1)] p-2 transition-all duration-300",
        isStreaming ? "border-emerald-400/50" : "focus-within:border-emerald-400/50 focus-within:shadow-[0_20px_60px_rgba(16,185,129,0.15)]"
      )}>
        {/* RAG settings floating above or inside */}
        <div className="flex items-center gap-2 px-3 py-1.5 border-b border-slate-100/50 mb-1">
          <Popover
            isOpen={isSettingsOpen}
            onClose={() => setIsSettingsOpen(false)}
            trigger={
              <button
                onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                className={cn(
                  'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all duration-200 cursor-pointer',
                  ragSettings.use_agent || isSettingsOpen
                    ? 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'
                    : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
                )}
              >
                <Settings2 className="w-3.5 h-3.5" />
                Options
              </button>
            }
          >
            <RagSettings onClose={() => setIsSettingsOpen(false)} />
          </Popover>

          <AnimatePresence>
            {ragSettings.use_agent && (
              <motion.span
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-600 text-[10px] font-bold uppercase tracking-wider"
              >
                <BrainCircuitIcon className="w-3 h-3" />
                Réflexion approfondie
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Input area */}
        <form onSubmit={handleSubmit} className="flex items-end gap-2 px-1">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Posez votre question à Seinentai..."
            rows={1}
            disabled={disabled}
            className={cn(
              'flex-1 resize-none px-3 py-2.5 text-sm text-slate-900',
              'bg-transparent !border-none !outline-none',
              'placeholder:text-slate-400 font-medium',
              'disabled:opacity-50',
              'max-h-[200px] no-scrollbar'
            )}
          />
          
          <div className="flex-shrink-0 p-1">
            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                className="flex items-center justify-center w-10 h-10 rounded-2xl bg-slate-900 text-white hover:bg-slate-800 transition-all cursor-pointer shadow-lg shadow-slate-200"
              >
                <Square className="w-4 h-4 fill-white" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!message.trim() || disabled}
                className={cn(
                  'flex items-center justify-center w-10 h-10 rounded-2xl transition-all duration-300 cursor-pointer shadow-lg',
                  message.trim()
                    ? 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-emerald-200 hover:shadow-emerald-300 hover:scale-105 active:scale-95'
                    : 'bg-slate-100 text-slate-300 shadow-none cursor-not-allowed'
                )}
              >
                <SendHorizonalIcon className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>
      </div>
      
      <div className="flex items-center justify-center gap-4 mt-3">
        <p className="text-[11px] text-slate-400 font-medium tracking-tight">
          <span className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-500 mr-1">Shift+Entrée</span> pour un saut de ligne
        </p>
        <p className="text-[11px] text-slate-400 font-medium tracking-tight">
          <span className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-500 mr-1">Entrée</span> pour envoyer
        </p>
      </div>
    </div>
  );
}
