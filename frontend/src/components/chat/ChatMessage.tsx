/**
 * SEINENTAI4US — ChatMessage bubble
 */
import { memo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, FileText, ChevronDown, ChevronUp, Copy, Check, Share2, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn, formatTime } from '@/lib/utils';
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
          'max-w-[80%] md:max-w-[75%] flex flex-col relative',
          isUser ? 'items-end' : 'items-start',
          !isUser && isStreaming && !message.content && 'hidden'
        )}
      >


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

        {/* Actions, Sources & Time Row */}
        <div className={cn(
          "flex items-start justify-between gap-4 mt-1 w-full",
          isUser ? "flex-row-reverse" : "flex-row"
        )}>
          <div className={cn("flex-1 min-w-0 flex flex-col", isUser ? "items-end" : "items-start")}>
            {!isUser && message.sources && message.sources.length > 0 && (
              <div className="flex flex-col items-start w-full min-w-0">
                <button
                  onClick={() => setSourcesExpanded(!sourcesExpanded)}
                  className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-600 hover:text-emerald-700 transition-colors cursor-pointer flex-shrink-0"
                >
                  <FileText className="w-3 h-3" />
                  {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                  {sourcesExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>

                <AnimatePresence>
                  {sourcesExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-2 space-y-1.5 overflow-hidden w-full min-w-0"
                    >
                      {message.sources.map((source, idx) => (
                        <div
                          key={idx}
                          className="px-3 py-2 rounded-lg bg-slate-50 border border-slate-100 text-xs w-full max-w-full overflow-hidden"
                        >
                          <div className="flex items-center justify-between mb-1 min-w-0 gap-2">
                            <span className="font-medium text-slate-700 truncate min-w-0">
                              {source.filename}
                            </span>
                            <span className="text-[10px] text-emerald-600 font-mono flex-shrink-0">
                              {(source.score * 10).toFixed(2)}%
                            </span>
                          </div>
                          <p className="text-slate-500 line-clamp-2">{source.excerpt}</p>
                        </div>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Time for User (where sources would be) */}
            {isUser && (
              <div className="flex items-center gap-2 mt-0.5">
                {message.error && (
                  <div className="flex items-center gap-1 text-[10px] text-red-500 font-medium animate-pulse">
                    <AlertCircle className="w-3 h-3" />
                    <span>Échec</span>
                  </div>
                )}
                <p className="text-[10px] text-slate-400">
                  {formatTime(message.timestamp)}
                </p>
              </div>
            )}
          </div>

          {!isStreaming && (
            <div className={cn(
              "flex items-center gap-1 opacity-100 md:opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5",
              isUser ? "flex-row-reverse" : "flex-row"
            )}>
              <button
                onClick={handleCopy}
                className="p-1 rounded-md text-slate-400 hover:text-emerald-600 hover:bg-slate-100 transition-colors cursor-pointer"
                title="Copier le message"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              </button>

              <Popover
                isOpen={isShareOpen}
                onClose={() => setIsShareOpen(false)}
                align={isUser ? "left" : "right"}
                position="top"
                contentClassName="min-w-[220px]"
                trigger={
                  <button
                    onClick={() => setIsShareOpen(!isShareOpen)}
                    className={cn(
                      "p-1 rounded-md text-slate-400 hover:text-blue-500 hover:bg-slate-100 transition-colors cursor-pointer",
                      isShareOpen && "text-blue-500 bg-blue-50"
                    )}
                    title="Partager le message"
                  >
                    <Share2 className="w-3.5 h-3.5" />
                  </button>
                }
              >
                <div className="p-3 bg-white/95 backdrop-blur-xl">
                  <div className="flex items-center justify-between border-b border-slate-100/80 pb-2 mb-3">
                    <span className="text-[11px] font-bold uppercase tracking-widest bg-black bg-clip-text text-transparent">
                      Partager via
                    </span>
                  </div>
                  <SocialShareButtons 
                    url={typeof window !== 'undefined' ? window.location.href : ''} 
                    title={message.content.substring(0, 100)} 
                  />
                </div>
              </Popover>
            </div>
          )}
        </div>

        {/* Time for Bot (below sources) */}
        {!isUser && (
          <div className="flex items-center gap-2 mt-1 w-full flex-row">
            <p className="text-[10px] text-slate-400">
              {formatTime(message.timestamp)}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default memo(ChatMessage);
