/**
 * CopilotKit Runtime Route for CRUD Chat (v1 API)
 *
 * Bridges the CRUD chat frontend to the FastAPI backend's AG-UI
 * crud-chat endpoint. Mirrors the pattern in /api/copilotkit/route.ts but
 * registers the crud agent instead of the supervisor agent.
 *
 * Story: E19-S8 Conversational CRUD Chat
 */

export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.INTERNAL_API_URL || "http://localhost:5055";

// Lazy singleton — initialized once on first request, reused across all requests.
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

      class AgUiAdapter extends EmptyAdapter {
        get name() {
          return "AgUiAdapter";
        }
      }

      const crudAgent = new HttpAgent({
        url: `${BACKEND_URL}/api/agui/crud-chat`,
      });

      const runtime = new CopilotRuntime({
        /* eslint-disable @typescript-eslint/no-explicit-any */
        agents: {
          default: crudAgent.clone() as any,
          crud: crudAgent as any,
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
    endpoint: "/copilot-crud",
  });

  return handleRequest(req);
};
