export interface WizardStep {
  id: string;
  title: string;
  description?: string;
  icon?: React.ElementType;
  isOptional?: boolean;
  validate?: () => boolean | Promise<boolean>;
}

export interface WizardContextValue {
  steps: WizardStep[];
  currentStepIndex: number;
  currentStep: WizardStep | undefined;
  isFirstStep: boolean;
  isLastStep: boolean;
  canGoNext: boolean;
  canGoPrevious: boolean;
  isValidating: boolean;
  goToStep: (index: number) => void;
  goNext: () => Promise<boolean>;
  goPrevious: () => void;
  setCanGoNext: (can: boolean) => void;
}
