/**
 * SEINENTAI4US — _app.tsx (Redux Provider + Auth Guard + Toasts)
 */
import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { Provider } from 'react-redux';
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { store } from '@/store';
import { useAppSelector } from '@/store/hooks';
import { PUBLIC_ROUTES, AUTH_TOKEN_KEY } from '@/lib/constants';
import ToastContainer from '@/components/ui/Toast';
import { useAuth } from '@/hooks/useAuth';

function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, token } = useAppSelector((s) => s.auth);
  const { fetchMe } = useAuth();

  useEffect(() => {
    // If we have a token but no user, try to fetch profile
    if (token && !isAuthenticated) {
      fetchMe();
    }
  }, [token, isAuthenticated, fetchMe]);

  useEffect(() => {
    const isPublic = PUBLIC_ROUTES.some((r) => router.pathname.startsWith(r));
    if (!isPublic && !token) {
      router.replace('/login');
    }
  }, [router, token]);

  // Allow public routes without auth
  const isPublic = PUBLIC_ROUTES.some((r) => router.pathname.startsWith(r));
  if (!isPublic && !token) {
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
    </Provider>
  );
}
