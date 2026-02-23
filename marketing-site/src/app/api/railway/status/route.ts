import { NextResponse } from "next/server";

interface ServiceStatus {
  name: string;
  status: "operational" | "degraded" | "down" | "unknown";
  lastDeploy: string | null;
}

interface RailwayStatusResponse {
  status: "operational" | "degraded" | "down" | "unknown";
  services: ServiceStatus[];
  lastDeploy: string | null;
  uptime: string | null;
  updatedAt: string;
  error?: string;
}

interface RailwayDeployment {
  id: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

interface RailwayService {
  id: string;
  name: string;
  deployments: {
    edges: Array<{
      node: RailwayDeployment;
    }>;
  };
}

interface RailwayGraphQLResponse {
  data?: {
    project?: {
      services?: {
        edges?: Array<{
          node: RailwayService;
        }>;
      };
    };
    deployments?: {
      edges?: Array<{
        node: RailwayDeployment;
      }>;
    };
  };
  errors?: Array<{ message: string }>;
}

const FALLBACK: RailwayStatusResponse = {
  status: "unknown",
  services: [],
  lastDeploy: null,
  uptime: null,
  updatedAt: new Date().toISOString(),
  error: "No RAILWAY_API_TOKEN configured — set it in .env.local to enable live status",
};

function mapRailwayStatus(
  railwayStatus: string | undefined
): "operational" | "degraded" | "down" | "unknown" {
  switch (railwayStatus?.toUpperCase()) {
    case "SUCCESS":
      return "operational";
    case "FAILED":
    case "CRASHED":
      return "down";
    case "BUILDING":
    case "DEPLOYING":
    case "INITIALIZING":
    case "WAITING":
      return "degraded";
    case "REMOVED":
    case "REMOVING":
      return "down";
    default:
      return "unknown";
  }
}

function computeUptime(createdAt: string | undefined, status: string | undefined): string | null {
  if (!createdAt || status?.toUpperCase() !== "SUCCESS") return null;

  const deployedAt = new Date(createdAt);
  const now = new Date();
  const diffMs = now.getTime() - deployedAt.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (diffDays > 0) return `${diffDays}d ${diffHours}h`;
  const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  return `${diffHours}h ${diffMinutes}m`;
}

// Query with project scoping — gets all services and their latest deployment
function buildProjectQuery(projectId: string) {
  return `
    query {
      project(id: "${projectId}") {
        services {
          edges {
            node {
              id
              name
              deployments(first: 1) {
                edges {
                  node {
                    id
                    status
                    createdAt
                    updatedAt
                  }
                }
              }
            }
          }
        }
      }
    }
  `;
}

// Fallback query without project scoping (less reliable)
const FALLBACK_QUERY = `
  query {
    deployments(first: 1) {
      edges {
        node {
          id
          status
          createdAt
          updatedAt
        }
      }
    }
  }
`;

export async function GET(): Promise<NextResponse> {
  const token = process.env.RAILWAY_API_TOKEN;
  const projectId = process.env.RAILWAY_PROJECT_ID;

  const headers = {
    "Cache-Control": "public, s-maxage=60, stale-while-revalidate=120",
  };

  if (!token) {
    return NextResponse.json(FALLBACK, { headers });
  }

  const query = projectId ? buildProjectQuery(projectId) : FALLBACK_QUERY;

  try {
    const apiResponse = await fetch(
      "https://backboard.railway.com/graphql/v2",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
        next: { revalidate: 60 },
      }
    );

    if (!apiResponse.ok) {
      const errorText = await apiResponse.text().catch(() => "Unknown error");
      return NextResponse.json(
        {
          ...FALLBACK,
          error: `Railway API returned ${apiResponse.status}: ${errorText.slice(0, 200)}`,
          updatedAt: new Date().toISOString(),
        },
        { headers }
      );
    }

    const data: RailwayGraphQLResponse = await apiResponse.json();

    if (data.errors?.length) {
      return NextResponse.json(
        {
          ...FALLBACK,
          error: `Railway GraphQL error: ${data.errors[0].message}`,
          updatedAt: new Date().toISOString(),
        },
        { headers }
      );
    }

    // If we have project-level data with services
    if (data.data?.project?.services?.edges) {
      const serviceEdges = data.data.project.services.edges;
      const services: ServiceStatus[] = serviceEdges.map((edge) => {
        const svc = edge.node;
        const latestDeploy = svc.deployments?.edges?.[0]?.node;
        return {
          name: svc.name,
          status: mapRailwayStatus(latestDeploy?.status),
          lastDeploy: latestDeploy?.createdAt
            ? new Date(latestDeploy.createdAt).toISOString()
            : null,
        };
      });

      // Overall status: "operational" if all are, "degraded" if any are, "down" if any are down
      const hasDown = services.some((s) => s.status === "down");
      const hasDegraded = services.some((s) => s.status === "degraded");
      const allOperational = services.every((s) => s.status === "operational");
      const overallStatus = hasDown ? "down" : hasDegraded ? "degraded" : allOperational ? "operational" : "unknown";

      const latestDeploy = services
        .map((s) => s.lastDeploy)
        .filter(Boolean)
        .sort()
        .reverse()[0] ?? null;

      const latestDeployNode = serviceEdges
        .flatMap((e) => e.node.deployments?.edges ?? [])
        .map((e) => e.node)
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())[0];

      return NextResponse.json(
        {
          status: overallStatus,
          services,
          lastDeploy: latestDeploy,
          uptime: computeUptime(latestDeployNode?.createdAt, latestDeployNode?.status),
          updatedAt: new Date().toISOString(),
        } satisfies RailwayStatusResponse,
        { headers }
      );
    }

    // Fallback: single deployment query (no project scoping)
    const latestEdge = data.data?.deployments?.edges?.[0];
    const latestDeployment = latestEdge?.node;

    const status = mapRailwayStatus(latestDeployment?.status);
    const lastDeploy = latestDeployment?.createdAt
      ? new Date(latestDeployment.createdAt).toISOString()
      : null;

    const response: RailwayStatusResponse = {
      status,
      services: [],
      lastDeploy,
      uptime: computeUptime(latestDeployment?.createdAt, latestDeployment?.status),
      updatedAt: new Date().toISOString(),
      error: projectId ? undefined : "Set RAILWAY_PROJECT_ID for per-service status",
    };

    return NextResponse.json(response, { headers });
  } catch (err) {
    return NextResponse.json(
      {
        ...FALLBACK,
        error: `Fetch failed: ${err instanceof Error ? err.message : "Unknown error"}`,
        updatedAt: new Date().toISOString(),
      },
      { headers }
    );
  }
}
