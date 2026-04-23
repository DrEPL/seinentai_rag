/**
 * SEINENTAI4US — Auth API
 */
import api from './axios';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
}

export type TutorialState = 'never_seen' | 'seen' | 'dismissed';

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    full_name: string;
    created_at: string;
    is_active: boolean;
    login_count: number;
    tutorial_state: TutorialState;
    last_login_at: string | null;
  };
}

export const authApi = {
  login: (data: LoginPayload) => api.post<TokenResponse>('/auth/login', data),
  register: (data: RegisterPayload) => api.post('/auth/register', data),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
  /** Met à jour l'état du tutoriel d'onboarding */
  updateTutorialState: (state: 'seen' | 'dismissed') =>
    api.patch('/auth/tutorial-state', { state }),
};
