/**
 * SEINENTAI4US — Auth Slice
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { AUTH_TOKEN_KEY } from '@/lib/constants';
import type { TutorialState } from '@/api/auth';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
  is_active: boolean;
  // ─── Onboarding ──────────────────────────────────────────────────────────
  login_count: number;
  tutorial_state: TutorialState;
  last_login_at: string | null;
}

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: typeof window !== 'undefined' ? localStorage.getItem(AUTH_TOKEN_KEY) : null,
  isAuthenticated: false,
  loading: false,
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<{ user: UserProfile; token: string }>) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.isAuthenticated = true;
      state.error = null;
      state.loading = false;
      if (typeof window !== 'undefined') {
        localStorage.setItem(AUTH_TOKEN_KEY, action.payload.token);
      }
    },
    setUser: (state, action: PayloadAction<UserProfile>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    /** Met à jour localement l'état du tutoriel après un appel API réussi */
    updateTutorialState: (state, action: PayloadAction<TutorialState>) => {
      if (state.user) {
        state.user.tutorial_state = action.payload;
      }
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.error = null;
      if (typeof window !== 'undefined') {
        localStorage.removeItem(AUTH_TOKEN_KEY);
      }
    },
    setAuthLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setAuthError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      if (action.payload) {
        state.loading = false;
      }
    },
  },
});

export const {
  setCredentials,
  setUser,
  updateTutorialState,
  logout,
  setAuthLoading,
  setAuthError,
} = authSlice.actions;
export default authSlice.reducer;
