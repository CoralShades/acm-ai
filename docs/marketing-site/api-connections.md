# API Connections

The marketing site has 3 API routes that fetch live infrastructure data. All routes gracefully degrade to static fallback data when tokens are not configured.

## Configuration

Copy `.env.local.example` to `.env.local` and add your tokens:

```bash
# GitHub API (for live project stats widget)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_OWNER=CoralShades
GITHUB_REPO=acm-ai

# Vercel API (for deployment status widget)
VERCEL_API_TOKEN=xxxxxxxxxxxx

# Railway API (for backend health widget)
RAILWAY_API_TOKEN=xxxxxxxxxxxx
```

## API Routes

### GitHub Stats — `GET /api/github/stats`

**Source**: `src/app/api/github/stats/route.ts`

Uses `@octokit/rest` to fetch 4 data points in parallel:
- Repository metadata (commit count proxy)
- Latest commit (message + date)
- Open pull requests
- Latest workflow run status

**Response shape**:
```typescript
{
  status: "operational" | "degraded" | "down" | "unknown",
  commits: number,
  openPRs: number,
  lastCommitMessage: string,
  lastCommitDate: string,      // ISO 8601
  workflowStatus: "success" | "failure" | "pending",
  updatedAt: string            // ISO 8601
}
```

**Token**: Create a GitHub Personal Access Token with `repo` scope at https://github.com/settings/tokens.

### Vercel Status — `GET /api/vercel/status`

**Source**: `src/app/api/vercel/status/route.ts`

Uses the Vercel REST API to fetch the latest deployment:

**Response shape**:
```typescript
{
  status: "operational" | "degraded" | "down" | "unknown",
  lastDeployment: string | null,   // ISO 8601
  deploymentUrl: string | null,    // https://...
  buildTime: number | null,        // seconds
  updatedAt: string                // ISO 8601
}
```

**Token**: Create at https://vercel.com/account/tokens. The token needs access to the project's team/scope.

### Railway Status — `GET /api/railway/status`

**Source**: `src/app/api/railway/status/route.ts`

Uses Railway's GraphQL API (`https://backboard.railway.com/graphql/v2`) to fetch the latest deployment:

**Response shape**:
```typescript
{
  status: "operational" | "degraded" | "down" | "unknown",
  lastDeploy: string | null,   // ISO 8601
  uptime: string | null,       // "3d 12h" or "2h 45m"
  updatedAt: string            // ISO 8601
}
```

**Token**: Create at https://railway.com/account/tokens.

## Fallback Behavior

When a token is missing or an API call fails, each route returns a static `FALLBACK` object with `status: "unknown"` and sensible defaults. The frontend components display this as a gray "Unknown" status indicator instead of erroring.

The caching header `Cache-Control: public, s-maxage=60, stale-while-revalidate=120` means:
- CDN caches responses for 60 seconds
- Serves stale content for up to 120 seconds while revalidating in the background

## Consumer Components

These components consume the API data:

| Component | API Route | Behavior |
|-----------|-----------|----------|
| `LiveStatusStrip` (landing) | All 3 | Shows status dots, skeleton loader while fetching |
| `StatusPage` (/status) | All 3 | Full infrastructure dashboard with detailed metrics |

Both use SWR with 60-second refresh:
```typescript
const { data } = useSWR("/api/github/stats", fetcher, { refreshInterval: 60000 });
```

## Adding a New API Connection

1. Create the route handler at `src/app/api/my-service/route.ts`
2. Define a typed response interface and a `FALLBACK` constant
3. Check for the env token — return fallback if missing
4. Add the env var to `.env.local.example`
5. Use `Cache-Control: public, s-maxage=60` headers
6. Consume with SWR in your component
