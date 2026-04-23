/**
 * SEINENTAI4US — OnboardingTutorial
 * Guided tour contextuel avec spotlight et tooltip ancrees sur l'UI.
 */
import { useEffect, useCallback, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ChevronLeft, ChevronRight, X, Check, Loader2, Sparkles, MessageCircle, BookOpen, Eye, FileText, ArrowUpCircle, CornerDownLeft, Target, BrainCircuit, Activity, RefreshCw, Search, SlidersHorizontal, MousePointerClick, Menu, Lightbulb, Play, MessageSquarePlus, Hand, Settings, Rocket, LucideIcon } from 'lucide-react';
import confetti from 'canvas-confetti';
import { useTutorial } from '@/hooks/useTutorial';
import { useAppDispatch } from '@/store/hooks';
import { nextStep, prevStep, setStep } from '@/store/slices/tutorialSlice';

type StepPosition = 'top' | 'bottom' | 'left' | 'right';

interface TourDetail {
  icon: LucideIcon;
  text: string;
}

interface TourStep {
  id: string;
  title: string;
  titleIcon?: LucideIcon;
  subtitle: string;
  target: string;
  mobileTarget?: string;
  content: string;
  details: TourDetail[];
  position: StepPosition;
}

const STEPS: TourStep[] = [
  {
    id: 'welcome',
    title: 'Bienvenue sur SEINENTAI4US',
    titleIcon: Hand,
    subtitle: "Je suis Sunao, votre assistant IA basé sur les enseignements de Sukyo Mahikari.",
    target: '#tour-app-header',
    mobileTarget: '#tour-app-header',
    content: "Posez vos questions et je vous fournirai les réponses basées sur les enseignements de Sukyo Mahikari.",
    details: [
      { icon: MessageCircle, text: 'Dialoguez naturellement avec moi comme vous le feriez avec un ami' },
      { icon: BookOpen, text: 'Réponses basées sur les enseignements de Sukyo Mahikari' },
    ],
    position: 'bottom',
  },
  {
    id: 'main_function',
    title: 'Votre espace de travail',
    subtitle: 'La zone de discussion',
    target: '#tour-chat-main',
    mobileTarget: '#tour-chat-main',
    content: "C'est ici que nos échanges s'affichent. L'interface est conçue pour être claire et lisible, vous permettant de vous concentrer sur l'essentiel.",
    details: [
      { icon: Eye, text: 'Suivez le fil de la réflexion' },
      { icon: FileText, text: 'Consultez les sources utilisées' },
    ],
    position: 'right',
  },
  {
    id: 'interaction',
    title: 'Posez votre question',
    subtitle: 'La barre de saisie',
    target: '#tour-chat-input',
    mobileTarget: '#tour-chat-input',
    content: "Utilisez cet espace pour m'interroger. Je peux résumer un long document, extraire des données précises ou rédiger une synthèse.",
    details: [
      { icon: ArrowUpCircle, text: 'Appuyez sur ⇧ (Shift) + ⏎ (Entrée) pour aller à la ligne' },
      { icon: CornerDownLeft, text: 'Appuyez sur ⏎ (Entrée) pour envoyer' },
      { icon: Target, text: 'Plus votre question est précise, plus ma réponse sera pertinente' },
    ],
    position: 'top',
  },
  {
    id: 'advanced_options',
    title: 'Mode Expert',
    titleIcon: Settings,
    subtitle: 'Ajustez les paramètres',
    target: '#tour-rag-options-trigger',
    mobileTarget: '#tour-rag-options-trigger',
    content: "Un clic ici vous ouvre des options avancées pour affiner mes recherches et adapter mes réponses à vos exigences.",
    details: [
      { icon: BrainCircuit, text: 'Mode Réflexion (précision maximale), mais plus lent.' },
      { icon: Activity, text: 'Mode Streaming: voir la réponse se construire mot après mot.' },
      { icon: RefreshCw, text: 'Mode HyDE : reformule votre question pour améliorer la pertinence.' },
      { icon: Search, text: 'Recherche Hybride (exhaustivité)' },
      { icon: SlidersHorizontal, text: 'Température : niveau de créativité de la réponse (plus bas = plus prévisible)' }
    ],
    position: 'bottom',
  },
  {
    id: 'history_sidebar',
    title: 'Retrouvez tout',
    subtitle: 'Historique des échanges',
    target: '#tour-sidebar-history',
    mobileTarget: '#tour-sidebar-toggle',
    content: "Ne perdez jamais une information. Toutes vos précédentes recherches sont sauvegardées et classées ici.",
    details: [
      { icon: MousePointerClick, text: 'Cliquez sur une conversation pour la rouvrir' },
      { icon: Menu, text: 'Sur mobile, utilisez le menu' },
    ],
    position: 'right',
  },
  {
    id: 'conclusion',
    title: 'À vous de jouer !',
    titleIcon: Rocket,
    subtitle: 'Le tour est terminé',
    target: '#tour-chat-input',
    mobileTarget: '#tour-chat-input',
    content: "Vous avez les clés en main. Essayez par vous-même avec une première question simple !",
    details: [
      { icon: Lightbulb, text: 'Astuce : Soyez le plus précis possible' },
      { icon: Play, text: 'Commencez simple puis affinez avec les options avancées' },
      { icon: MessageSquarePlus, text: 'Pour débuter, posez une question simple comme "Quel est le sens de la vie ?"' },
    ],
    position: 'top',
  },
];

const TOTAL = STEPS.length;
const PADDING = 16;
const GAP = 16;
const TOOLTIP_WIDTH = 360;
const TOOLTIP_HEIGHT_ESTIMATE = 260;
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
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
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
    [isOpen, handleDefer]
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

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const minSwipeDistance = 50;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && !isLast) {
      dispatch(nextStep());
    } else if (isRightSwipe && !isFirst) {
      dispatch(prevStep());
    }
  };

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
            className="fixed pointer-events-none border-2 border-emerald-500/90 shadow-[0_0_0_9999px_rgba(15,23,42,0.7)] transition-all duration-300 ease-out"
            style={spotlightStyle}
          />
          <div
            className="fixed pointer-events-none border-[3px] border-emerald-400/50 animate-pulse transition-all duration-300 ease-out"
            style={spotlightStyle}
          />
        </>
      )}

      <div
        ref={tooltipRef}
        className="fixed z-[10001] w-[min(400px,calc(100vw-32px))] rounded-[20px] md:rounded-3xl border border-white/60 bg-white/95 backdrop-blur-2xl p-4 sm:p-5 md:p-6 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.2),0_0_20px_rgba(0,0,0,0.05)] transition-[top,left,transform] duration-300 ease-out max-md:max-h-[calc(100dvh-32px)] max-md:overflow-y-auto"
        style={tooltipStyle}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        <div className="mb-3 md:mb-4">
          <div className="flex items-start justify-between gap-2 md:gap-3">
            <div>
              <span className="mb-1.5 md:mb-2 inline-flex items-center gap-1.5 rounded-full border border-emerald-200/60 bg-emerald-50 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-600">
                <Sparkles className="h-3 w-3" />
                Étape {currentStep + 1} sur {TOTAL}
              </span>
              <h3 className="text-lg md:text-xl font-bold text-slate-900 leading-tight flex items-center gap-2">
                {step.title}
                {step.titleIcon && <step.titleIcon className="h-4 w-4 md:h-5 md:w-5 text-emerald-500" />}
              </h3>
              <p className="text-[12px] md:text-sm font-medium text-slate-500 mt-0.5 md:mt-1 leading-snug">
                {step.subtitle}
              </p>
            </div>
            <button
              onClick={() => {
                setManualOpenFallback(false);
                handleDefer();
              }}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600 cursor-pointer"
              aria-label="Quitter le tutoriel"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {isWaitingTarget ? (
          <div className="flex flex-col items-center justify-center py-6">
            <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
            <p className="mt-2 text-xs text-slate-500">Recherche en cours...</p>
          </div>
        ) : (
          <>
            <p className="text-[13px] md:text-[14px] leading-snug md:leading-relaxed text-slate-600">
              {step.content}
            </p>
            {step.details.length > 0 && (
              <ul className="mt-3 md:mt-4 grid list-none gap-2 p-0">
                {(isMobileViewport && step.details.length > 2 ? step.details.slice(0, 2) : step.details).map((detail, idx) => (
                  <li key={idx} className="flex items-start gap-2 md:gap-2.5 text-[12px] md:text-[13px] text-slate-600">
                    <detail.icon className="mt-0.5 h-3.5 w-3.5 md:h-4 md:w-4 shrink-0 text-emerald-500" />
                    <span className="leading-snug">{detail.text}</span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}

        {targetMissing && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3">
            <p className="text-[12px] font-medium text-amber-700">
              Élément non détecté sur cet écran. Vous pouvez passer cette étape.
            </p>
          </div>
        )}

        <div className="mt-4 md:mt-6 flex w-full items-center justify-center gap-2.5">
          {Array.from({ length: TOTAL }).map((_, index) => {
            const isActive = index === currentStep;
            const isPast = index < currentStep;
            return (
              <button
                key={index}
                onClick={() => dispatch(setStep(index))}
                className={`h-2 rounded-full transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] cursor-pointer ${
                  isActive 
                    ? 'w-10 bg-gradient-to-r from-emerald-400 to-teal-500 shadow-[0_0_10px_rgba(20,184,166,0.3)]' 
                    : isPast 
                    ? 'w-2.5 bg-emerald-200 hover:bg-emerald-300 hover:w-4' 
                    : 'w-2.5 bg-slate-200 hover:bg-slate-300 hover:w-4'
                }`}
                aria-label={`Aller à l'étape ${index + 1}`}
                aria-current={isActive ? 'step' : undefined}
              />
            );
          })}
        </div>

        <div className="mt-5 md:mt-6 flex items-center justify-between gap-2 md:gap-3">
          <button
            onClick={() => dispatch(prevStep())}
            disabled={isFirst}
            className="inline-flex h-9 md:h-10 items-center justify-center gap-1 md:gap-1.5 rounded-xl px-3 md:px-4 text-[12px] md:text-[13px] font-semibold text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 disabled:pointer-events-none disabled:opacity-40 cursor-pointer"
          >
            <ChevronLeft className="h-4 w-4" />
            <span className="hidden sm:inline">Précédent</span>
          </button>

          <button
            onClick={() => {
              if (isLast) {
                confetti({
                  particleCount: 150,
                  spread: 70,
                  origin: { y: 0.6 },
                  colors: ['#10b981', '#14b8a6', '#0f766e', '#facc15'],
                  zIndex: 10005
                });
                setManualOpenFallback(false);
                handleFinish();
              } else dispatch(nextStep());
            }}
            className="inline-flex h-9 md:h-10 items-center justify-center gap-1 md:gap-1.5 rounded-xl bg-slate-900 px-4 md:px-5 text-[12px] md:text-[13px] font-semibold text-white shadow-md transition-all hover:bg-slate-800 hover:shadow-lg hover:scale-[1.02] cursor-pointer"
          >
            {isLast ? 'Terminer' : 'Suivant'}
            {isLast ? <Check className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </div>

        <div className="mt-3 md:mt-5 flex items-center justify-center gap-3 md:gap-4 border-t border-slate-100 pt-3 md:pt-4">
          <button
            onClick={handleDefer}
            onClickCapture={() => setManualOpenFallback(false)}
            className="text-[12px] font-medium text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
          >
            Passer le tutoriel
          </button>
          {!isManual && (
            <>
              <span className="h-3 w-px bg-slate-200" />
              <button
                onClick={handleDismiss}
                onClickCapture={() => setManualOpenFallback(false)}
                className="text-[12px] font-medium text-slate-400 hover:text-rose-500 transition-colors cursor-pointer"
              >
                Ne plus afficher
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(portal, document.body);
}
