/**
 * SEINENTAI4US — OnboardingTutorial
 * Guided tour contextuel avec spotlight et tooltip ancrees sur l'UI.
 */
import { useEffect, useCallback, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ChevronLeft, ChevronRight, X, Check, Loader2, Sparkles } from 'lucide-react';
import { useTutorial } from '@/hooks/useTutorial';
import { useAppDispatch } from '@/store/hooks';
import { nextStep, prevStep, setStep } from '@/store/slices/tutorialSlice';

type StepPosition = 'top' | 'bottom' | 'left' | 'right';

interface TourStep {
  id: string;
  title: string;
  subtitle: string;
  target: string;
  mobileTarget?: string;
  content: string;
  details: string[];
  position: StepPosition;
}

const STEPS: TourStep[] = [
  {
    id: 'welcome',
    title: 'Bienvenue sur SEINENTAI4US',
    subtitle: "Présentation rapide de l'app",
    target: '#tour-app-header',
    mobileTarget: '#tour-app-header',
    content:
      "Cette application t'accompagne pour explorer rapidement les contenus, poser des questions naturelles et obtenir des réponses fiables avec contexte.",
    details: [
      'Interface conçue pour une prise en main immédiate.',
      'Chaque étape de ce guide te montre exactement où agir.',
      'Tu peux quitter et relancer le tutoriel à tout moment.',
    ],
    position: 'bottom',
  },
  {
    id: 'main_function',
    title: 'Fonction principale',
    subtitle: 'Comprendre le rôle du système',
    target: '#tour-chat-main',
    mobileTarget: '#tour-chat-main',
    content:
      'Le cœur de la plateforme est un chat intelligent basé sur vos documents : il recherche, croise les passages pertinents et formule une réponse exploitable.',
    details: [
      'Tu poses une question métier en langage naturel.',
      'Le système retrouve les meilleurs extraits puis produit une synthèse.',
      "L'objectif : gagner du temps sans perdre la qualité des références.",
    ],
    position: 'right',
  },
  {
    id: 'interaction',
    title: 'Interaction',
    subtitle: 'Comment poser une question',
    target: '#tour-chat-input',
    mobileTarget: '#tour-chat-input',
    content:
      'Écris ta question dans la zone de saisie, puis envoie. Utilise des formulations précises pour obtenir des réponses plus utiles et plus ciblées.',
    details: [
      'Entrée pour envoyer, Shift + Entrée pour aller à la ligne.',
      'Tu peux poser des questions de suivi dans la même conversation.',
      'Plus la question est claire, plus la réponse sera actionnable.',
    ],
    position: 'top',
  },
  {
    id: 'advanced_options',
    title: 'Options avancées',
    subtitle: 'Réglages expert du moteur',
    target: '#tour-rag-options-trigger',
    mobileTarget: '#tour-rag-options-trigger',
    content:
      "Ces options permettent d'ajuster le comportement de l'assistant selon ton besoin de vitesse, de profondeur et de couverture documentaire.",
    details: [
      'Mode réflexion approfondie : raisonnement plus poussé pour les cas complexes.',
      'Streaming : affiche la réponse en temps réel token par token.',
      'HyDE : génère une hypothèse intermédiaire pour enrichir la recherche.',
      'Recherche hybride : combine sémantique + lexicale pour mieux couvrir les documents.',
      'Température : faible = stable/factuel, élevée = plus créatif.',
      'Résultats : nombre de documents récupérés avant génération finale.',
    ],
    position: 'bottom',
  },
  {
    id: 'history_sidebar',
    title: 'Historique',
    subtitle: 'Retrouver les conversations',
    target: '#tour-sidebar-history',
    mobileTarget: '#tour-sidebar-toggle',
    content:
      "L'historique te permet de reprendre une discussion, comparer les réponses précédentes et conserver le contexte de travail.",
    details: [
      'Clique une conversation pour reprendre exactement où tu en étais.',
      'Utile pour conserver la trace des décisions et analyses.',
      "En mobile, le menu permet d'accéder rapidement à cet historique.",
    ],
    position: 'right',
  },
  {
    id: 'conclusion',
    title: 'Tu es prêt(e)',
    subtitle: 'Conclusion',
    target: '#tour-chat-input',
    mobileTarget: '#tour-chat-input',
    content:
      'Excellent, tu as les bases pour utiliser la plateforme efficacement. Lance une première question concrète pour démarrer.',
    details: [
      'Commence simple, puis affine avec les options avancées.',
      "Appuie-toi sur l'historique pour capitaliser sur tes échanges.",
      'Ce guide reste disponible via "Revoir le tutoriel".',
    ],
    position: 'top',
  },
];

const TOTAL = STEPS.length;
const PADDING = 10;
const GAP = 14;
const TOOLTIP_WIDTH = 320;
const TOOLTIP_HEIGHT_ESTIMATE = 220;
const TARGET_WAIT_MS = 4000;

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

export default function OnboardingTutorial() {
  const dispatch = useAppDispatch();
  const { isOpen, currentStep, isManual, handleFinish, handleDefer, handleDismiss } = useTutorial();
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  const [manualOpenFallback, setManualOpenFallback] = useState(false);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [targetRadius, setTargetRadius] = useState('12px');
  const [isWaitingTarget, setIsWaitingTarget] = useState(false);
  const [targetMissing, setTargetMissing] = useState(false);
  const [tooltipHeight, setTooltipHeight] = useState(TOOLTIP_HEIGHT_ESTIMATE);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const effectiveIsOpen = isOpen || manualOpenFallback;

  const isFirst = currentStep === 0;
  const isLast = currentStep === TOTAL - 1;
  const step = STEPS[currentStep];
  const resolveTargetSelector = useCallback((s: TourStep) => {
    if (typeof window === 'undefined') return s.target;
    if (window.innerWidth < 768 && s.mobileTarget) return s.mobileTarget;
    return s.target;
  }, []);
  const activeTargetSelector = resolveTargetSelector(step);

  const measureTarget = useCallback(() => {
    const el = document.querySelector(activeTargetSelector) as HTMLElement | null;
    if (!el) {
      setTargetRect(null);
      return false;
    }

    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') {
      setTargetRect(null);
      return false;
    }

    const rect = el.getBoundingClientRect();
    if (rect.width < 4 || rect.height < 4) {
      setTargetRect(null);
      return false;
    }

    setTargetRect(rect);
    setTargetRadius(style.borderRadius || '12px');
    return true;
  }, [activeTargetSelector]);

  useEffect(() => {
    if (!effectiveIsOpen) return;
    let rafId = 0;
    const startedAt = Date.now();

    const tick = () => {
      const found = measureTarget();
      if (found) {
        setIsWaitingTarget(false);
        setTargetMissing(false);
      } else if (Date.now() - startedAt > TARGET_WAIT_MS) {
        setIsWaitingTarget(false);
        setTargetMissing(true);
      } else {
        setIsWaitingTarget(true);
      }

      // Keep tracking rect continuously (mobile viewport/toolbars/layout shifts)
      rafId = window.requestAnimationFrame(tick);
    };

    rafId = window.requestAnimationFrame(tick);
    return () => {
      if (rafId) window.cancelAnimationFrame(rafId);
    };
  }, [effectiveIsOpen, step.id, measureTarget]);

  useEffect(() => {
    if (!effectiveIsOpen) return;
    const onResize = () => measureTarget();
    const onScroll = () => measureTarget();
    const onViewport = () => measureTarget();
    window.addEventListener('resize', onResize);
    window.addEventListener('scroll', onScroll, true);
    window.visualViewport?.addEventListener('resize', onViewport);
    window.visualViewport?.addEventListener('scroll', onViewport);
    return () => {
      window.removeEventListener('resize', onResize);
      window.removeEventListener('scroll', onScroll, true);
      window.visualViewport?.removeEventListener('resize', onViewport);
      window.visualViewport?.removeEventListener('scroll', onViewport);
    };
  }, [effectiveIsOpen, measureTarget]);

  useEffect(() => {
    const syncViewport = () => setIsMobileViewport(window.innerWidth < 768);
    syncViewport();
    window.addEventListener('resize', syncViewport);
    return () => window.removeEventListener('resize', syncViewport);
  }, []);

  const handleEsc = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setManualOpenFallback(false);
        handleDefer();
      }
    },
    [effectiveIsOpen, handleDefer]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [handleEsc]);

  useEffect(() => {
    if (!effectiveIsOpen) return;
    const node = tooltipRef.current;
    if (!node) return;

    const measure = () => {
      const rect = node.getBoundingClientRect();
      if (rect.height > 0) setTooltipHeight(Math.ceil(rect.height));
    };

    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    return () => observer.disconnect();
  }, [effectiveIsOpen, currentStep, isWaitingTarget, targetMissing]);

  useEffect(() => {
    const onManualOpen = () => {
      dispatch(setStep(0));
      setManualOpenFallback(true);
    };
    window.addEventListener('seinentai:tutorial-open-manual', onManualOpen);
    return () => window.removeEventListener('seinentai:tutorial-open-manual', onManualOpen);
  }, [dispatch]);

  const tooltipStyle = useMemo(() => {
    if (!targetRect) {
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      } as const;
    }

    const viewportW = window.innerWidth;
    const viewportH = window.innerHeight;
    const isMobile = viewportW < 768;
    const preferPos = isMobile ? 'bottom' : step.position;
    const maxLeft = viewportW - TOOLTIP_WIDTH - PADDING;
    const centeredLeft = clamp(targetRect.left + targetRect.width / 2 - TOOLTIP_WIDTH / 2, PADDING, maxLeft);

    if (preferPos === 'top') {
      const topCandidate = targetRect.top - GAP - tooltipHeight;
      const bottomCandidate = targetRect.bottom + GAP;
      if (topCandidate >= PADDING) {
        return { top: topCandidate, left: centeredLeft, transform: 'none' } as const;
      }
      if (bottomCandidate + tooltipHeight <= viewportH - PADDING) {
        return { top: bottomCandidate, left: centeredLeft, transform: 'none' } as const;
      }
      return {
        top: clamp(bottomCandidate, PADDING, viewportH - tooltipHeight - PADDING),
        left: centeredLeft,
        transform: 'none',
      } as const;
    }

    if (preferPos === 'left') {
      const leftCandidate = targetRect.left - GAP - TOOLTIP_WIDTH;
      const rightCandidate = targetRect.right + GAP;
      if (leftCandidate >= PADDING) {
        return {
          top: clamp(targetRect.top + targetRect.height / 2 - tooltipHeight / 2, PADDING, viewportH - tooltipHeight - PADDING),
          left: leftCandidate,
          transform: 'none',
        } as const;
      }
      if (rightCandidate + TOOLTIP_WIDTH <= viewportW - PADDING) {
        return {
          top: clamp(targetRect.top + targetRect.height / 2 - tooltipHeight / 2, PADDING, viewportH - tooltipHeight - PADDING),
          left: rightCandidate,
          transform: 'none',
        } as const;
      }
      return {
        top: clamp(targetRect.bottom + GAP, PADDING, viewportH - tooltipHeight - PADDING),
        left: centeredLeft,
        transform: 'none',
      } as const;
    }

    if (preferPos === 'right') {
      const rightCandidate = targetRect.right + GAP;
      const leftCandidate = targetRect.left - GAP - TOOLTIP_WIDTH;
      if (rightCandidate + TOOLTIP_WIDTH <= viewportW - PADDING) {
        return {
          top: clamp(targetRect.top + targetRect.height / 2 - tooltipHeight / 2, PADDING, viewportH - tooltipHeight - PADDING),
          left: rightCandidate,
          transform: 'none',
        } as const;
      }
      if (leftCandidate >= PADDING) {
        return {
          top: clamp(targetRect.top + targetRect.height / 2 - tooltipHeight / 2, PADDING, viewportH - tooltipHeight - PADDING),
          left: leftCandidate,
          transform: 'none',
        } as const;
      }
      return {
        top: clamp(targetRect.bottom + GAP, PADDING, viewportH - tooltipHeight - PADDING),
        left: centeredLeft,
        transform: 'none',
      } as const;
    }

    const belowTop = targetRect.bottom + GAP;
    const aboveTop = targetRect.top - GAP - tooltipHeight;
    if (belowTop + tooltipHeight <= viewportH - PADDING) {
      return { top: belowTop, left: centeredLeft, transform: 'none' } as const;
    }
    if (aboveTop >= PADDING) {
      return { top: aboveTop, left: centeredLeft, transform: 'none' } as const;
    }
    return {
      top: clamp(belowTop, PADDING, viewportH - tooltipHeight - PADDING),
      left: centeredLeft,
      transform: 'none',
    } as const;
  }, [targetRect, step.position, tooltipHeight]);

  if (!effectiveIsOpen || typeof window === 'undefined') return null;

  const spotlightStyle =
    targetRect && !targetMissing
      ? {
          top: `${Math.max(0, targetRect.top)}px`,
          left: `${Math.max(0, targetRect.left)}px`,
          width: `${targetRect.width}px`,
          height: `${targetRect.height}px`,
          borderRadius: targetRadius,
        }
      : undefined;

  const portal = (
    <div className="fixed inset-0 z-[10000] pointer-events-auto" role="dialog" aria-modal="true" aria-label="Tutoriel guide">
      {spotlightStyle && (
        <>
          <div
            className="fixed pointer-events-none border-2 border-emerald-500/95 shadow-[0_0_0_9999px_rgba(2,6,23,0.66)] transition-all duration-200 ease-out"
            style={spotlightStyle}
          />
          <div
            className="fixed pointer-events-none border-2 border-emerald-400/50 animate-pulse"
            style={spotlightStyle}
          />
        </>
      )}

      <div
        ref={tooltipRef}
        className="fixed z-[10001] w-[min(380px,calc(100vw-20px))] rounded-2xl border border-slate-200/90 bg-linear-to-b from-white/99 to-slate-50/98 p-3.5 shadow-[0_24px_46px_-14px_rgba(15,23,42,0.4),0_2px_8px_rgba(15,23,42,0.06),inset_0_1px_0_rgba(255,255,255,0.8)] transition-[top,left,transform] duration-220 ease-out max-md:w-[min(380px,calc(100vw-16px))] max-md:max-h-[calc(100dvh-24px)] max-md:overflow-y-auto"
        style={tooltipStyle}
      >
        <div className="mb-2.5">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-[11px] uppercase tracking-widest text-emerald-500 font-bold">
                Etape {currentStep + 1} / {TOTAL}
              </p>
              <h3 className="text-base font-bold text-slate-900">{step.title}</h3>
              <p className="text-[12px] text-slate-500 mt-0.5">{step.subtitle}</p>
            </div>
            <button
              onClick={() => {
                setManualOpenFallback(false);
                handleDefer();
              }}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
              aria-label="Quitter le tutoriel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-teal-700">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Guide interactif contextuel</span>
          </div>
        </div>

        {isWaitingTarget ? (
          <p className="text-xs text-slate-500 flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Recherche de l&apos;élément cible...
          </p>
        ) : (
          <>
            <p className="text-sm text-slate-600 leading-relaxed">{step.content}</p>
            <ul className="mt-2.5 grid list-none gap-1.5 p-0">
              {(isMobileViewport ? step.details.slice(0, 2) : step.details).map((detail) => (
                <li
                  key={detail}
                  className="rounded-[10px] border border-slate-200 bg-white px-2.5 py-2 text-xs leading-[1.4] text-slate-600"
                >
                  {detail}
                </li>
              ))}
            </ul>
          </>
        )}

        {targetMissing && (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-2">
            <p className="text-[11px] text-amber-700">
              Élément non détecté sur cet écran. Vous pouvez passer cette étape.
            </p>
          </div>
        )}

        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full bg-linear-to-r from-emerald-500 to-teal-500 transition-[width] duration-260 ease-out"
            style={{ width: `${((currentStep + 1) / TOTAL) * 100}%` }}
          />
        </div>

        <div className="mt-4 flex items-center justify-between gap-2">
          <button
            onClick={() => dispatch(prevStep())}
            disabled={isFirst}
            className="inline-flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-semibold text-slate-500 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Précédent
          </button>

          <button
            onClick={() => {
              if (isLast) {
                setManualOpenFallback(false);
                handleFinish();
              }
              else dispatch(nextStep());
            }}
            className="inline-flex items-center gap-1 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 transition-all cursor-pointer"
          >
            {isLast ? 'Terminer' : 'Suivant'}
            {isLast ? <Check className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </button>
        </div>

        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
          <button
            onClick={handleDefer}
            onClickCapture={() => setManualOpenFallback(false)}
            className="inline-flex min-h-7 cursor-pointer items-center justify-center gap-1.5 rounded-[9px] border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-[11px] font-bold tracking-[0.01em] text-slate-600 transition-all duration-150 hover:-translate-y-px hover:border-slate-300 hover:bg-slate-100 hover:text-slate-700 active:translate-y-0 max-md:min-h-[30px] max-md:px-2 max-md:text-[10.5px]"
          >
            Quitter
          </button>
          {!isManual && (
            <button
              onClick={handleDismiss}
              onClickCapture={() => setManualOpenFallback(false)}
              className="inline-flex min-h-7 cursor-pointer items-center justify-center gap-1.5 rounded-[9px] border border-rose-200 bg-linear-to-b from-rose-50 to-rose-100 px-2.5 py-1.5 text-[11px] font-bold tracking-[0.01em] text-rose-700 transition-all duration-150 hover:-translate-y-px hover:border-rose-300 hover:from-rose-100 hover:to-rose-200 hover:text-rose-800 active:translate-y-0 max-md:min-h-[30px] max-md:px-2 max-md:text-[10.5px]"
            >
              Ne plus afficher
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(portal, document.body);
}
