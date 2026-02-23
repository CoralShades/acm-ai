import { NextResponse } from "next/server";
import { Octokit } from "@octokit/rest";

interface GitHubStatsResponse {
  status: "operational" | "degraded" | "down" | "unknown";
  commits: number;
  openPRs: number;
  lastCommitMessage: string;
  lastCommitDate: string;
  workflowStatus: string;
  updatedAt: string;
}

const FALLBACK: GitHubStatsResponse = {
  status: "unknown",
  commits: 318,
  openPRs: 3,
  lastCommitMessage: "feat: add cloud deployment config for Railway + Vercel",
  lastCommitDate: new Date().toISOString(),
  workflowStatus: "success",
  updatedAt: new Date().toISOString(),
};

export async function GET(): Promise<NextResponse> {
  const token = process.env.GITHUB_TOKEN;
  const owner = process.env.GITHUB_OWNER ?? "CoralShades";
  const repo = process.env.GITHUB_REPO ?? "acm-ai";

  const headers = {
    "Cache-Control": "public, s-maxage=60, stale-while-revalidate=120",
  };

  if (!token) {
    return NextResponse.json(FALLBACK, { headers });
  }

  try {
    const octokit = new Octokit({ auth: token });

    const [commitsData, prsData, workflowData, contributorsData] = await Promise.all([
      octokit.repos.listCommits({ owner, repo, per_page: 1 }),
      octokit.pulls.list({ owner, repo, state: "open" }),
      octokit.actions.listWorkflowRunsForRepo({ owner, repo, per_page: 1 }),
      octokit.repos.getContributorsStats({ owner, repo }).catch(() => null),
    ]);

    const lastCommit = commitsData.data[0];
    const latestRun = workflowData.data.workflow_runs[0];

    const workflowConclusion = latestRun?.conclusion ?? latestRun?.status ?? "unknown";
    const workflowStatus =
      workflowConclusion === "success"
        ? "success"
        : workflowConclusion === "failure"
          ? "failure"
          : "pending";

    const response: GitHubStatsResponse = {
      status: "operational",
      commits: contributorsData?.data && Array.isArray(contributorsData.data)
        ? contributorsData.data.reduce((sum: number, c: { total?: number }) => sum + (c.total ?? 0), 0)
        : FALLBACK.commits,
      openPRs: prsData.data.length,
      lastCommitMessage:
        lastCommit?.commit?.message?.split("\n")[0] ?? FALLBACK.lastCommitMessage,
      lastCommitDate:
        lastCommit?.commit?.author?.date ?? new Date().toISOString(),
      workflowStatus,
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
