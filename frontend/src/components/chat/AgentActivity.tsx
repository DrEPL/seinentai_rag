/**
 * SEINENTAI4US — Agent Activity Panel (Fluid Experience)
 */
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Wrench,
  Eye,
  Sparkles,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppSelector } from '@/store/hooks';
import type { AgentStep } from '@/store/slices/agentSlice';

const stepConfig: Record<AgentStep['type'], { icon: typeof Brain; label: string; color: string; bgColor: string; borderColor: string }> = {
  thought: { 
    icon: Brain, 
    label: 'Réflexion', 
    color: 'text-emerald-600', 
    bgColor: 'bg-emerald-50/50', 
    borderColor: 'border-emerald-100' 
  },
  tool_call: { 
    icon: Wrench, 
    label: 'Utilisation d\'un outil', 
    color: 'text-blue-600', 
    bgColor: 'bg-blue-50/50', 
    borderColor: 'border-blue-100' 
  },
  observation: { 
    icon: Eye, 
    label: 'Analyse des résultats', 
    color: 'text-amber-600', 
    bgColor: 'bg-amber-50/50', 
    borderColor: 'border-amber-100' 
  },
  synthesis_start: { 
    icon: Sparkles, 
    label: 'Synthèse finale', 
    color: 'text-indigo-600', 
    bgColor: 'bg-indigo-50/50', 
    borderColor: 'border-indigo-100' 
  },
  error: { 
    icon: AlertCircle, 
    label: 'Erreur', 
    color: 'text-red-600', 
    bgColor: 'bg-red-50/50', 
    borderColor: 'border-red-100' 
  },
};

function StepCard({ step }: { step: AgentStep }) {
  const config = stepConfig[step.type];
  const Icon = config.icon;

  return (
    <motion.div
      key={step.id}
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.98 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={cn(
        'flex items-start gap-4 p-4 rounded-2xl border backdrop-blur-sm shadow-sm transition-all duration-300',
        config.bgColor,
        config.borderColor
      )}
    >
      <div className={cn(
        'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center bg-white shadow-sm border border-slate-100',
        config.color
      )}>
        <Icon className="w-5 h-5 animate-pulse" />
      </div>
      
      <div className="flex-1 min-w-0 py-0.5">
        <div className="flex items-center justify-between">
          <span className={cn('text-[11px] font-bold uppercase tracking-wider', config.color)}>
            {config.label}
          </span>
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
        </div>

        <div className="mt-1.5 text-sm text-slate-700 leading-relaxed font-medium">
          {step.type === 'thought' && step.content && (
            <p className="line-clamp-3 italic opacity-80">"{step.content}"</p>
          )}
          
          {step.type === 'tool_call' && (
            <div>
              <p className="font-semibold">{step.tool}</p>
              {step.params && (
                <p className="text-xs text-slate-500 mt-1 truncate">
                  Paramètres : {JSON.stringify(step.params)}
                </p>
              )}
            </div>
          )}

          {step.type === 'observation' && (
            <div className="space-y-1">
              {step.score !== undefined && (
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${step.score * 100}%` }}
                      className={cn(
                        'h-full rounded-full',
                        step.sufficient ? 'bg-emerald-500' : 'bg-amber-500'
                      )}
                    />
                  </div>
                  <span className="text-[10px] font-mono font-bold text-slate-500">
                    {(step.score * 100).toFixed(0)}%
                  </span>
                </div>
              )}
              {step.feedback && (
                <p className="text-xs text-slate-600 line-clamp-2">{step.feedback}</p>
              )}
            </div>
          )}

          {step.type === 'synthesis_start' && (
            <p className="text-slate-600 animate-pulse">Préparation de la réponse détaillée...</p>
          )}

          {step.type === 'error' && (
            <p className="text-red-600">{step.message || step.content}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function AgentActivity() {
  const { steps, isActive, mode } = useAppSelector((s) => s.agent);

  // We only show the very last step to give that "current thought" feeling
  const currentStep = steps[steps.length - 1];

  if (!isActive || !currentStep) return null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="max-w-3xl mx-auto px-4 md:px-0 mb-6"
    >
      <div className="flex items-center gap-2 mb-3 px-1">
        <Loader2 className="w-3.5 h-3.5 text-emerald-500 animate-spin" />
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em]">
          Raisonnement de l&apos;agent {mode === 'agent' ? 'Expert' : ''}
        </span>
      </div>

      <AnimatePresence mode="wait">
        <StepCard key={currentStep.id} step={currentStep} />
      </AnimatePresence>
    </motion.div>
  );
}
