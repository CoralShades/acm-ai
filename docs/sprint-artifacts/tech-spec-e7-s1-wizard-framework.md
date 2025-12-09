# Tech Spec: E7-S1 - Create Wizard Framework Component

> **Story:** E7-S1
> **Epic:** Upload Wizard
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Create a reusable multi-step wizard framework component that can be used for the upload flow and other wizard experiences.

---

## User Story

**As a** developer
**I want** a reusable multi-step wizard framework
**So that** I can build consistent wizard experiences

---

## Acceptance Criteria

- [ ] `WizardContainer` component with step navigation
- [ ] Progress indicator showing current step
- [ ] Previous/Next/Finish buttons with proper states
- [ ] Step validation before proceeding
- [ ] Keyboard navigation support (Enter, Escape)
- [ ] Mobile-responsive design

---

## Technical Design

### 1. Wizard Types

Create `frontend/src/components/ui/wizard/types.ts`:

```typescript
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
  currentStep: WizardStep;
  isFirstStep: boolean;
  isLastStep: boolean;
  canGoNext: boolean;
  canGoPrevious: boolean;
  goToStep: (index: number) => void;
  goNext: () => Promise<boolean>;
  goPrevious: () => void;
  setCanGoNext: (can: boolean) => void;
}
```

### 2. Wizard Context

Create `frontend/src/components/ui/wizard/context.tsx`:

```tsx
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
  children: React.ReactNode;
}

export function WizardProvider({
  steps,
  initialStep = 0,
  onComplete,
  children,
}: WizardProviderProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(initialStep);
  const [canGoNext, setCanGoNext] = useState(true);

  const currentStep = steps[currentStepIndex];
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === steps.length - 1;

  const goToStep = useCallback((index: number) => {
    if (index >= 0 && index < steps.length) {
      setCurrentStepIndex(index);
    }
  }, [steps.length]);

  const goNext = useCallback(async () => {
    // Run validation if defined
    if (currentStep.validate) {
      const isValid = await currentStep.validate();
      if (!isValid) return false;
    }

    if (isLastStep) {
      onComplete?.();
      return true;
    }

    setCurrentStepIndex((prev) => Math.min(prev + 1, steps.length - 1));
    return true;
  }, [currentStep, isLastStep, onComplete, steps.length]);

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
```

### 3. Wizard Container

Create `frontend/src/components/ui/wizard/wizard.tsx`:

```tsx
'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { WizardProvider, useWizard } from './context';
import { WizardStep } from './types';
import { cn } from '@/lib/utils';
import { Check, ChevronLeft, ChevronRight } from 'lucide-react';

interface WizardProps {
  steps: WizardStep[];
  initialStep?: number;
  onComplete?: () => void;
  children: React.ReactNode;
  className?: string;
}

export function Wizard({
  steps,
  initialStep,
  onComplete,
  children,
  className,
}: WizardProps) {
  return (
    <WizardProvider steps={steps} initialStep={initialStep} onComplete={onComplete}>
      <div className={cn('flex flex-col h-full', className)}>
        {children}
      </div>
    </WizardProvider>
  );
}

export function WizardProgress({ className }: { className?: string }) {
  const { steps, currentStepIndex } = useWizard();

  return (
    <div className={cn('flex items-center justify-center gap-2 py-4', className)}>
      {steps.map((step, index) => {
        const isCompleted = index < currentStepIndex;
        const isCurrent = index === currentStepIndex;

        return (
          <div key={step.id} className="flex items-center">
            {/* Step indicator */}
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
                isCompleted && 'bg-primary text-primary-foreground',
                isCurrent && 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2',
                !isCompleted && !isCurrent && 'bg-muted text-muted-foreground'
              )}
            >
              {isCompleted ? <Check className="w-4 h-4" /> : index + 1}
            </div>

            {/* Step title (desktop) */}
            <span className={cn(
              'hidden md:block ml-2 text-sm',
              isCurrent ? 'font-medium' : 'text-muted-foreground'
            )}>
              {step.title}
            </span>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div className={cn(
                'w-8 md:w-16 h-0.5 mx-2',
                index < currentStepIndex ? 'bg-primary' : 'bg-muted'
              )} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function WizardContent({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex-1 overflow-y-auto p-4">
      {children}
    </div>
  );
}

export function WizardStepContent({
  stepId,
  children,
}: {
  stepId: string;
  children: React.ReactNode;
}) {
  const { currentStep } = useWizard();

  if (currentStep.id !== stepId) return null;

  return <>{children}</>;
}

export function WizardFooter({ className }: { className?: string }) {
  const {
    isFirstStep,
    isLastStep,
    canGoNext,
    canGoPrevious,
    goNext,
    goPrevious,
  } = useWizard();

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && canGoNext) {
        e.preventDefault();
        goNext();
      }
      if (e.key === 'Escape' && canGoPrevious) {
        e.preventDefault();
        goPrevious();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canGoNext, canGoPrevious, goNext, goPrevious]);

  return (
    <div className={cn('flex justify-between p-4 border-t', className)}>
      <Button
        variant="outline"
        onClick={goPrevious}
        disabled={!canGoPrevious}
      >
        <ChevronLeft className="w-4 h-4 mr-2" />
        Previous
      </Button>

      <Button
        onClick={goNext}
        disabled={!canGoNext}
      >
        {isLastStep ? 'Finish' : 'Next'}
        {!isLastStep && <ChevronRight className="w-4 h-4 ml-2" />}
      </Button>
    </div>
  );
}
```

### 4. Usage Example

```tsx
import {
  Wizard,
  WizardProgress,
  WizardContent,
  WizardStepContent,
  WizardFooter,
} from '@/components/ui/wizard';

const steps = [
  { id: 'upload', title: 'Upload Files' },
  { id: 'type', title: 'Document Type' },
  { id: 'options', title: 'Options' },
  { id: 'review', title: 'Review' },
  { id: 'progress', title: 'Progress' },
];

export function UploadWizard() {
  const handleComplete = () => {
    console.log('Wizard completed!');
  };

  return (
    <Wizard steps={steps} onComplete={handleComplete}>
      <WizardProgress />
      <WizardContent>
        <WizardStepContent stepId="upload">
          <UploadStep />
        </WizardStepContent>
        <WizardStepContent stepId="type">
          <TypeStep />
        </WizardStepContent>
        {/* ... other steps */}
      </WizardContent>
      <WizardFooter />
    </Wizard>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/ui/wizard/types.ts` | New - Type definitions |
| `frontend/src/components/ui/wizard/context.tsx` | New - Wizard context |
| `frontend/src/components/ui/wizard/wizard.tsx` | New - Wizard components |
| `frontend/src/components/ui/wizard/index.ts` | New - Exports |

---

## Dependencies

None - foundational component

---

## Testing

1. Navigate through all steps
2. Verify progress indicator updates
3. Test Previous/Next buttons
4. Test keyboard navigation (Enter/Escape)
5. Test step validation (block next if invalid)
6. Test responsive layout on mobile
7. Test with different number of steps

---

## Estimated Complexity

**Medium** - Reusable component with context and state management

---
