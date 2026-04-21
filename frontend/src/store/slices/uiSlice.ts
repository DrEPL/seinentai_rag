/**
 * SEINENTAI4US — UI Slice
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import type { InterfaceMode } from '@/lib/constants';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}

interface UIState {
  sidebarOpen: boolean;
  interfaceMode: InterfaceMode;
  toasts: Toast[];
  activeModal: string | null;
  ragSettingsOpen: boolean;
}

const initialState: UIState = {
  sidebarOpen: true,
  interfaceMode: 'user',
  toasts: [],
  activeModal: null,
  ragSettingsOpen: false,
};

let toastCounter = 0;

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    switchInterface: (state, action: PayloadAction<InterfaceMode>) => {
      state.interfaceMode = action.payload;
    },
    addToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      toastCounter++;
      state.toasts.push({
        ...action.payload,
        id: `toast-${toastCounter}`,
      });
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload);
    },
    setActiveModal: (state, action: PayloadAction<string | null>) => {
      state.activeModal = action.payload;
    },
    toggleRagSettings: (state) => {
      state.ragSettingsOpen = !state.ragSettingsOpen;
    },
    setRagSettingsOpen: (state, action: PayloadAction<boolean>) => {
      state.ragSettingsOpen = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  switchInterface,
  addToast,
  removeToast,
  setActiveModal,
  toggleRagSettings,
  setRagSettingsOpen,
} = uiSlice.actions;
export default uiSlice.reducer;
