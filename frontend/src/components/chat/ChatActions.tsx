/**
 * SEINENTAI4US — Global Chat Actions (Export, Share)
 */
import { useState } from 'react';
import { Download, Share2, Send, Briefcase, MessageSquare, MoreVertical, FileDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useAppDispatch } from '@/store/hooks';
import { addToast } from '@/store/slices/uiSlice';
import { exportConversationToPDF } from '@/utils/exportUtils';
import type { ChatMessage } from '@/store/slices/chatSlice';
import Popover from '@/components/ui/Popover';
import SocialShareButtons from './SocialShareButtons';

interface ChatActionsProps {
  messages: ChatMessage[];
  sessionId?: string;
  isStreaming?: boolean;
}

export default function ChatActions({ messages, sessionId, isStreaming }: ChatActionsProps) {
  const dispatch = useAppDispatch();
  const [isShareOpen, setIsShareOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  if (messages.length === 0) return null;

  const handleExportPDF = async () => {
    if (isExporting) return;
    setIsExporting(true);
    
    // Small delay to show activity
    setTimeout(async () => {
      const success = exportConversationToPDF(messages, "Conversation SEINENTAI4US");
      if (success) {
        dispatch(addToast({ type: 'success', message: 'PDF généré avec succès !' }));
      } else {
        dispatch(addToast({ type: 'error', message: "Échec de l'exportation PDF" }));
      }
      setIsExporting(false);
    }, 500);
  };


  return (
    <div className="flex items-center gap-2">
      {/* Export Button */}
      <button
        onClick={handleExportPDF}
        disabled={isExporting || isStreaming}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
          "bg-white border border-slate-200 text-slate-600 shadow-sm",
          "hover:border-emerald-200 hover:text-emerald-700 hover:bg-emerald-50/50",
          "disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        )}
      >
        <FileDown className={cn("w-3.5 h-3.5", isExporting && "animate-bounce")} />
        {isExporting ? 'Exportation...' : 'Exporter PDF'}
      </button>

      {/* Share Dropdown */}
      <Popover
        isOpen={isShareOpen}
        onClose={() => setIsShareOpen(false)}
        align="right"
        position="bottom"
        contentClassName="min-w-[200px]"
        trigger={
          <button
            onClick={() => setIsShareOpen(!isShareOpen)}
            className={cn(
              "p-2 rounded-lg bg-white border border-slate-200 text-slate-600 shadow-sm",
              "hover:border-slate-300 hover:text-slate-900 transition-all cursor-pointer",
              isShareOpen && "border-emerald-200 bg-emerald-50/30"
            )}
          >
            <Share2 className="w-3.5 h-3.5" />
          </button>
        }
      >
        <div className="p-1">
          <p className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-50 mb-1">
            Partager via
          </p>
          <SocialShareButtons 
            url={typeof window !== 'undefined' ? window.location.href : ''} 
            title={messages[0]?.content.substring(0, 100)} 
          />
        </div>
      </Popover>
    </div>
  );
}
