/**
 * CopilotKit Runtime Route (v1 API)
 *
 * Bridges CopilotKit frontend to the FastAPI backend's AG-UI endpoint.
 * Uses dynamic imports to avoid graphql CJS/ESM interop issues during build.
 *
 * Registers an HttpAgent as "supervisor" (matching useCoAgent({ name: 'supervisor' })
 * in the frontend) and a dummy AgUiAdapter to satisfy the serviceAdapter requirement.
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

  const extractionAgent = new HttpAgent({
    url: `${BACKEND_URL}/api/agui/extraction`,
  });

  const runtime = new CopilotRuntime({
    /* eslint-disable @typescript-eslint/no-explicit-any */
    agents: {
      default: supervisorAgent.clone() as any,
      supervisor: supervisorAgent as any,
      extraction: extractionAgent as any,
    },
    /* eslint-enable @typescript-eslint/no-explicit-any */
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new AgUiAdapter(),
    endpoint: "/copilot",
  });

  return handleRequest(req);
};
