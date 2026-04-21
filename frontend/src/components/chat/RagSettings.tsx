/**
 * SEINENTAI4US — RAG Settings content
 */
import { Sparkles, X } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateRagSettings } from '@/store/slices/chatSlice';
import Toggle from '@/components/ui/Toggle';
import Slider from '@/components/ui/Slider';

interface RagSettingsProps {
  onClose?: () => void;
}

export default function RagSettings({ onClose }: RagSettingsProps) {
  const dispatch = useAppDispatch();
  const settings = useAppSelector((s) => s.chat.ragSettings);

  return (
    <div className="p-4 space-y-4 w-72 sm:w-80">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-50">
        <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
          Paramètres RAG
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5 text-slate-400" />
          </button>
        )}
      </div>

      {/* Toggles */}
      <div className="space-y-3">
        <Toggle
          checked={settings.stream}
          onChange={(v) => dispatch(updateRagSettings({ stream: v }))}
          label="Streaming"
          className="!py-0"
          labelClassName="text-xs"
        />
        <Toggle
          checked={settings.use_agent}
          onChange={(v) => dispatch(updateRagSettings({ use_agent: v }))}
          label="Mode Agent IA"
          className="!py-0"
          labelClassName="text-xs"
        />
        <Toggle
          checked={settings.use_hybrid}
          onChange={(v) => dispatch(updateRagSettings({ use_hybrid: v }))}
          label="Recherche Hybride"
          className="!py-0"
          labelClassName="text-xs"
        />
        <Toggle
          checked={settings.use_hyde}
          onChange={(v) => dispatch(updateRagSettings({ use_hyde: v }))}
          label="HyDE"
          className="!py-0"
          labelClassName="text-xs"
        />
      </div>

      {/* Sliders */}
      <div className="space-y-4 pt-3 border-t border-slate-50">
        <Slider
          value={settings.temperature}
          onChange={(v) => dispatch(updateRagSettings({ temperature: v }))}
          min={0}
          max={1}
          step={0.1}
          label="Température"
          labelClassName="text-[10px] uppercase tracking-wider text-slate-400 font-bold"
          displayValue={settings.temperature.toFixed(1)}
        />
        <Slider
          value={settings.search_limit}
          onChange={(v) => dispatch(updateRagSettings({ search_limit: v }))}
          min={1}
          max={20}
          step={1}
          label="Résultats"
          labelClassName="text-[10px] uppercase tracking-wider text-slate-400 font-bold"
          displayValue={String(settings.search_limit)}
        />
      </div>
    </div>
  );
}
