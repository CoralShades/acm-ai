"use client";

import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import React from "react";

interface CopilotProviderProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Error boundary that catches CopilotKit initialization failures
 * and renders children without the CopilotKit context.
 */
class CopilotErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.warn("[CopilotProvider] CopilotKit failed to initialize:", error.message);
  }

  render() {
    if (this.state.hasError) {
      // Render children without CopilotKit context - Smart Chat will be unavailable
      return this.props.children;
    }
    return this.props.children;
  }
}

/**
 * CopilotKit provider that wraps the application.
 *
 * Connects to the /copilot route which bridges to the FastAPI
 * AG-UI supervisor agent. Falls back gracefully if CopilotKit
 * fails to connect - the rest of the app remains functional.
 */
export function CopilotProvider({ children }: CopilotProviderProps) {
  return (
    <CopilotErrorBoundary>
      <CopilotKit runtimeUrl="/copilot">
        {children}
      </CopilotKit>
    </CopilotErrorBoundary>
  );
}
