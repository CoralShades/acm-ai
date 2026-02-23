import { NextResponse } from "next/server";

interface RailwayStatusResponse {
  status: "operational" | "degraded" | "down" | "unknown";
  lastDeploy: string | null;
  uptime: string | null;
  updatedAt: string;
}

interface RailwayDeployment {
  id: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

interface RailwayGraphQLResponse {
  data?: {
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
  lastDeploy: null,
  uptime: null,
  updatedAt: new Date().toISOString(),
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

const RAILWAY_QUERY = `
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

  const headers = {
    "Cache-Control": "public, s-maxage=60, stale-while-revalidate=120",
  };

  if (!token) {
    return NextResponse.json(FALLBACK, { headers });
  }

  try {
    const apiResponse = await fetch(
      "https://backboard.railway.com/graphql/v2",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: RAILWAY_QUERY }),
      }
    );

    if (!apiResponse.ok) {
      return NextResponse.json(
        { ...FALLBACK, updatedAt: new Date().toISOString() },
        { headers }
      );
    }

    const data: RailwayGraphQLResponse = await apiResponse.json();

    if (data.errors?.length) {
      return NextResponse.json(
        { ...FALLBACK, updatedAt: new Date().toISOString() },
        { headers }
      );
    }

    const latestEdge = data.data?.deployments?.edges?.[0];
    const latestDeployment = latestEdge?.node;

    const status = mapRailwayStatus(latestDeployment?.status);

    const lastDeploy = latestDeployment?.createdAt
      ? new Date(latestDeployment.createdAt).toISOString()
      : null;

    let uptime: string | null = null;
    if (
      latestDeployment?.createdAt &&
      latestDeployment?.status?.toUpperCase() === "SUCCESS"
    ) {
      const deployedAt = new Date(latestDeployment.createdAt);
      const now = new Date();
      const diffMs = now.getTime() - deployedAt.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      const diffHours = Math.floor(
        (diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
      );

      if (diffDays > 0) {
        uptime = `${diffDays}d ${diffHours}h`;
      } else {
        const diffMinutes = Math.floor(
          (diffMs % (1000 * 60 * 60)) / (1000 * 60)
        );
        uptime = `${diffHours}h ${diffMinutes}m`;
      }
    }

    const response: RailwayStatusResponse = {
      status,
      lastDeploy,
      uptime,
      updatedAt: new Date().toISOString(),
    };

    return NextResponse.json(response, { headers });
  } catch {
    return NextResponse.json(
      { ...FALLBACK, updatedAt: new Date().toISOString() },
      { headers }
    );
  }
}
