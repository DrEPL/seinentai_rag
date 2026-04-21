/**
 * SEINENTAI4US — Documents management page (Admin)
 */
import { useEffect, useCallback, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, Trash2, RefreshCw, HardDrive, File, AlertCircle, CheckCircle, CloudUpload } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';
import { DocumentCardSkeleton } from '@/components/ui/Skeleton';
import { useDocuments } from '@/hooks/useDocuments';
import { cn, formatFileSize, formatDate } from '@/lib/utils';

export default function DocumentsPage() {
  const { documents, loading, uploading, uploadProgress, reindexing, loadDocuments, uploadDocument, deleteDocument, reindexAll } = useDocuments();
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadDocument(file);
  }, [uploadDocument]);

  const indexedCount = documents.filter((d) => d.indexed).length;
  const stats = [
    { label: 'Documents', value: documents.length, icon: FileText, color: 'text-indigo-500', bg: 'bg-indigo-50' },
    { label: 'Indexés', value: indexedCount, icon: CheckCircle, color: 'text-emerald-500', bg: 'bg-emerald-50' },
    { label: 'En attente', value: documents.length - indexedCount, icon: AlertCircle, color: 'text-amber-500', bg: 'bg-amber-50' },
    { label: 'Stockage', value: formatFileSize(documents.reduce((a: number, d: any) => a + (d.size || 0), 0)), icon: HardDrive, color: 'text-blue-500', bg: 'bg-blue-50' },
  ];

  return (
    <AppLayout title="Gestion des documents" pageTitle="Documents">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {stats.map((s, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }} className="card p-4">
              <div className="flex items-center gap-3">
                <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', s.bg)}><s.icon className={cn('w-5 h-5', s.color)} /></div>
                <div><p className="text-lg font-bold text-slate-900">{s.value}</p><p className="text-[11px] text-slate-400">{s.label}</p></div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-700">Fichiers</h2>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" loading={reindexing} icon={<RefreshCw className="w-3.5 h-3.5" />} onClick={() => reindexAll(false)}>Réindexer</Button>
            <Button size="sm" icon={<Upload className="w-3.5 h-3.5" />} onClick={() => fileInputRef.current?.click()}>Uploader</Button>
            <input ref={fileInputRef} type="file" accept=".pdf,.txt,.md,.docx,.csv" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadDocument(f); e.target.value = ''; }} />
          </div>
        </div>

        {/* Drop zone */}
        <div onDragOver={(e) => { e.preventDefault(); setDragActive(true); }} onDragLeave={() => setDragActive(false)} onDrop={handleDrop}
          className={cn('border-2 border-dashed rounded-2xl transition-all duration-200 cursor-pointer', dragActive ? 'border-indigo-400 bg-indigo-50/50' : 'border-slate-200 hover:border-slate-300 bg-white', uploading && 'pointer-events-none')}
          onClick={() => !uploading && fileInputRef.current?.click()}>
          <div className="flex flex-col items-center justify-center py-10 px-4">
            {uploading ? (
              <><div className="w-full max-w-xs mb-3"><div className="h-2 bg-slate-100 rounded-full overflow-hidden"><motion.div className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full" initial={{ width: 0 }} animate={{ width: `${uploadProgress}%` }} /></div></div><p className="text-sm text-indigo-600 font-medium">{uploadProgress}%</p></>
            ) : (
              <><CloudUpload className={cn('w-10 h-10 mb-3', dragActive ? 'text-indigo-500' : 'text-slate-300')} /><p className="text-sm text-slate-600 font-medium">Glissez un fichier ici</p><p className="text-xs text-slate-400 mt-1">PDF, TXT, Markdown, DOCX, CSV</p></>
            )}
          </div>
        </div>

        {/* List */}
        {loading ? <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <DocumentCardSkeleton key={i} />)}</div>
        : documents.length === 0 ? <div className="text-center py-12"><File className="w-12 h-12 text-slate-200 mx-auto mb-3" /><p className="text-slate-500">Aucun document</p></div>
        : <div className="space-y-2"><AnimatePresence mode="popLayout">{documents.map((doc, i) => (
          <motion.div key={doc.filename} layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ delay: i * 0.03 }} className="card p-4 flex items-center gap-4 hover:shadow-md transition-shadow group">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0"><FileText className="w-5 h-5 text-indigo-500" /></div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900 truncate">{doc.filename}</p>
              <div className="flex items-center gap-3 mt-1">
                {doc.size && <span className="text-[11px] text-slate-400">{formatFileSize(doc.size)}</span>}
                {doc.chunk_count !== null && <span className="text-[11px] text-slate-400">{doc.chunk_count} chunks</span>}
              </div>
            </div>
            <Badge variant={doc.indexed ? 'success' : 'warning'} dot>{doc.indexed ? 'Indexé' : 'En attente'}</Badge>
            <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(doc.filename); }} className="p-2 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100 cursor-pointer"><Trash2 className="w-4 h-4" /></button>
          </motion.div>
        ))}</AnimatePresence></div>}

        {/* Delete modal */}
        <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Confirmer la suppression" size="sm">
          <p className="text-sm text-slate-600 mb-6">Supprimer <strong>{deleteTarget}</strong> ? Irréversible.</p>
          <div className="flex gap-3 justify-end">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Annuler</Button>
            <Button variant="danger" icon={<Trash2 className="w-4 h-4" />} onClick={() => { if (deleteTarget) { deleteDocument(deleteTarget); setDeleteTarget(null); } }}>Supprimer</Button>
          </div>
        </Modal>
      </div>
    </AppLayout>
  );
}
