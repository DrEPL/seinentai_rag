/**
 * SEINENTAI4US — Export & Share Utilities
 */
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { type ChatMessage } from '@/store/slices/chatSlice';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

/**
 * Exports a conversation to PDF
 */
export const exportConversationToPDF = (messages: ChatMessage[], title: string = 'Conversation') => {
  try {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    let yPos = 20;

    // Header
    doc.setFontSize(20);
    doc.setTextColor(15, 23, 42); // slate-900
    doc.text('SEINENTAI4US', 14, yPos);
    yPos += 10;

    doc.setFontSize(12);
    doc.setTextColor(100, 116, 139); // slate-500
    doc.text(`Conversation : ${title}`, 14, yPos);
    doc.text(`Date : ${format(new Date(), 'dd/MM/yyyy', { locale: fr })}`, pageWidth - 14, yPos, { align: 'right' });
    yPos += 15;

    // Divider
    doc.setDrawColor(226, 232, 240); // slate-200
    doc.line(14, yPos, pageWidth - 14, yPos);
    yPos += 15;

    // Messages
    messages.forEach((msg) => {
      const isUser = msg.role === 'user';
      const roleText = isUser ? 'VOUS' : 'ASSISTANT';
      
      // Check page overflow
      if (yPos > 270) {
        doc.addPage();
        yPos = 20;
      }

      // Role Badge
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(isUser ? 71 : 16, isUser ? 85 : 185, isUser ? 105 : 129); // slate-600 or emerald-600
      doc.text(roleText, 14, yPos);
      yPos += 6;

      // Content
      doc.setFontSize(11);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(51, 65, 85); // slate-700
      
      // Clean content (strip markdown roughly or use standard text)
      const cleanContent = msg.content.replace(/[#*`_~]/g, '');
      const splitContent = doc.splitTextToSize(cleanContent, pageWidth - 28);
      
      doc.text(splitContent, 14, yPos);
      yPos += (splitContent.length * 6) + 10;
    });

    // Save
    const fileName = `seinentai-conversation-${new Date().getTime()}.pdf`;
    doc.save(fileName);
    return true;
  } catch (error) {
    console.error('PDF Export Error:', error);
    return false;
  }
};

/**
 * Copy to Clipboard Utility
 */
export const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Copy failed:', err);
    return false;
  }
};
