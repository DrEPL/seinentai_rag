/**
 * SEINENTAI4US — Search hook
 */
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setSearchResults, setSearchLoading, setSearchError, clearSearch } from '@/store/slices/searchSlice';
import { addToast } from '@/store/slices/uiSlice';
import { searchApi } from '@/api/search';

export function useSearch() {
  const dispatch = useAppDispatch();
  const { query, results, total, searchTimeMs, searchType, loading, error } = useAppSelector(
    (s) => s.search
  );

  const semanticSearch = useCallback(
    async (q: string, options?: { limit?: number; use_hybrid?: boolean; use_hyde?: boolean }) => {
      dispatch(setSearchLoading(true));
      try {
        const res = await searchApi.semantic({
          query: q,
          limit: options?.limit || 10,
          use_hybrid: options?.use_hybrid || false,
          use_hyde: options?.use_hyde || false,
        });
        dispatch(
          setSearchResults({
            query: q,
            results: res.data.results || [],
            total: res.data.total,
            searchTimeMs: res.data.search_time_ms,
            searchType: 'semantic',
          })
        );
      } catch (err) {
        dispatch(setSearchError((err as Error).message));
        dispatch(addToast({ type: 'error', message: 'Erreur de recherche' }));
      }
    },
    [dispatch]
  );

  const hybridSearch = useCallback(
    async (q: string, limit = 10) => {
      dispatch(setSearchLoading(true));
      try {
        const res = await searchApi.hybrid({ q, limit });
        dispatch(
          setSearchResults({
            query: q,
            results: res.data.results || [],
            total: res.data.total,
            searchTimeMs: res.data.search_time_ms,
            searchType: 'hybrid',
          })
        );
      } catch (err) {
        dispatch(setSearchError((err as Error).message));
        dispatch(addToast({ type: 'error', message: 'Erreur de recherche hybride' }));
      }
    },
    [dispatch]
  );

  const clear = useCallback(() => {
    dispatch(clearSearch());
  }, [dispatch]);

  return { query, results, total, searchTimeMs, searchType, loading, error, semanticSearch, hybridSearch, clear };
}
