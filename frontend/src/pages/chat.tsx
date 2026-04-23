/**
 * SEINENTAI4US — Chat page
 */
import { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { MessageSquarePlus, Sparkles, Search, SkullIcon, BanIcon, UserStar, Smile } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import ChatMessage from '@/components/chat/ChatMessage';
import ChatInput from '@/components/chat/ChatInput';
import AgentActivity from '@/components/chat/AgentActivity';
import { ChatMessageSkeleton } from '@/components/ui/Skeleton';
import { useChat } from '@/hooks/useChat';
import { cn } from '@/lib/utils';

const suggestions = [
  { icon: Search, text: 'Quel est le sens de la vie ?' },
  { icon: UserStar, text: 'Qui est Sukuinushisama ?' },
  { icon: Smile, text: 'Comment être heureux ?' },
  { icon: Sparkles, text: 'C\'est quoi le but de l\'humanité ?' },
  { icon: SkullIcon, text: "Il y a quoi après la mort ?" },
  { icon: BanIcon, text: "Le sexe avant le mariage est il un péché ?" },
];

export default function ChatPage() {
  const {
    currentMessages,
    isStreaming,
    loading,
    historyLoading,
    activeSessionId,
    sendMessage,
    stopStreaming,
  } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentMessages, isStreaming]);

  const isEmpty = !activeSessionId && currentMessages.length === 0;

  return (
    <AppLayout pageTitle="Chat RAG" fullHeight>
      <div className="flex-1 flex flex-col pb-8 relative overflow-hidden chat-bg-pattern">
        {/* Messages area */}
        <div
          id="tour-chat-main"
          ref={scrollRef} 
          className="flex-1 overflow-y-auto no-scrollbar scroll-smooth pb-32 pt-4"
        >
          {isEmpty ? (
            <div className="flex-1 flex items-center justify-center min-h-full px-4">
              <div className="text-center max-w-3xl">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.1, duration: 0.4 }}
                  className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-200 mb-6"
                >
                  <MessageSquarePlus className="w-9 h-9 text-white" />
                </motion.div>

                <motion.h2
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="text-2xl font-bold text-slate-900 mb-2"
                >
                  Bonjour ! 👋
                </motion.h2>
                <motion.p
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="text-slate-500 mb-8"
                >
                  Comment puis-je vous aider ? Posez votre question je répondrais en me basant sur les enseignements.
                </motion.p>

                {/* Suggestions */}
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="grid grid-cols-1 sm:grid-cols-2 gap-2"
                >
                  {suggestions.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(s.text)}
                      className={cn(
                        'flex items-center gap-2.5 px-4 py-3 rounded-xl text-left',
                        'text-sm text-slate-600 bg-white border border-slate-200',
                        'hover:border-emerald-200 hover:bg-emerald-50/50 hover:text-emerald-700',
                        'transition-all duration-200 cursor-pointer',
                        'active:scale-[0.98]'
                      )}
                    >
                      <s.icon className="w-4 h-4 flex-shrink-0 text-emerald-500" />
                      <span className="line-clamp-1">{s.text}</span>
                    </button>
                  ))}
                </motion.div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto py-6 space-y-6 px-4">
              {historyLoading && currentMessages.length === 0 ? (
                <div className="space-y-6">
                  <ChatMessageSkeleton isUser />
                  <ChatMessageSkeleton />
                </div>
              ) : (
                currentMessages.map((msg, i) => {
                  const isLastAssistant = i === currentMessages.length - 1 && msg.role === 'assistant';
                  const hasContent = msg.content && msg.content.trim() !== '';
                  // On ne montre un placeholder de message que si on est en train de streamer du vrai SSE
                  const isLoadingPlaceholder = !hasContent && isLastAssistant && isStreaming;
                  const shouldShow = msg.role === 'user' || hasContent || (isStreaming && isLastAssistant) || isLoadingPlaceholder;
                  
                  if (!shouldShow) return null;
                  
                  return (
                    <ChatMessage
                      key={msg.id}
                      message={msg}
                      isStreaming={(isStreaming && isLastAssistant) || isLoadingPlaceholder}
                    />
                  );
                })
              )}
              {/* Agent activity */}
              <AgentActivity />

              {/* Thinking indicator for non-streaming mode */}
              {loading && !isStreaming && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3 px-4 md:px-0"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center bg-gradient-to-br from-slate-700 to-slate-900 shadow-sm">
                    <Sparkles className="w-4 h-4 text-white animate-pulse" />
                  </div>
                  <div className="bg-white border border-slate-100 rounded-2xl px-4 py-3 shadow-sm rounded-tl-md">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium text-slate-500">Réflexion en cours</span>
                      <div className="flex gap-1">
                        <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce"></span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          )}
        </div>

        {/* Bottom Blur/Gradient Overlay */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#f8fafc] via-[#f8fafc]/90 to-transparent pointer-events-none z-10 backdrop-blur-[1px]" />

        {/* Floating Input Overlay */}
        <div className="absolute bottom-0 left-0 right-0 z-20 pointer-events-none">
          <div className="pointer-events-auto">
            <ChatInput
              onSend={sendMessage}
              isStreaming={isStreaming}
              onStop={stopStreaming}
            />
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
