/**
 * SEINENTAI4US — Axios instance & interceptors
 */
import axios from 'axios';
import { API_BASE_URL, AUTH_TOKEN_KEY } from '@/lib/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request Interceptor: Attach JWT ─────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor: Handle errors globally ────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;

      // 401: Token expired or invalid → redirect to login
      if (status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem(AUTH_TOKEN_KEY);
          // Only redirect if not already on login page
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
        }
      }

      // Format error message
      const message =
        data?.detail ||
        data?.message ||
        (typeof data === 'string' ? data : `Erreur ${status}`);

      return Promise.reject(new Error(message));
    }

    if (error.request) {
      return Promise.reject(new Error('Serveur inaccessible. Vérifiez votre connexion.'));
    }

    return Promise.reject(error);
  }
);

export default api;

/**
 * SSE streaming helper using fetch (for POST SSE endpoints).
 * Axios doesn't support streaming natively, so we use fetch + ReadableStream.
 */
export async function fetchSSE(
  endpoint: string,
  body: Record<string, unknown>,
  onEvent: (event: Record<string, unknown>) => void,
  onError?: (error: Error) => void,
  signal?: AbortSignal
): Promise<void> {
  const token = typeof window !== 'undefined' ? localStorage.getItem(AUTH_TOKEN_KEY) : null;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const text = await response.text();
    let msg: string;
    try {
      const j = JSON.parse(text);
      msg = j.detail || j.message || `Erreur ${response.status}`;
    } catch {
      msg = text || `Erreur ${response.status}`;
    }
    throw new Error(msg);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('ReadableStream non supporté');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;

        const jsonStr = trimmed.slice(6);
        if (jsonStr === '[DONE]') return;

        try {
          const event = JSON.parse(jsonStr);
          onEvent(event);
        } catch {
          // Skip malformed JSON
        }
      }
    }
  } catch (err) {
    if ((err as Error).name === 'AbortError') return;
    onError?.(err as Error);
    throw err;
  }
}
