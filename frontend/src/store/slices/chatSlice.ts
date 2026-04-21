/**
 * SEINENTAI4US — Chat Slice
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { RAG_DEFAULTS, RAG_SETTINGS_KEY } from '@/lib/constants';

// ─── Types ───────────────────────────────────────────────────────────────────
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Array<{
    filename: string;
    score: number;
    chunk_index: number;
    excerpt: string;
  }>;
  metadata?: Record<string, unknown>;
}

export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface RagSettings {
  stream: boolean;
  use_agent: boolean;
  use_hybrid: boolean;
  use_hyde: boolean;
  temperature: number;
  search_limit: number;
}

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: Record<string, ChatMessage[]>; // session_id → messages
  isStreaming: boolean;
  streamingContent: string;
  loading: boolean;
  sessionsLoading: boolean;
  error: string | null;
  ragSettings: RagSettings;
}

// Load RAG settings from localStorage
function loadRagSettings(): RagSettings {
  if (typeof window === 'undefined') return { ...RAG_DEFAULTS };
  try {
    const stored = localStorage.getItem(RAG_SETTINGS_KEY);
    if (stored) return { ...RAG_DEFAULTS, ...JSON.parse(stored) };
  } catch {
    // ignore
  }
  return { ...RAG_DEFAULTS };
}

const initialState: ChatState = {
  sessions: [],
  activeSessionId: null,
  messages: {},
  isStreaming: false,
  streamingContent: '',
  loading: false,
  sessionsLoading: false,
  error: null,
  ragSettings: loadRagSettings(),
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setSessions: (state, action: PayloadAction<ChatSession[]>) => {
      // Sort by updated_at DESC initially
      state.sessions = [...action.payload].sort((a, b) => 
        new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime()
      );
      state.sessionsLoading = false;
    },
    addSession: (state, action: PayloadAction<ChatSession>) => {
      state.sessions.unshift(action.payload);
    },
    setActiveSession: (state, action: PayloadAction<string | null>) => {
      state.activeSessionId = action.payload;
      state.streamingContent = '';
    },
    setMessages: (state, action: PayloadAction<{ sessionId: string; messages: ChatMessage[] }>) => {
      state.messages[action.payload.sessionId] = action.payload.messages;
      state.loading = false;
    },
    addMessage: (state, action: PayloadAction<{ sessionId: string; message: ChatMessage }>) => {
      const { sessionId, message } = action.payload;
      if (!state.messages[sessionId]) {
        state.messages[sessionId] = [];
      }
      state.messages[sessionId].push(message);

      // Move session to top and update timestamp
      const sessionIndex = state.sessions.findIndex(s => s.session_id === sessionId);
      if (sessionIndex !== -1) {
        const session = state.sessions[sessionIndex];
        const updatedSession = { 
          ...session, 
          updated_at: new Date().toISOString(),
          message_count: session.message_count + 1
        };
        state.sessions.splice(sessionIndex, 1);
        state.sessions.unshift(updatedSession);
      }
    },
    updateLastMessage: (state, action: PayloadAction<{ sessionId: string; content: string; sources?: ChatMessage['sources'] }>) => {
      const { sessionId, content, sources } = action.payload;
      const msgs = state.messages[sessionId];
      if (msgs && msgs.length > 0) {
        const last = msgs[msgs.length - 1];
        if (last.role === 'assistant') {
          last.content = content;
          if (sources) last.sources = sources;
        }
      }

      // Move session to top and update timestamp (especially for streaming)
      const sessionIndex = state.sessions.findIndex(s => s.session_id === sessionId);
      if (sessionIndex !== -1) {
        const session = state.sessions[sessionIndex];
        const updatedSession = { 
          ...session, 
          updated_at: new Date().toISOString() 
        };
        state.sessions.splice(sessionIndex, 1);
        state.sessions.unshift(updatedSession);
      }
    },
    appendStreamToken: (state, action: PayloadAction<string>) => {
      state.streamingContent += action.payload;
    },
    setStreaming: (state, action: PayloadAction<boolean>) => {
      state.isStreaming = action.payload;
      if (!action.payload) {
        state.streamingContent = '';
      }
    },
    setChatLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setSessionsLoading: (state, action: PayloadAction<boolean>) => {
      state.sessionsLoading = action.payload;
    },
    setChatError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.loading = false;
    },
    updateRagSettings: (state, action: PayloadAction<Partial<RagSettings>>) => {
      state.ragSettings = { ...state.ragSettings, ...action.payload };
      if (typeof window !== 'undefined') {
        localStorage.setItem(RAG_SETTINGS_KEY, JSON.stringify(state.ragSettings));
      }
    },
    clearChat: (state) => {
      state.activeSessionId = null;
      state.streamingContent = '';
      state.isStreaming = false;
      state.error = null;
    },
  },
});

export const {
  setSessions,
  addSession,
  setActiveSession,
  setMessages,
  addMessage,
  updateLastMessage,
  appendStreamToken,
  setStreaming,
  setChatLoading,
  setSessionsLoading,
  setChatError,
  updateRagSettings,
  clearChat,
} = chatSlice.actions;
export default chatSlice.reducer;
