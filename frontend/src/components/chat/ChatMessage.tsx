/**
 * SEINENTAI4US — ChatMessage bubble
 */
import { memo } from 'react';
import { motion } from 'framer-motion';
import { Bot, User, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ChatMessage as ChatMessageType } from '@/store/slices/chatSlice';
import { useState } from 'react';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const [sourcesExpanded, setSourcesExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'flex gap-3 px-4 md:px-0',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center shadow-sm',
          isUser
            ? 'bg-gradient-to-br from-indigo-400 to-violet-500'
            : 'bg-gradient-to-br from-emerald-400 to-teal-500'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={cn(
          'max-w-[80%] md:max-w-[70%]',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white rounded-tr-md'
              : 'bg-white border border-slate-100 text-slate-700 shadow-sm rounded-tl-md'
          )}
        >
          {/* Render content with line breaks */}
          <div className="whitespace-pre-wrap break-words">
            {message.content}
            {isStreaming && !message.content && (
              <span className="typing-dots inline-flex ml-1">
                <span /><span /><span />
              </span>
            )}
          </div>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2">
            <button
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
              className="inline-flex items-center gap-1.5 text-[11px] font-medium text-indigo-600 hover:text-indigo-700 transition-colors cursor-pointer"
            >
              <FileText className="w-3 h-3" />
              {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
              {sourcesExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {sourcesExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-2 space-y-1.5"
              >
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="px-3 py-2 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-slate-700 truncate">
                        {source.filename}
                      </span>
                      <span className="text-[10px] text-indigo-500 font-mono">
                        {(source.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-slate-500 line-clamp-2">{source.excerpt}</p>
                  </div>
                ))}
              </motion.div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <p className={cn('text-[10px] text-slate-400 mt-1', isUser && 'text-right')}>
          {new Date(message.timestamp).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </motion.div>
  );
}

export default memo(ChatMessage);
