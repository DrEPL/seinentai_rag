/**
 * SEINENTAI4US — Documents Slice
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export interface DocumentItem {
  filename: string;
  size: number | null;
  last_modified: string | null;
  content_type: string | null;
  indexed: boolean;
  chunk_count: number | null;
}

export interface DocumentStatus {
  filename: string;
  status: 'indexed' | 'pending' | 'not_found' | 'error';
  chunk_count?: number;
  indexed_at?: string;
  error?: string;
}

interface DocumentsState {
  documents: DocumentItem[];
  statuses: Record<string, DocumentStatus>;
  loading: boolean;
  uploading: boolean;
  uploadProgress: number;
  reindexing: boolean;
  error: string | null;
}

const initialState: DocumentsState = {
  documents: [],
  statuses: {},
  loading: false,
  uploading: false,
  uploadProgress: 0,
  reindexing: false,
  error: null,
};

const documentsSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {
    setDocuments: (state, action: PayloadAction<DocumentItem[]>) => {
      state.documents = action.payload;
      state.loading = false;
    },
    removeDocument: (state, action: PayloadAction<string>) => {
      state.documents = state.documents.filter((d) => d.filename !== action.payload);
    },
    setDocumentStatus: (state, action: PayloadAction<DocumentStatus>) => {
      state.statuses[action.payload.filename] = action.payload;
    },
    setDocumentsLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setUploading: (state, action: PayloadAction<boolean>) => {
      state.uploading = action.payload;
      if (!action.payload) state.uploadProgress = 0;
    },
    setUploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },
    setReindexing: (state, action: PayloadAction<boolean>) => {
      state.reindexing = action.payload;
    },
    setDocumentsError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.loading = false;
    },
  },
});

export const {
  setDocuments,
  removeDocument,
  setDocumentStatus,
  setDocumentsLoading,
  setUploading,
  setUploadProgress,
  setReindexing,
  setDocumentsError,
} = documentsSlice.actions;
export default documentsSlice.reducer;
