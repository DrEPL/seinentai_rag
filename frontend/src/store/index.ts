/**
 * SEINENTAI4US — Redux Store
 */
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import chatReducer from './slices/chatSlice';
import agentReducer from './slices/agentSlice';
import documentsReducer from './slices/documentsSlice';
import searchReducer from './slices/searchSlice';
import uiReducer from './slices/uiSlice';
import tutorialReducer from './slices/tutorialSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    chat: chatReducer,
    agent: agentReducer,
    documents: documentsReducer,
    search: searchReducer,
    ui: uiReducer,
    tutorial: tutorialReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore date fields in actions
        ignoredActionPaths: ['payload.timestamp', 'payload.created_at', 'payload.updated_at'],
        ignoredPaths: ['chat.sessions', 'chat.messages'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
