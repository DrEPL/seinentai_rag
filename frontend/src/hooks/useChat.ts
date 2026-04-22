/**
 * SEINENTAI4US — Chat hook with SSE streaming
 */
import { useCallback, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  setSessions,
  addSession,
  setActiveSession,
  setMessages,
  addMessage,
  updateLastMessage,
  appendStreamToken,
  setStreaming,
  setChatLoading,
  setHistoryLoading,
  setSessionsLoading,
  setChatError,
  removeSession,
  replaceSessionId,
  setMessageError,
} from '@/store/slices/chatSlice';
import { addStep, clearSteps, setAgentMode } from '@/store/slices/agentSlice';
import { addToast } from '@/store/slices/uiSlice';
import { chatApi } from '@/api/chat';
import { fetchSSE } from '@/api/axios';
import type { ChatMessage } from '@/store/slices/chatSlice';

export function useChat() {
  const dispatch = useAppDispatch();
  const { sessions, activeSessionId, messages, isStreaming, streamingContent, ragSettings, loading, historyLoading, sessionsLoading } =
    useAppSelector((s) => s.chat);
  const abortRef = useRef<AbortController | null>(null);

  const currentMessages = activeSessionId ? messages[activeSessionId] || [] : [];

  // ─── Load sessions ─────────────────────────────────────────────────────
  const loadSessions = useCallback(async () => {
    dispatch(setSessionsLoading(true));
    try {
      const res = await chatApi.getHistory();
      dispatch(setSessions(res.data.sessions || []));
    } catch (err) {
      dispatch(addToast({ type: 'error', message: 'Erreur chargement historique' }));
    }
  }, [dispatch]);

  // ─── Load session messages ─────────────────────────────────────────────
  const loadSession = useCallback(
    async (sessionId: string) => {
      dispatch(setActiveSession(sessionId));
      if (messages[sessionId]?.length) return;
      dispatch(setHistoryLoading(true));
      try {
        const res = await chatApi.getSession(sessionId);
        const msgs: ChatMessage[] = (res.data.messages || []).map(
          (m: Record<string, unknown>, i: number) => ({
            id: `${sessionId}-${i}`,
            role: m.role as string,
            content: m.content as string,
            timestamp: m.timestamp as string,
            sources: m.sources as ChatMessage['sources'],
            metadata: m.metadata as Record<string, unknown>,
          })
        );
        dispatch(setMessages({ sessionId, messages: msgs }));
      } catch (err) {
        dispatch(addToast({ type: 'error', message: 'Erreur chargement conversation' }));
      } finally {
        dispatch(setHistoryLoading(false));
      }
    },
    [dispatch, messages]
  );

  // ─── Send message (streaming SSE) ─────────────────────────────────────
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isStreaming) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      };

      // Clear agent steps
      dispatch(clearSteps());

      const isNewChat = !activeSessionId;
      const endpoint = isNewChat ? '/chat/new' : `/chat/${activeSessionId}`;
      const body: Record<string, unknown> = {
        message: text,
        stream: ragSettings.stream,
        use_agent: ragSettings.use_agent,
        use_hybrid: ragSettings.use_hybrid,
        use_hyde: ragSettings.use_hyde,
        temperature: ragSettings.temperature,
        search_limit: ragSettings.search_limit,
      };

      if (!isNewChat) {
        body.session_id = activeSessionId;
      }

      // Generate temp ID for optimistic updates
      let currentSessionId = activeSessionId || `temp-${Date.now()}`;

      // Create optimistic session if new
      if (isNewChat) {
        dispatch(
          addSession({
            session_id: currentSessionId,
            title: text.slice(0, 80),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            message_count: 0,
          })
        );
        dispatch(setActiveSession(currentSessionId));
      }

      // Add user message optimistically
      dispatch(addMessage({ sessionId: currentSessionId, message: userMsg }));

      // Create placeholder assistant message
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage({ sessionId: currentSessionId, message: assistantMsg }));

      // If streaming
      if (ragSettings.stream) {
        dispatch(setStreaming(true));

        let fullContent = '';

        const abortController = new AbortController();
        abortRef.current = abortController;

        try {
          await fetchSSE(
            endpoint,
            body,
            (event) => {
              const type = event.type as string;

              switch (type) {
                case 'start': {
                  const sid = event.session_id as string;
                  const mode = (event.mode as string) || 'static';
                  dispatch(setAgentMode(mode as 'agent' | 'static'));

                  if (isNewChat && sid && sid !== currentSessionId) {
                    dispatch(replaceSessionId({ oldId: currentSessionId, newId: sid }));
                    currentSessionId = sid;
                  }
                  break;
                }
                case 'thought':
                  dispatch(
                    addStep({
                      type: 'thought',
                      node: event.node as string,
                      content: event.content as string,
                      timestamp: (event.timestamp as string) || new Date().toISOString(),
                    })
                  );
                  break;
                case 'tool_call':
                  dispatch(
                    addStep({
                      type: 'tool_call',
                      tool: event.tool as string,
                      params: event.params as Record<string, unknown>,
                      result_preview: event.result_preview as string,
                      timestamp: (event.timestamp as string) || new Date().toISOString(),
                    })
                  );
                  break;
                case 'observation':
                  dispatch(
                    addStep({
                      type: 'observation',
                      content: event.content as string,
                      score: event.score as number,
                      sufficient: event.sufficient as boolean,
                      feedback: event.feedback as string,
                      timestamp: (event.timestamp as string) || new Date().toISOString(),
                    })
                  );
                  break;
                case 'synthesis_start':
                  dispatch(
                    addStep({
                      type: 'synthesis_start',
                      content: 'Génération de la réponse...',
                      timestamp: new Date().toISOString(),
                    })
                  );
                  break;
                case 'token': {
                  const token = event.token as string;
                  fullContent += token;
                  dispatch(appendStreamToken(token));
                  dispatch(
                    updateLastMessage({
                      sessionId: currentSessionId,
                      content: fullContent,
                    })
                  );
                  break;
                }
                case 'done': {
                  const sources = event.sources as ChatMessage['sources'];
                  if (sources) {
                    dispatch(
                      updateLastMessage({
                        sessionId: currentSessionId,
                        content: fullContent,
                        sources,
                      })
                    );
                  }
                  dispatch(clearSteps());
                  break;
                }
                case 'error':
                  dispatch(addToast({ type: 'error', message: (event.message as string) || 'Erreur streaming' }));
                  break;
              }
            },
            (error) => {
              dispatch(addToast({ type: 'error', message: error.message }));
            },
            abortController.signal
          );
        } catch (err) {
          if ((err as Error).name !== 'AbortError') {
            dispatch(addToast({ type: 'error', message: (err as Error).message }));
          }
        } finally {
          dispatch(setStreaming(false));
          abortRef.current = null;
        }
      } else {
        // Non-streaming mode
        dispatch(setChatLoading(true));

        try {
          const requestBody = isNewChat ? { ...body, session_id: undefined } : body;
          const res = isNewChat
            ? await chatApi.newChat(requestBody as any)
            : await chatApi.continueChat(activeSessionId!, requestBody as any);

          const data = res.data;
          const sid = data.session_id;

          if (isNewChat && sid && sid !== currentSessionId) {
            dispatch(replaceSessionId({ oldId: currentSessionId, newId: sid }));
            currentSessionId = sid;
          }

          dispatch(
            updateLastMessage({
              sessionId: currentSessionId,
              content: data.response,
              sources: data.sources,
            })
          );
        } catch (err) {
          dispatch(addToast({ type: 'error', message: (err as Error).message }));
          dispatch(setMessageError({ 
            sessionId: currentSessionId, 
            messageId: userMsg.id, 
            error: true 
          }));
          dispatch(
            updateLastMessage({
              sessionId: currentSessionId,
              content: "❌ Une erreur s'est produite lors de la génération de la réponse.",
            })
          );
        } finally {
          dispatch(setChatLoading(false));
        }
      }
    },
    [dispatch, activeSessionId, isStreaming, ragSettings]
  );

  // ─── Stop streaming ───────────────────────────────────────────────────
  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    dispatch(setStreaming(false));
  }, [dispatch]);

  // ─── New conversation ─────────────────────────────────────────────────
  const newConversation = useCallback(() => {
    dispatch(setActiveSession(null));
    dispatch(clearSteps());
  }, [dispatch]);

  // ─── Delete session ───────────────────────────────────────────────────
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await chatApi.deleteSession(sessionId);
      dispatch(removeSession(sessionId));
      dispatch(addToast({ type: 'success', message: 'Session supprimée' }));
      
      if (activeSessionId === sessionId) {
        newConversation();
      }
    } catch (err) {
      dispatch(addToast({ type: 'error', message: 'Erreur suppression session' }));
    }
  }, [dispatch, activeSessionId, newConversation]);

  return {
    sessions,
    activeSessionId,
    currentMessages,
    isStreaming,
    streamingContent,
    ragSettings,
    loading,
    historyLoading,
    sessionsLoading,
    loadSessions,
    loadSession,
    sendMessage,
    stopStreaming,
    newConversation,
    deleteSession,
  };
}
