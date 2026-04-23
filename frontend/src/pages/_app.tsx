/**
 * SEINENTAI4US — _app.tsx (Redux Provider + Auth Guard + Toasts + Onboarding)
 */
import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { Provider } from 'react-redux';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { store } from '@/store';
import { useAppSelector } from '@/store/hooks';
import { PUBLIC_ROUTES, AUTH_TOKEN_KEY } from '@/lib/constants';
import ToastContainer from '@/components/ui/Toast';
import { useAuth } from '@/hooks/useAuth';
import { useTutorial } from '@/hooks/useTutorial';
import OnboardingTutorial from '@/components/onboarding/OnboardingTutorial';

function TutorialGate() {
  const { isAuthenticated, user } = useAppSelector((s) => s.auth);
  const { shouldShowTutorial, handleOpenAuto, isOpen } = useTutorial();
  const [triggered, setTriggered] = useState(false);

  useEffect(() => {
    // Déclencher une seule fois par session, après que l'utilisateur est chargé
    if (isAuthenticated && user && !triggered && !isOpen) {
      if (shouldShowTutorial()) {
        handleOpenAuto();
      }
      setTriggered(true);
    }
    // Reset si l'utilisateur se déconnecte (pour la prochaine session)
    if (!isAuthenticated) {
      setTriggered(false);
    }
  }, [isAuthenticated, user, triggered, isOpen, shouldShowTutorial, handleOpenAuto]);

  return <OnboardingTutorial />;
}

function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, token } = useAppSelector((s) => s.auth);
  const { fetchMe } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // If we have a token but no user, try to fetch profile
    if (token && !isAuthenticated) {
      fetchMe();
    }
  }, [token, isAuthenticated, fetchMe]);

  useEffect(() => {
    const isPublic = PUBLIC_ROUTES.some((r) => router.pathname.startsWith(r));
    if (mounted && !isPublic && !token) {
      router.replace('/login');
    }
  }, [router, token, mounted]);

  const isPublic = PUBLIC_ROUTES.some((r) => router.pathname.startsWith(r));
  const effectiveToken = mounted ? token : null;

  if (!isPublic && !effectiveToken) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-bg-animated">
        <div className="typing-dots">
          <span /><span /><span />
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <Provider store={store}>
      <AuthGuard>
        <Component {...pageProps} />
      </AuthGuard>
      <ToastContainer />
      <TutorialGate />
    </Provider>
  );
}
