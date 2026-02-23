import { NextResponse } from "next/server";

interface VercelStatusResponse {
  status: "operational" | "degraded" | "down" | "unknown";
  lastDeployment: string | null;
  deploymentUrl: string | null;
  buildTime: number | null;
  environment: string | null;
  updatedAt: string;
  error?: string;
}

interface VercelDeployment {
  readyState?: string;
  state?: string;
  url?: string;
  createdAt?: number;
  buildingAt?: number;
  ready?: number;
  target?: string;
}

interface VercelApiResponse {
  deployments: VercelDeployment[];
}

const FALLBACK: VercelStatusResponse = {
  status: "unknown",
  lastDeployment: null,
  deploymentUrl: null,
  buildTime: null,
  environment: null,
  updatedAt: new Date().toISOString(),
  error: "No VERCEL_API_TOKEN configured — set it in .env.local to enable live status",
};

function mapVercelState(
  state: string | undefined
): "operational" | "degraded" | "down" | "unknown" {
  switch (state) {
    case "READY":
      return "operational";
    case "ERROR":
    case "CANCELED":
      return "down";
    case "BUILDING":
    case "INITIALIZING":
    case "QUEUED":
      return "degraded";
    default:
      return "unknown";
  }
}

export async function GET(): Promise<NextResponse> {
  const token = process.env.VERCEL_API_TOKEN;
  const teamId = process.env.VERCEL_TEAM_ID;
  const projectId = process.env.VERCEL_PROJECT_ID;

  const headers = {
    "Cache-Control": "public, s-maxage=60, stale-while-revalidate=120",
  };

  if (!token) {
    return NextResponse.json(FALLBACK, { headers });
  }

  try {
    // Build URL with optional team and project scoping
    const params = new URLSearchParams({ limit: "1" });
    if (teamId) params.set("teamId", teamId);
    if (projectId) params.set("projectId", projectId);

    const apiUrl = `https://api.vercel.com/v6/deployments?${params.toString()}`;

    const apiResponse = await fetch(apiUrl, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      next: { revalidate: 60 },
    });

    if (!apiResponse.ok) {
      const errorText = await apiResponse.text().catch(() => "Unknown error");
      return NextResponse.json(
        {
          ...FALLBACK,
          error: `Vercel API returned ${apiResponse.status}: ${errorText.slice(0, 200)}`,
          updatedAt: new Date().toISOString(),
        },
        { headers }
      );
    }

    const data: VercelApiResponse = await apiResponse.json();
    const latest: VercelDeployment | undefined = data.deployments?.[0];

    if (!latest) {
      return NextResponse.json(
        {
          ...FALLBACK,
          error: "No deployments found — verify VERCEL_PROJECT_ID is correct",
          updatedAt: new Date().toISOString(),
        },
        { headers }
      );
    }

    const rawState = latest?.readyState ?? latest?.state;
    const status = mapVercelState(rawState);

    const lastDeployment = latest?.createdAt
      ? new Date(latest.createdAt).toISOString()
      : null;

    const deploymentUrl = latest?.url
      ? `https://${latest.url}`
      : null;

    let buildTime: number | null = null;
    if (latest?.buildingAt && latest?.ready) {
      buildTime = Math.round((latest.ready - latest.buildingAt) / 1000);
    }

    const response: VercelStatusResponse = {
      status,
      lastDeployment,
      deploymentUrl,
      buildTime,
      environment: latest?.target ?? null,
      updatedAt: new Date().toISOString(),
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
