# Deployment

The marketing site is designed for Vercel deployment but can run on any Node.js hosting platform.

## Vercel Deployment

### Initial Setup

1. Push the repository to GitHub (already at `CoralShades/acm-ai`)
2. Import the project in Vercel Dashboard
3. Set the **Root Directory** to `marketing-site`
4. Framework preset: **Next.js** (auto-detected)
5. Build command: `npm run build` (default)
6. Output directory: `.next` (default)

### Environment Variables

Add these in Vercel Dashboard > Settings > Environment Variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_APP_URL` | Yes | App host used by `Open App` CTAs (example: `https://demo.vaea.coralshades.ai`) |
| `GITHUB_TOKEN` | No | GitHub PAT for live project stats |
| `GITHUB_OWNER` | No | GitHub org/user (default: `CoralShades`) |
| `GITHUB_REPO` | No | GitHub repo name (default: `acm-ai`) |
| `VERCEL_API_TOKEN` | No | Vercel API token for deployment status |
| `RAILWAY_API_TOKEN` | No | Railway API token for backend health |

All tokens are optional — the site works without them using static fallback data.

### Vercel Configuration

The `vercel.json` file configures:
- Framework: `nextjs`
- Build command: `npm run build`
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`
- API route caching: `s-maxage=60, stale-while-revalidate=120`

### Custom Domain

Configure in Vercel Dashboard > Settings > Domains. Update `public/sitemap.xml` and `public/robots.txt` with the new domain.

### Multi-Project Vercel Setup (Marketing + App)

Use two Vercel projects from the monorepo:

1. **Marketing project**
- Root Directory: `marketing-site`
- Domain: `vaea.coralshades.ai`
- Env: `NEXT_PUBLIC_APP_URL=https://demo.vaea.coralshades.ai`

2. **App project**
- Root Directory: `frontend`
- Domain: `demo.vaea.coralshades.ai`
- Env: `NEXT_PUBLIC_MARKETING_URL=https://vaea.coralshades.ai`

Cutover strategy:
- Make `vaea.coralshades.ai` point to marketing as canonical entrypoint.
- Keep app on `demo.vaea.coralshades.ai`.
- Add 301 redirects from any legacy app aliases to the demo subdomain.

## Local Production Build

```bash
cd marketing-site
npm run build        # Build for production
npm run start        # Serve at http://localhost:3000
```

## Docker Deployment (Alternative)

Create a `Dockerfile` in `marketing-site/`:

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

For standalone output, add to `next.config.ts`:
```typescript
const nextConfig: NextConfig = {
  output: "standalone",
  // ... existing config
};
```

## CI/CD

### GitHub Actions

Add a workflow for the marketing site:

```yaml
# .github/workflows/marketing-site.yml
name: Marketing Site CI
on:
  push:
    paths: ['marketing-site/**']
  pull_request:
    paths: ['marketing-site/**']

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: marketing-site
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
          cache-dependency-path: marketing-site/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm run build
```

### Vercel Auto-Deploy

Vercel automatically deploys on push to `main`. Configure in Vercel Dashboard:
- **Production Branch**: `main`
- **Root Directory**: `marketing-site`
- **Ignored Build Step**: Use `git diff --quiet HEAD^ HEAD -- marketing-site/` to skip deploys when no marketing-site files changed

## SEO Artifacts

| File | Purpose | Update When |
|------|---------|------------|
| `public/robots.txt` | Search engine directives | Changing domain |
| `public/sitemap.xml` | Page listing for crawlers | Adding/removing pages |
| `vercel.json` | Deploy config + security headers | Changing hosting setup |
| `src/app/layout.tsx` | Root metadata (title template, OG tags) | Changing branding |
| `src/app/*/layout.tsx` | Per-page metadata | Changing page titles/descriptions |

## Monitoring

After deployment, verify:
1. All 5 pages load correctly
2. API routes return data (or graceful fallbacks)
3. Fumadocs sidebar navigation works
4. Framer Motion animations play on scroll
5. Dark/light mode toggle works
6. Mobile responsive at 375px, 768px
