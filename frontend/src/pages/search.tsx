/**
 * SEINENTAI4US — Search page
 */
import { useState, type FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search as SearchIcon,
  FileText,
  Clock,
  Zap,
  ToggleLeft,
  ToggleRight,
  Hash,
} from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { useSearch } from '@/hooks/useSearch';
import { cn, formatFileSize } from '@/lib/utils';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [useHybrid, setUseHybrid] = useState(false);
  const { results, total, searchTimeMs, searchType, loading, semanticSearch, hybridSearch, clear } =
    useSearch();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    if (useHybrid) {
      hybridSearch(query.trim());
    } else {
      semanticSearch(query.trim());
    }
  };

  return (
    <AppLayout title="Recherche sémantique" pageTitle="Recherche">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Search form */}
        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-1">
                <Input
                  placeholder="Rechercher dans vos documents..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  icon={<SearchIcon className="w-4 h-4" />}
                />
              </div>
              <Button type="submit" loading={loading} icon={<SearchIcon className="w-4 h-4" />}>
                Rechercher
              </Button>
            </div>

            {/* Search options */}
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => setUseHybrid(!useHybrid)}
                className="flex items-center gap-2 text-sm text-slate-600 hover:text-indigo-600 transition-colors cursor-pointer"
              >
                {useHybrid ? (
                  <ToggleRight className="w-5 h-5 text-indigo-500" />
                ) : (
                  <ToggleLeft className="w-5 h-5 text-slate-400" />
                )}
                Recherche hybride
              </button>
            </div>
          </form>
        </div>

        {/* Results header */}
        {total > 0 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-600">
              <span className="font-semibold text-slate-900">{total}</span> résultat
              {total > 1 ? 's' : ''} trouvé{total > 1 ? 's' : ''}
            </p>
            <div className="flex items-center gap-3">
              <Badge variant="info" dot>
                {searchType === 'hybrid' ? 'Hybride' : 'Sémantique'}
              </Badge>
              <span className="flex items-center gap-1 text-xs text-slate-400">
                <Clock className="w-3 h-3" />
                {searchTimeMs}ms
              </span>
            </div>
          </div>
        )}

        {/* Results */}
        <AnimatePresence mode="popLayout">
          {results.map((result, i) => (
            <motion.div
              key={`${result.filename}-${result.chunk_index}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ delay: i * 0.05 }}
              className="card p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-indigo-500" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{result.filename}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-slate-400 flex items-center gap-0.5">
                        <Hash className="w-2.5 h-2.5" />
                        Chunk {result.chunk_index}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <Zap className="w-3 h-3 text-amber-500" />
                  <span className="text-sm font-bold text-indigo-600 font-mono">
                    {(result.score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <p className="text-sm text-slate-600 leading-relaxed line-clamp-4">
                {result.text}
              </p>

              {/* Score bar */}
              <div className="mt-3">
                <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${result.score * 100}%` }}
                    transition={{ delay: 0.3 + i * 0.05, duration: 0.5, ease: 'easeOut' }}
                    className="h-full bg-gradient-to-r from-indigo-400 to-violet-500 rounded-full"
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty state */}
        {!loading && total === 0 && query && (
          <div className="text-center py-12">
            <SearchIcon className="w-12 h-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500">Aucun résultat pour &quot;{query}&quot;</p>
          </div>
        )}

        {/* Initial empty state */}
        {!loading && total === 0 && !query && (
          <div className="text-center py-16">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-50 mb-4"
            >
              <SearchIcon className="w-7 h-7 text-indigo-400" />
            </motion.div>
            <p className="text-slate-500 mb-1">Explorez vos documents</p>
            <p className="text-xs text-slate-400">
              Saisissez une requête pour lancer la recherche sémantique
            </p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
