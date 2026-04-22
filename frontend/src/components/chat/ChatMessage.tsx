/**
 * SEINENTAI4US — ChatMessage bubble
 */
import { memo, useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, User, FileText, ChevronDown, ChevronUp, Copy, Check, Share2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { useAppDispatch } from '@/store/hooks';
import { addToast } from '@/store/slices/uiSlice';
import { copyToClipboard } from '@/utils/exportUtils';
import Popover from '@/components/ui/Popover';
import SocialShareButtons from './SocialShareButtons';
import type { ChatMessage as ChatMessageType } from '@/store/slices/chatSlice';

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const dispatch = useAppDispatch();
  const isUser = message.role === 'user';
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const [isShareOpen, setIsShareOpen] = useState(false);

  const handleCopy = async () => {
    const success = await copyToClipboard(message.content);
    if (success) {
      setCopied(true);
      dispatch(addToast({ type: 'success', message: 'Message copié !' }));
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'flex gap-3 px-4 md:px-0 group',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center shadow-sm transition-all duration-500',
          isUser
            ? 'bg-gradient-to-br from-slate-400 to-slate-500'
            : 'bg-gradient-to-br from-slate-700 via-slate-800 to-slate-950',
          // Hide AI icon while "thinking" (streaming but no content yet)
          !isUser && isStreaming && !message.content && 'hidden'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Bubble Container */}
      <div
        className={cn(
          'max-w-[85%] md:max-w-[80%] flex flex-col relative',
          isUser ? 'items-end' : 'items-start',
          !isUser && isStreaming && !message.content && 'hidden'
        )}
      >
        {/* Actions - Visible on hover */}
        {!isStreaming && (
          <div className={cn(
            "absolute -top-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 flex gap-1",
            isUser ? "right-full mr-2 flex-row-reverse" : "left-full ml-2"
          )}>
            <button
              onClick={handleCopy}
              className="p-2 rounded-lg bg-white border border-slate-200 shadow-sm text-slate-400 hover:text-emerald-600 hover:border-emerald-100 transition-all cursor-pointer"
              title="Copier le message"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </button>

            <Popover
              isOpen={isShareOpen}
              onClose={() => setIsShareOpen(false)}
              align={isUser ? "right" : "left"}
              position="bottom"
              contentClassName="min-w-[200px]"
              trigger={
                <button
                  onClick={() => setIsShareOpen(!isShareOpen)}
                  className={cn(
                    "p-2 rounded-lg bg-white border border-slate-200 shadow-sm text-slate-400 hover:text-blue-500 hover:border-blue-100 transition-all cursor-pointer",
                    isShareOpen && "border-blue-100 bg-blue-50/30"
                  )}
                  title="Partager le message"
                >
                  <Share2 className="w-3.5 h-3.5" />
                </button>
              }
            >
              <div className="p-1">
                <p className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-50 mb-1">
                  Partager le message
                </p>
                <SocialShareButtons 
                  url={typeof window !== 'undefined' ? window.location.href : ''} 
                  title={message.content.substring(0, 100)} 
                />
              </div>
            </Popover>
          </div>
        )}

        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm',
            isUser
              ? 'bg-slate-100 text-slate-900 border border-slate-200 rounded-tr-md'
              : 'bg-white border border-slate-100 text-slate-700 rounded-tl-md'
          )}
        >
          {/* Render content with Markdown */}
          <div className={cn(
            'break-words',
            isUser ? 'prose-chat-user' : 'prose-chat'
          )}>
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ node, ...props }) => <a target="_blank" rel="noopener noreferrer" {...props} />,
                code: ({ node, className, children, ...props }: any) => {
                  const match = /language-(\w+)/.exec(className || '');
                  const isInline = !match;
                  
                  // Extract node and other non-HTML props to avoid spreading them to <code>
                  const { node: _, ...rest } = props;

                  if (isInline) {
                    return (
                      <code 
                        className={cn(
                          "px-1.5 py-0.5 rounded font-medium",
                          isUser 
                            ? "bg-slate-200/70 text-slate-800" 
                            : "bg-slate-100 text-emerald-600"
                        )} 
                        {...rest}
                      >
                        {children}
                      </code>
                    );
                  }

                  return (
                    <code 
                      className={cn(
                        "block p-3 rounded-lg border overflow-x-auto my-2",
                        className,
                        isUser
                          ? "bg-slate-200/40 border-slate-300/50 text-slate-900"
                          : "bg-slate-50 border-slate-100 text-slate-800"
                      )}
                      {...rest}
                    >
                      {children}
                    </code>
                  );
                }
              }}
            >
              {message.content || (isStreaming ? '...' : '')}
            </ReactMarkdown>
            
            {isStreaming && message.content && (
              <span className="inline-block w-2 h-4 ml-1 bg-emerald-500 animate-[typing-cursor_1s_infinite] vertical-middle" />
            )}
          </div>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2">
            <button
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
              className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-600 hover:text-emerald-700 transition-colors cursor-pointer"
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
                      <span className="text-[10px] text-emerald-600 font-mono">
                        {(source.score * 10).toFixed(2)}%
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
