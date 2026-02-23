import { NextResponse } from "next/server";

interface VercelStatusResponse {
  status: "operational" | "degraded" | "down" | "unknown";
  lastDeployment: string | null;
  deploymentUrl: string | null;
  buildTime: number | null;
  updatedAt: string;
}

interface VercelDeployment {
  readyState?: string;
  state?: string;
  url?: string;
  createdAt?: number;
  buildingAt?: number;
  ready?: number;
}

interface VercelApiResponse {
  deployments: VercelDeployment[];
}

const FALLBACK: VercelStatusResponse = {
  status: "unknown",
  lastDeployment: null,
  deploymentUrl: null,
  buildTime: null,
  updatedAt: new Date().toISOString(),
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

  const headers = {
    "Cache-Control": "public, s-maxage=60, stale-while-revalidate=120",
  };

  if (!token) {
    return NextResponse.json(FALLBACK, { headers });
  }

  try {
    const apiResponse = await fetch(
      "https://api.vercel.com/v6/deployments?limit=1",
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    if (!apiResponse.ok) {
      return NextResponse.json(
        { ...FALLBACK, updatedAt: new Date().toISOString() },
        { headers }
      );
    }

    const data: VercelApiResponse = await apiResponse.json();
    const latest: VercelDeployment | undefined = data.deployments?.[0];

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
