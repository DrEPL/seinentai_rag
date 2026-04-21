/**
 * SEINENTAI4US — Auth hook
 */
import { useCallback } from 'react';
import { useRouter } from 'next/router';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setCredentials, setUser, logout as logoutAction, setAuthLoading, setAuthError } from '@/store/slices/authSlice';
import { addToast } from '@/store/slices/uiSlice';
import { authApi } from '@/api/auth';
import { ROUTES } from '@/lib/constants';

export function useAuth() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { user, token, isAuthenticated, loading, error } = useAppSelector((s) => s.auth);

  const login = useCallback(
    async (email: string, password: string) => {
      dispatch(setAuthLoading(true));
      console.log("loading ",loading);
      
      dispatch(setAuthError(null));
      try {
        const res = await authApi.login({ email, password });
        const { access_token, user } = res.data;
        dispatch(setCredentials({ user, token: access_token }));
        dispatch(addToast({ type: 'success', message: `Bienvenue, ${user.full_name} !` }));
        router.push(ROUTES.CHAT);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erreur de connexion';
        dispatch(setAuthError(message));
        dispatch(addToast({ type: 'error', message }));
      }
    },
    [dispatch, router]
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      dispatch(setAuthLoading(true));
      dispatch(setAuthError(null));
      try {
        await authApi.register({ email, password, full_name: fullName });
        dispatch(addToast({ type: 'success', message: 'Compte créé ! Connectez-vous.' }));
        router.push(ROUTES.LOGIN);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Erreur d'inscription";
        dispatch(setAuthError(message));
        dispatch(addToast({ type: 'error', message }));
      }
    },
    [dispatch, router]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore errors during logout
    }
    dispatch(logoutAction());
    router.push(ROUTES.LOGIN);
  }, [dispatch, router]);

  const fetchMe = useCallback(async () => {
    if (!token) return;
    try {
      const res = await authApi.getMe();
      dispatch(setUser(res.data));
    } catch {
      dispatch(logoutAction());
    }
  }, [dispatch, token]);

  return { user, token, isAuthenticated, loading, error, login, register, logout, fetchMe };
}
