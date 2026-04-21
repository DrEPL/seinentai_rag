/**
 * SEINENTAI4US — Agent Activity Panel (Fluid & Subtle Experience)
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
    color: 'text-slate-500', 
    bgColor: 'bg-slate-50/50', 
    borderColor: 'border-slate-100' 
  },
  tool_call: { 
    icon: Wrench, 
    label: 'Action en cours', 
    color: 'text-slate-600', 
    bgColor: 'bg-slate-100/50', 
    borderColor: 'border-slate-200' 
  },
  observation: { 
    icon: Eye, 
    label: 'Analyse', 
    color: 'text-slate-500', 
    bgColor: 'bg-slate-50/50', 
    borderColor: 'border-slate-100' 
  },
  synthesis_start: { 
    icon: Sparkles, 
    label: 'Synthèse', 
    color: 'text-emerald-600', 
    bgColor: 'bg-emerald-50/30', 
    borderColor: 'border-emerald-100/50' 
  },
  error: { 
    icon: AlertCircle, 
    label: 'Erreur', 
    color: 'text-red-500', 
    bgColor: 'bg-red-50/50', 
    borderColor: 'border-red-100' 
  },
};

function StepCard({ step, isActive }: { step: AgentStep; isActive: boolean }) {
  const config = stepConfig[step.type];
  const Icon = config.icon;

  return (
    <motion.div
      key={step.id}
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'flex items-center gap-3 px-4 py-2.5 rounded-xl border backdrop-blur-[2px] transition-all duration-300',
        config.bgColor,
        config.borderColor,
        !isActive && 'opacity-60 grayscale-[0.5]'
      )}
    >
      <div className={cn(
        'flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center bg-white shadow-sm border border-slate-100',
        config.color
      )}>
        {isActive && step.type !== 'synthesis_start' ? (
          <Loader2 className="w-4 h-4 animate-spin opacity-70" />
        ) : (
          <Icon className="w-4 h-4" />
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn('text-[10px] font-bold uppercase tracking-wider', config.color)}>
            {config.label}
          </span>
          {isActive && (
            <span className="flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-1.5 w-1.5 rounded-full bg-slate-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-slate-500"></span>
            </span>
          )}
        </div>

        <div className="text-[12px] text-slate-500 truncate font-medium">
          {step.type === 'thought' && step.content && (
            <span>{step.content}</span>
          )}
          
          {step.type === 'tool_call' && (
            <span className="font-semibold text-slate-700">{step.tool}</span>
          )}

          {step.type === 'observation' && (
            <div className="flex items-center gap-2">
              <span>Résultats analysés</span>
              {step.score !== undefined && (
                <span className="text-[10px] font-mono bg-slate-200/50 px-1 rounded text-slate-600">
                  {(step.score * 100).toFixed(0)}%
                </span>
              )}
            </div>
          )}

          {step.type === 'synthesis_start' && (
            <span className="text-emerald-600 font-semibold">Génération de la réponse...</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function AgentActivity() {
  const { steps, isActive, mode } = useAppSelector((s) => s.agent);

  // We only show the last step
  const currentStep = steps[steps.length - 1];

  // If we have steps, we show them even if not "active" (unless it's cleared)
  if (!currentStep) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-3xl mx-auto px-4 md:px-0 mb-4"
    >
      <AnimatePresence mode="wait">
        <StepCard key={currentStep.id} step={currentStep} isActive={isActive} />
      </AnimatePresence>
    </motion.div>
  );
}
