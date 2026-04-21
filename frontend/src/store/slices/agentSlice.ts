/**
 * SEINENTAI4US — Agent Activity Slice
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export interface AgentStep {
  id: string;
  type: 'thought' | 'tool_call' | 'observation' | 'synthesis_start' | 'error';
  timestamp: string;
  content?: string;
  // thought
  node?: string;
  // tool_call
  tool?: string;
  params?: Record<string, unknown>;
  result_preview?: string;
  // observation
  score?: number;
  sufficient?: boolean;
  feedback?: string;
  // error
  message?: string;
}

interface AgentState {
  steps: AgentStep[];
  isActive: boolean;
  mode: 'agent' | 'static' | null;
}

const initialState: AgentState = {
  steps: [],
  isActive: false,
  mode: null,
};

let stepCounter = 0;

const agentSlice = createSlice({
  name: 'agent',
  initialState,
  reducers: {
    addStep: (state, action: PayloadAction<Omit<AgentStep, 'id'>>) => {
      stepCounter++;
      state.steps.push({
        ...action.payload,
        id: `step-${stepCounter}-${Date.now()}`,
      });
      state.isActive = true;
    },
    clearSteps: (state) => {
      state.steps = [];
      state.isActive = false;
      state.mode = null;
    },
    setAgentActive: (state, action: PayloadAction<boolean>) => {
      state.isActive = action.payload;
    },
    setAgentMode: (state, action: PayloadAction<'agent' | 'static' | null>) => {
      state.mode = action.payload;
    },
  },
});

export const { addStep, clearSteps, setAgentActive, setAgentMode } = agentSlice.actions;
export default agentSlice.reducer;
