/**
 * SEINENTAI4US — useTutorial hook
 *
 * Encapsule toute la logique de décision et les trois handlers métier :
 *  - shouldShowTutorial() → bool
 *  - handleFinish()       → state = "seen"    + ferme
 *  - handleDefer()        → state = "seen"    + ferme (réaffichage connexion suivante)
 *  - handleDismiss()      → state = "dismissed" + ferme définitivement (auto)
 *  - handleOpenManual()   → ouvre sans changer l'état
 */
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  openTutorial,
  closeTutorial,
} from '@/store/slices/tutorialSlice';
import { updateTutorialState } from '@/store/slices/authSlice';
import { authApi } from '@/api/auth';

export function useTutorial() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);
  const { isOpen, currentStep, isManual } = useAppSelector((s) => s.tutorial);

  // ─── Logique de décision ──────────────────────────────────────────────────
  /**
   * Retourne true si le tutoriel doit s'afficher automatiquement.
   *
   * Règles :
   *   login_count === 1  AND tutorial_state === "never_seen"  → premiere connexion
   *   tutorial_state === "seen"                                → reporter
   *   tutorial_state === "dismissed"                           → jamais (auto)
   */
  const shouldShowTutorial = useCallback((): boolean => {
    if (!user) return false;
    if (user.tutorial_state === 'dismissed') return false;
    if (user.tutorial_state === 'never_seen') return true;
    if (user.tutorial_state === 'seen') return true;
    return false;
  }, [user]);

  // ─── Handlers ─────────────────────────────────────────────────────────────

  /** Terminer le tutoriel → état "seen" (réaffichage possible à la prochaine connexion) */
  const handleFinish = useCallback(async () => {
    dispatch(closeTutorial());
    dispatch(updateTutorialState('seen'));
    try {
      await authApi.updateTutorialState('seen');
    } catch {
      // L'état local est déjà mis à jour, l'erreur réseau n'est pas bloquante
    }
  }, [dispatch]);

  /**
   * "Revoir plus tard" → état "seen"
   * Le tutoriel se réaffichera automatiquement à la prochaine connexion.
   */
  const handleDefer = useCallback(async () => {
    dispatch(closeTutorial());
    dispatch(updateTutorialState('seen'));
    try {
      await authApi.updateTutorialState('seen');
    } catch {
      // silencieux
    }
  }, [dispatch]);

  /**
   * "Ne plus afficher" → état "dismissed"
   * Bloque définitivement l'auto-affichage, mais le tutoriel reste accessible
   * manuellement via "Revoir le tutoriel".
   */
  const handleDismiss = useCallback(async () => {
    dispatch(closeTutorial());
    dispatch(updateTutorialState('dismissed'));
    try {
      await authApi.updateTutorialState('dismissed');
    } catch {
      // silencieux
    }
  }, [dispatch]);

  /**
   * Lancement manuel depuis les paramètres / header.
   * N'altère pas l'état du tutoriel — l'utilisateur peut toujours changer d'avis.
   */
  const handleOpenManual = useCallback(() => {
    dispatch(openTutorial({ manual: true }));
  }, [dispatch]);

  /** Ouvrir automatiquement (appelé depuis _app.tsx après fetchMe) */
  const handleOpenAuto = useCallback(() => {
    dispatch(openTutorial({ manual: false }));
  }, [dispatch]);

  return {
    isOpen,
    currentStep,
    isManual,
    shouldShowTutorial,
    handleFinish,
    handleDefer,
    handleDismiss,
    handleOpenManual,
    handleOpenAuto,
  };
}
