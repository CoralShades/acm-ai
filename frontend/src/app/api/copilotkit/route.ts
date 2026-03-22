/**
 * CopilotKit Runtime Route — Unified Agent (v1 API)
 *
 * Bridges the CopilotKit React frontend to the FastAPI backend's unified
 * agent at /api/agui/chat. Handles both read queries and write operations
 * with interrupt-based HITL approval.
 *
 * Path: /api/copilotkit (CopilotKit convention)
 * Backend: /api/agui/chat (unified agent)
 *
 * @see docs/ag-ui-pipeline-spec.md Section 4 - AG-UI / CopilotKit Integration
 */

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.INTERNAL_API_URL || "http://localhost:5055";

// Lazy singleton — initialized once on first request, reused across all requests.
// Avoids the anti-pattern of creating CopilotRuntime per-request (memory pressure,
// prevents thread persistence).
let _initPromise: Promise<{
  runtime: InstanceType<typeof import("@copilotkit/runtime").CopilotRuntime>;
  adapter: InstanceType<typeof import("@copilotkit/runtime").EmptyAdapter>;
  createEndpoint: typeof import("@copilotkit/runtime").copilotRuntimeNextJSAppRouterEndpoint;
}> | null = null;

function getSharedRuntime() {
  if (!_initPromise) {
    _initPromise = (async () => {
      const {
        CopilotRuntime,
        copilotRuntimeNextJSAppRouterEndpoint,
        EmptyAdapter,
      } = await import("@copilotkit/runtime");
      const { HttpAgent } = await import("@ag-ui/client");

      // Custom adapter bypasses EmptyAdapter name blacklist — needed because
      // all LLM calls happen in the Python backend, not in the JS runtime.
      class AgUiAdapter extends EmptyAdapter {
        get name() {
          return "AgUiAdapter";
        }
      }

      const unifiedAgent = new HttpAgent({
        url: `${BACKEND_URL}/api/agui/chat`,
      });

      const runtime = new CopilotRuntime({
        /* eslint-disable @typescript-eslint/no-explicit-any */
        agents: {
          default: unifiedAgent.clone() as any,
          acm_agent: unifiedAgent as any,
        },
        /* eslint-enable @typescript-eslint/no-explicit-any */
      });

      return {
        runtime,
        adapter: new AgUiAdapter(),
        createEndpoint: copilotRuntimeNextJSAppRouterEndpoint,
      };
    })();
  }
  return _initPromise;
}

export const POST = async (req: Request) => {
  const { runtime, adapter, createEndpoint } = await getSharedRuntime();

  const { handleRequest } = createEndpoint({
    runtime,
    serviceAdapter: adapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
