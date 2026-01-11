'use client';

import { createContext, useContext, useState, useCallback } from 'react';
import { WizardStep, WizardContextValue } from './types';

const WizardContext = createContext<WizardContextValue | null>(null);

export function useWizard() {
  const context = useContext(WizardContext);
  if (!context) {
    throw new Error('useWizard must be used within a WizardProvider');
  }
  return context;
}

interface WizardProviderProps {
  steps: WizardStep[];
  initialStep?: number;
  onComplete?: () => void;
  onValidationError?: (stepId: string) => void;
  children: React.ReactNode;
}

export function WizardProvider({
  steps,
  initialStep = 0,
  onComplete,
  onValidationError,
  children,
}: WizardProviderProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(initialStep);
  const [canGoNext, setCanGoNext] = useState(true);
  const [isValidating, setIsValidating] = useState(false);

  // Guard against empty steps array
  const currentStep = steps.length > 0 ? steps[currentStepIndex] : undefined;
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = steps.length > 0 ? currentStepIndex === steps.length - 1 : true;

  const goToStep = useCallback((index: number) => {
    if (index >= 0 && index < steps.length) {
      setCurrentStepIndex(index);
    }
  }, [steps.length]);

  const goNext = useCallback(async () => {
    // Guard against empty steps or no current step
    if (!currentStep) return false;

    // Run validation if defined
    if (currentStep.validate) {
      setIsValidating(true);
      try {
        const isValid = await currentStep.validate();
        if (!isValid) {
          onValidationError?.(currentStep.id);
          return false;
        }
      } finally {
        setIsValidating(false);
      }
    }

    if (isLastStep) {
      onComplete?.();
      return true;
    }

    setCurrentStepIndex((prev) => Math.min(prev + 1, steps.length - 1));
    return true;
  }, [currentStep, isLastStep, onComplete, onValidationError, steps.length]);

  const goPrevious = useCallback(() => {
    setCurrentStepIndex((prev) => Math.max(prev - 1, 0));
  }, []);

  const value: WizardContextValue = {
    steps,
    currentStepIndex,
    currentStep,
    isFirstStep,
    isLastStep,
    canGoNext,
    canGoPrevious: !isFirstStep,
    isValidating,
    goToStep,
    goNext,
    goPrevious,
    setCanGoNext,
  };

  return (
    <WizardContext.Provider value={value}>
      {children}
    </WizardContext.Provider>
  );
}
