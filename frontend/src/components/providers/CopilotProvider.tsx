"use client";

import { CopilotKit } from "@copilotkit/react-core";
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
interface CopilotErrorBoundaryProps {
  children: React.ReactNode;
  runtimeUrl: string;
}

class CopilotErrorBoundary extends React.Component<
  CopilotErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: CopilotErrorBoundaryProps) {
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
    return (
      <CopilotKit
        runtimeUrl={this.props.runtimeUrl}
        showDevConsole={false}
        onError={(error) => {
          console.error("[CopilotKit] Runtime error:", error);
        }}
      >
        {this.props.children}
      </CopilotKit>
    );
  }
}

/**
 * CopilotKit provider that wraps the application.
 *
 * Connects to /api/copilotkit which bridges to the FastAPI
 * AG-UI supervisor agent at /api/agui/chat. Falls back gracefully
 * if CopilotKit fails to connect - the rest of the app remains functional.
 *
 * Path follows the CopilotKit convention (/api/copilotkit).
 * @see docs/ag-ui-pipeline-spec.md Section 4
 */
export function CopilotProvider({ children }: CopilotProviderProps) {
  return (
    <CopilotErrorBoundary runtimeUrl="/api/copilotkit">
      {children}
    </CopilotErrorBoundary>
  );
}
