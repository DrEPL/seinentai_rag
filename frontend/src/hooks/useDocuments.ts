/**
 * SEINENTAI4US — Documents hook
 */
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  setDocuments,
  removeDocument,
  setDocumentsLoading,
  setUploading,
  setUploadProgress,
  setReindexing,
  setDocumentsError,
} from '@/store/slices/documentsSlice';
import { addToast } from '@/store/slices/uiSlice';
import { documentsApi } from '@/api/documents';

export function useDocuments() {
  const dispatch = useAppDispatch();
  const { documents, loading, uploading, uploadProgress, reindexing, error } = useAppSelector(
    (s) => s.documents
  );

  const loadDocuments = useCallback(async () => {
    dispatch(setDocumentsLoading(true));
    try {
      const res = await documentsApi.list();
      dispatch(setDocuments(res.data.documents || []));
    } catch (err) {
      dispatch(setDocumentsError((err as Error).message));
      dispatch(addToast({ type: 'error', message: 'Erreur chargement documents' }));
    }
  }, [dispatch]);

  const uploadDocument = useCallback(
    async (file: File) => {
      dispatch(setUploading(true));
      dispatch(setUploadProgress(0));
      try {
        await documentsApi.upload(file, (pct) => dispatch(setUploadProgress(pct)));
        dispatch(addToast({ type: 'success', message: `"${file.name}" uploadé avec succès` }));
        await loadDocuments();
      } catch (err) {
        dispatch(addToast({ type: 'error', message: (err as Error).message }));
      } finally {
        dispatch(setUploading(false));
      }
    },
    [dispatch, loadDocuments]
  );

  const deleteDocument = useCallback(
    async (filename: string) => {
      try {
        await documentsApi.delete(filename);
        dispatch(removeDocument(filename));
        dispatch(addToast({ type: 'success', message: `"${filename}" supprimé` }));
      } catch (err) {
        dispatch(addToast({ type: 'error', message: (err as Error).message }));
      }
    },
    [dispatch]
  );

  const reindexAll = useCallback(
    async (force = false) => {
      dispatch(setReindexing(true));
      try {
        await documentsApi.reindex({ force });
        dispatch(addToast({ type: 'info', message: 'Réindexation lancée en arrière-plan' }));
      } catch (err) {
        dispatch(addToast({ type: 'error', message: (err as Error).message }));
      } finally {
        dispatch(setReindexing(false));
      }
    },
    [dispatch]
  );

  return {
    documents,
    loading,
    uploading,
    uploadProgress,
    reindexing,
    error,
    loadDocuments,
    uploadDocument,
    deleteDocument,
    reindexAll,
  };
}
