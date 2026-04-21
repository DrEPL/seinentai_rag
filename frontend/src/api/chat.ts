/**
 * SEINENTAI4US — Chat API
 */
import api from './axios';

export interface NewChatPayload {
  message: string;
  temperature?: number;
  max_tokens?: number;
  search_limit?: number;
  score_threshold?: number;
  stream?: boolean;
  use_hyde?: boolean;
  use_hybrid?: boolean;
  use_agent?: boolean;
}

export interface ContinueChatPayload {
  session_id: string;
  message: string;
  temperature?: number;
  stream?: boolean;
  use_hyde?: boolean;
  use_hybrid?: boolean;
  use_agent?: boolean;
}

export const chatApi = {
  newChat: (data: NewChatPayload) => api.post('/chat/new', data),
  continueChat: (sessionId: string, data: ContinueChatPayload) =>
    api.post(`/chat/${sessionId}`, data),
  getHistory: () => api.get('/chat/history'),
  getSession: (sessionId: string) => api.get(`/chat/sessions/${sessionId}`),
};
