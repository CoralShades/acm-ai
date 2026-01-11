'use client';

import { useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { WizardProvider, useWizard } from './context';
import { WizardStep } from './types';
import { cn } from '@/lib/utils';
import { Check, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

interface WizardProps {
  steps: WizardStep[];
  initialStep?: number;
  onComplete?: () => void;
  onValidationError?: (stepId: string) => void;
  children: React.ReactNode;
  className?: string;
}

export function Wizard({
  steps,
  initialStep,
  onComplete,
  onValidationError,
  children,
  className,
}: WizardProps) {
  return (
    <WizardProvider
      steps={steps}
      initialStep={initialStep}
      onComplete={onComplete}
      onValidationError={onValidationError}
    >
      <div className={cn('flex flex-col h-full', className)}>
        {children}
      </div>
    </WizardProvider>
  );
}

export function WizardProgress({ className }: { className?: string }) {
  const { steps, currentStepIndex } = useWizard();

  return (
    <div
      className={cn('flex items-center justify-center gap-2 py-4', className)}
      role="progressbar"
      aria-valuenow={currentStepIndex + 1}
      aria-valuemin={1}
      aria-valuemax={steps.length}
      aria-label={`Step ${currentStepIndex + 1} of ${steps.length}`}
    >
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
              aria-label={`${step.title}${isCompleted ? ' (completed)' : isCurrent ? ' (current)' : ''}`}
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

export function WizardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('flex-1 overflow-y-auto p-4', className)}>
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

  if (!currentStep || currentStep.id !== stepId) return null;

  return <>{children}</>;
}

interface WizardFooterProps {
  className?: string;
  previousLabel?: string;
  nextLabel?: string;
  finishLabel?: string;
  validatingLabel?: string;
  onCancel?: () => void;
  showCancel?: boolean;
  cancelLabel?: string;
  enableKeyboardNav?: boolean;
}

export function WizardFooter({
  className,
  previousLabel = 'Previous',
  nextLabel = 'Next',
  finishLabel = 'Finish',
  validatingLabel = 'Validating...',
  onCancel,
  showCancel = false,
  cancelLabel = 'Cancel',
  enableKeyboardNav = true,
}: WizardFooterProps) {
  const {
    isLastStep,
    canGoNext,
    canGoPrevious,
    isValidating,
    goNext,
    goPrevious,
  } = useWizard();

  const footerRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation - scoped to when wizard footer is in view
  useEffect(() => {
    if (!enableKeyboardNav) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // Only handle if wizard footer is visible in the DOM
      if (!footerRef.current || !document.body.contains(footerRef.current)) {
        return;
      }

      // Check if footer is visible (not hidden via CSS)
      const style = window.getComputedStyle(footerRef.current);
      if (style.display === 'none' || style.visibility === 'hidden') {
        return;
      }

      if (e.key === 'Enter' && canGoNext && !isValidating) {
        e.preventDefault();
        goNext();
      }
      if (e.key === 'Escape' && canGoPrevious && !isValidating) {
        e.preventDefault();
        goPrevious();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canGoNext, canGoPrevious, isValidating, goNext, goPrevious, enableKeyboardNav]);

  const isNextDisabled = !canGoNext || isValidating;

  return (
    <div ref={footerRef} className={cn('flex justify-between p-4 border-t', className)}>
      <div className="flex gap-2">
        {showCancel && onCancel && (
          <Button
            variant="ghost"
            onClick={onCancel}
            disabled={isValidating}
          >
            {cancelLabel}
          </Button>
        )}
        <Button
          variant="outline"
          onClick={goPrevious}
          disabled={!canGoPrevious || isValidating}
        >
          <ChevronLeft className="w-4 h-4 mr-2" />
          {previousLabel}
        </Button>
      </div>

      <Button
        onClick={goNext}
        disabled={isNextDisabled}
      >
        {isValidating ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            {validatingLabel}
          </>
        ) : (
          <>
            {isLastStep ? finishLabel : nextLabel}
            {!isLastStep && <ChevronRight className="w-4 h-4 ml-2" />}
          </>
        )}
      </Button>
    </div>
  );
}
