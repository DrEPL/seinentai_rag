/**
 * SEINENTAI4US — Chat page
 */
import { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { MessageSquarePlus, Sparkles, Search, FileText, Zap } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import ChatMessage from '@/components/chat/ChatMessage';
import ChatInput from '@/components/chat/ChatInput';
import AgentActivity from '@/components/chat/AgentActivity';
import { ChatMessageSkeleton } from '@/components/ui/Skeleton';
import { useChat } from '@/hooks/useChat';
import { cn } from '@/lib/utils';

const suggestions = [
  { icon: Search, text: 'Rechercher un concept dans mes documents' },
  { icon: FileText, text: 'Résumer un document spécifique' },
  { icon: Zap, text: 'Comparer des informations entre documents' },
  { icon: Sparkles, text: 'Expliquer un sujet complexe' },
];

export default function ChatPage() {
  const {
    currentMessages,
    isStreaming,
    loading,
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
      <div className="flex-1 flex flex-col relative overflow-hidden chat-bg-pattern">
        {/* Messages area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto no-scrollbar scroll-smooth pb-4">
          {isEmpty ? (
            /* Empty state */
            <div className="flex-1 flex items-center justify-center min-h-full px-4">
              <div className="text-center max-w-md">
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
                  Comment puis-je vous aider ? Posez votre question sur vos documents.
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
            /* Messages */
            <div className="max-w-3xl mx-auto py-6 space-y-6 px-4">
              {loading ? (
                <div className="space-y-6">
                  <ChatMessageSkeleton isUser />
                  <ChatMessageSkeleton />
                </div>
              ) : (
                currentMessages.map((msg, i) => (
                  <ChatMessage
                    key={msg.id}
                    message={msg}
                    isStreaming={isStreaming && i === currentMessages.length - 1 && msg.role === 'assistant'}
                  />
                ))
              )}
              {/* Agent activity */}
              <AgentActivity />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="shrink-0">
          <ChatInput
            onSend={sendMessage}
            isStreaming={isStreaming}
            onStop={stopStreaming}
          />
        </div>
      </div>
    </AppLayout>
  );
}
