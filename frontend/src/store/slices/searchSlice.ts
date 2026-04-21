/**
 * SEINENTAI4US — Search Slice
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export interface SearchResult {
  text: string;
  filename: string;
  score: number;
  chunk_index: number;
  total_chunks?: number;
  doc_id?: string;
  metadata?: Record<string, unknown>;
}

interface SearchState {
  query: string;
  results: SearchResult[];
  total: number;
  searchTimeMs: number;
  searchType: 'semantic' | 'hybrid';
  loading: boolean;
  error: string | null;
}

const initialState: SearchState = {
  query: '',
  results: [],
  total: 0,
  searchTimeMs: 0,
  searchType: 'semantic',
  loading: false,
  error: null,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setSearchResults: (
      state,
      action: PayloadAction<{
        query: string;
        results: SearchResult[];
        total: number;
        searchTimeMs: number;
        searchType: 'semantic' | 'hybrid';
      }>
    ) => {
      state.query = action.payload.query;
      state.results = action.payload.results;
      state.total = action.payload.total;
      state.searchTimeMs = action.payload.searchTimeMs;
      state.searchType = action.payload.searchType;
      state.loading = false;
      state.error = null;
    },
    setSearchLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setSearchError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.loading = false;
    },
    clearSearch: (state) => {
      state.query = '';
      state.results = [];
      state.total = 0;
      state.searchTimeMs = 0;
      state.error = null;
    },
  },
});

export const { setSearchResults, setSearchLoading, setSearchError, clearSearch } = searchSlice.actions;
export default searchSlice.reducer;
