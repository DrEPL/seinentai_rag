/**
 * SEINENTAI4US — RAG Settings panel
 */
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Zap, Layers, FlaskConical } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateRagSettings } from '@/store/slices/chatSlice';
import { setRagSettingsOpen } from '@/store/slices/uiSlice';
import Toggle from '@/components/ui/Toggle';
import Slider from '@/components/ui/Slider';

export default function RagSettings() {
  const dispatch = useAppDispatch();
  const open = useAppSelector((s) => s.ui.ragSettingsOpen);
  const settings = useAppSelector((s) => s.chat.ragSettings);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.98 }}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          className="absolute bottom-full left-0 right-0 mb-2 mx-4 md:mx-auto max-w-3xl z-20"
        >
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl p-5 space-y-5">
            {/* Header */}
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-500" />
                Paramètres
              </h3>
              <button
                onClick={() => dispatch(setRagSettingsOpen(false))}
                className="p-1 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            {/* Toggles */}
            <div className="space-y-4">
              <Toggle
                checked={settings.stream}
                onChange={(v) => dispatch(updateRagSettings({ stream: v }))}
                label="Streaming"
                description="Réponses en temps réel token par token"
              />
              <Toggle
                checked={settings.use_agent}
                onChange={(v) => dispatch(updateRagSettings({ use_agent: v }))}
                label="Mode Agent IA"
                description="Raisonnement multi-étapes avec outils"
              />
              <Toggle
                checked={settings.use_hybrid}
                onChange={(v) => dispatch(updateRagSettings({ use_hybrid: v }))}
                label="Recherche Hybride"
                description="Combine recherche sémantique et lexicale"
              />
              <Toggle
                checked={settings.use_hyde}
                onChange={(v) => dispatch(updateRagSettings({ use_hyde: v }))}
                label="HyDE"
                description="Hypothetical Document Embeddings"
              />
            </div>

            {/* Sliders */}
            <div className="space-y-4 pt-2 border-t border-slate-100">
              <Slider
                value={settings.temperature}
                onChange={(v) => dispatch(updateRagSettings({ temperature: v }))}
                min={0}
                max={1}
                step={0.1}
                label="Température"
                displayValue={settings.temperature.toFixed(1)}
              />
              <Slider
                value={settings.search_limit}
                onChange={(v) => dispatch(updateRagSettings({ search_limit: v }))}
                min={1}
                max={20}
                step={1}
                label="Nombre de résultats"
                displayValue={String(settings.search_limit)}
              />
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
