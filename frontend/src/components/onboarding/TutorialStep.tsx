/**
 * SEINENTAI4US — TutorialStep
 * Composant réutilisable pour afficher le contenu d'une étape du tutoriel.
 */
import { type ReactNode } from 'react';

export interface TutorialStepData {
  icon: ReactNode;
  title: string;
  subtitle: string;
  description: string;
  highlights?: { icon: string; label: string; detail: string }[];
  accentColor: string;       // ex: 'from-emerald-400 to-teal-500'
  bgAccent: string;          // ex: 'bg-emerald-50'
  iconBg: string;            // ex: 'bg-emerald-100'
}

interface TutorialStepProps {
  data: TutorialStepData;
  stepIndex: number;
  isActive: boolean;
}

export default function TutorialStep({ data, stepIndex, isActive }: TutorialStepProps) {
  if (!isActive) return null;

  return (
    <div
      className="tutorial-step-content"
      style={{ animation: 'tutorialStepIn 0.45s cubic-bezier(0.34,1.56,0.64,1) both' }}
    >
      {/* ─── Icône hero ──────────────────────────────────────────────────── */}
      <div className="flex justify-center mb-3">
        <div className="relative">
          <div
            className={`w-12 h-12 rounded-xl ${data.bgAccent} flex items-center justify-center shadow-md`}
            style={{ animation: 'stepIconPop 0.5s cubic-bezier(0.34,1.56,0.64,1) 0.1s both' }}
          >
            <div className={`w-6 h-6 text-transparent bg-gradient-to-br ${data.accentColor} [&>svg]:w-full [&>svg]:h-full`}
              style={{ WebkitBackgroundClip: 'text' }}
            >
              {data.icon}
            </div>
          </div>
          {/* Halo décoratif */}
          <div
            className={`absolute inset-0 rounded-2xl opacity-30 blur-xl -z-10 bg-gradient-to-br ${data.accentColor}`}
            style={{ transform: 'scale(1.3)' }}
          />
        </div>
      </div>

      {/* ─── Texte ───────────────────────────────────────────────────────── */}
      <div className="text-center mb-3">
        <p className="text-[10px] font-bold tracking-widest uppercase text-emerald-500 mb-1">
          Étape {stepIndex + 1}
        </p>
        <h2 className="text-lg font-bold text-slate-900 leading-tight mb-1 font-heading">
          {data.title}
        </h2>
        <p className="text-xs font-medium text-slate-500">{data.subtitle}</p>
      </div>

      <p className="text-slate-600 text-center leading-relaxed mb-4 text-xs">
        {data.description}
      </p>

      {/* ─── Highlights ──────────────────────────────────────────────────── */}
      {data.highlights && data.highlights.length > 0 && (
        <div className="space-y-1.5 stagger-children">
          {data.highlights.map((h, i) => (
            <div
              key={i}
              className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-50 border border-slate-100 hover:border-emerald-200 hover:bg-emerald-50/40 transition-all duration-200"
            >
              <span className="text-base flex-shrink-0 mt-0.5">{h.icon}</span>
              <div>
                <p className="text-[11px] font-bold text-slate-700">{h.label}</p>
                <p className="text-[11px] text-slate-500 leading-snug">{h.detail}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
