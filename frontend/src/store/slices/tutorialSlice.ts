/**
 * SEINENTAI4US — Tutorial Slice
 * Gère l'état UI du tutoriel d'onboarding (ouvert/fermé, étape courante).
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

interface TutorialUIState {
  isOpen: boolean;
  currentStep: number;  // 0-indexed, 0..5
  isManual: boolean;    // true = lancé manuellement via "Revoir le tutoriel"
}

const initialState: TutorialUIState = {
  isOpen: false,
  currentStep: 0,
  isManual: false,
};

const MAX_TUTORIAL_STEP = 5;

const tutorialSlice = createSlice({
  name: 'tutorial',
  initialState,
  reducers: {
    openTutorial: (state, action: PayloadAction<{ manual?: boolean } | undefined>) => {
      state.isOpen = true;
      state.currentStep = 0;
      state.isManual = action?.payload?.manual ?? false;
    },
    closeTutorial: (state) => {
      state.isOpen = false;
    },
    nextStep: (state) => {
      if (state.currentStep < MAX_TUTORIAL_STEP) {
        state.currentStep += 1;
      }
    },
    prevStep: (state) => {
      if (state.currentStep > 0) {
        state.currentStep -= 1;
      }
    },
    setStep: (state, action: PayloadAction<number>) => {
      const s = action.payload;
      if (s >= 0 && s <= MAX_TUTORIAL_STEP) {
        state.currentStep = s;
      }
    },
  },
});

export const { openTutorial, closeTutorial, nextStep, prevStep, setStep } =
  tutorialSlice.actions;
export default tutorialSlice.reducer;
