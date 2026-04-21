/**
 * SEINENTAI4US — Documents API
 */
import api from './axios';

export const documentsApi = {
  list: () => api.get('/documents'),
  upload: (file: File, onProgress?: (pct: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      },
    });
  },
  delete: (filename: string) => api.delete(`/documents/${encodeURIComponent(filename)}`),
  getStatus: (filename: string) => api.get(`/documents/${encodeURIComponent(filename)}/status`),
  reindex: (data: { force?: boolean; filenames?: string[] }) =>
    api.post('/documents/reindex', data),
};
