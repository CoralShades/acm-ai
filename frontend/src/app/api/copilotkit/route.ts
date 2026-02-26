/**
 * CopilotKit Runtime Route — Main Supervisor Agent (v1 API)
 *
 * Bridges the CopilotKit React frontend to the FastAPI backend's AG-UI
 * supervisor agent at /api/agui/chat. This is the primary CopilotKit
 * runtime endpoint used by the dashboard-level CopilotProvider.
 *
 * The CRUD chat has a separate runtime at /copilot-crud/route.ts to
 * keep write-capable tools isolated from the read-only supervisor.
 *
 * Path: /api/copilotkit (CopilotKit convention)
 * Backend: /api/agui/chat (supervisor agent)
 *
 * @see docs/ag-ui-pipeline-spec.md Section 4 - AG-UI / CopilotKit Integration
 */

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.INTERNAL_API_URL || "http://localhost:5055";

export const POST = async (req: Request) => {
  const {
    CopilotRuntime,
    copilotRuntimeNextJSAppRouterEndpoint,
    EmptyAdapter,
  } = await import("@copilotkit/runtime");
  const { HttpAgent } = await import("@ag-ui/client");

  // Custom adapter bypasses EmptyAdapter name blacklist.
  class AgUiAdapter extends EmptyAdapter {
    get name() {
      return "AgUiAdapter";
    }
  }

  const supervisorAgent = new HttpAgent({
    url: `${BACKEND_URL}/api/agui/chat`,
  });

  const runtime = new CopilotRuntime({
    /* eslint-disable @typescript-eslint/no-explicit-any */
    agents: {
      default: supervisorAgent.clone() as any,
      supervisor: supervisorAgent as any,
    },
    /* eslint-enable @typescript-eslint/no-explicit-any */
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new AgUiAdapter(),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
