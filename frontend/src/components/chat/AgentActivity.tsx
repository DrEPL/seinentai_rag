/**
 * SEINENTAI4US — Agent Activity Panel
 */
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Wrench,
  Eye,
  Sparkles,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { useAppSelector } from '@/store/hooks';
import type { AgentStep } from '@/store/slices/agentSlice';

const stepConfig: Record<AgentStep['type'], { icon: typeof Brain; label: string; color: string; bgColor: string }> = {
  thought: { icon: Brain, label: 'Réflexion', color: 'text-violet-600', bgColor: 'bg-violet-50 border-violet-200' },
  tool_call: { icon: Wrench, label: 'Outil', color: 'text-blue-600', bgColor: 'bg-blue-50 border-blue-200' },
  observation: { icon: Eye, label: 'Observation', color: 'text-amber-600', bgColor: 'bg-amber-50 border-amber-200' },
  synthesis_start: { icon: Sparkles, label: 'Synthèse', color: 'text-emerald-600', bgColor: 'bg-emerald-50 border-emerald-200' },
  error: { icon: AlertCircle, label: 'Erreur', color: 'text-red-600', bgColor: 'bg-red-50 border-red-200' },
};

function StepItem({ step, index }: { step: AgentStep; index: number }) {
  const config = stepConfig[step.type];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
      className={cn('flex items-start gap-2.5 px-3 py-2 rounded-lg border', config.bgColor)}
    >
      <div className={cn('flex-shrink-0 mt-0.5', config.color)}>
        <Icon className="w-3.5 h-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <span className={cn('text-[10px] font-semibold uppercase tracking-wider', config.color)}>
          {config.label}
        </span>
        {step.type === 'thought' && step.content && (
          <p className="text-xs text-slate-600 mt-0.5 line-clamp-3">{step.content}</p>
        )}
        {step.type === 'tool_call' && (
          <div className="mt-0.5">
            <p className="text-xs font-medium text-slate-700">
              {step.tool}
            </p>
            {step.result_preview && (
              <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{step.result_preview}</p>
            )}
          </div>
        )}
        {step.type === 'observation' && (
          <div className="mt-0.5">
            {step.score !== undefined && (
              <span className="text-[11px] font-mono text-amber-600">
                Score: {(step.score * 100).toFixed(0)}%
                {step.sufficient !== undefined && (
                  <span className={step.sufficient ? ' ✓' : ' ✗'}>
                    {step.sufficient ? ' Suffisant' : ' Insuffisant'}
                  </span>
                )}
              </span>
            )}
            {step.feedback && (
              <p className="text-xs text-slate-600 mt-0.5">{step.feedback}</p>
            )}
          </div>
        )}
        {step.type === 'error' && (
          <p className="text-xs text-red-600 mt-0.5">{step.message || step.content}</p>
        )}
      </div>
    </motion.div>
  );
}

export default function AgentActivity() {
  const { steps, isActive, mode } = useAppSelector((s) => s.agent);
  const [collapsed, setCollapsed] = useState(false);

  if (steps.length === 0 && !isActive) return null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      className="max-w-3xl mx-auto px-4 md:px-0 mb-3"
    >
      <div className="rounded-xl border border-slate-200 bg-white/60 backdrop-blur-sm overflow-hidden shadow-sm">
        {/* Header */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-slate-50 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <div className={cn(
              'w-2 h-2 rounded-full',
              isActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-300'
            )} />
            <span className="text-xs font-semibold text-slate-700">
              Agent {mode === 'agent' ? 'Agentic' : 'Statique'}
            </span>
            <span className="text-[10px] text-slate-400">
              ({steps.length} étape{steps.length > 1 ? 's' : ''})
            </span>
          </div>
          {collapsed ? (
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          ) : (
            <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
          )}
        </button>

        {/* Steps */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="px-3 pb-3 space-y-1.5 max-h-[240px] overflow-y-auto no-scrollbar"
            >
              {steps.map((step, i) => (
                <StepItem key={step.id} step={step} index={i} />
              ))}
              {isActive && (
                <div className="flex items-center gap-2 px-3 py-2">
                  <div className="typing-dots">
                    <span /><span /><span />
                  </div>
                  <span className="text-[10px] text-slate-400">En cours...</span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
