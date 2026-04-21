/**
 * SEINENTAI4US — Search API
 */
import api from './axios';

export interface SearchPayload {
  query: string;
  limit?: number;
  score_threshold?: number;
  filename_filter?: string;
  use_hybrid?: boolean;
  use_hyde?: boolean;
}

export const searchApi = {
  semantic: (data: SearchPayload) => api.post('/search', data),
  hybrid: (params: { q: string; limit?: number; score_threshold?: number }) =>
    api.get('/search/hybrid', { params }),
};
