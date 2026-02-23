# E20-S1: Marketing to App Linking

## Story Info
- **Epic**: E20 — Marketing-App Cross-Site Navigation & Domain Cutover
- **Status**: done
- **Priority**: P0
- **Created**: 2026-02-23

## Description
Wire marketing-site header, hero, and footer CTAs to open the deployed app host with an environment-configurable URL.

## Acceptance Criteria
- [x] Header includes `Open App` link.
- [x] Hero primary CTA uses `Open App` and targets app host.
- [x] Footer includes `Open App` in Product links.
- [x] URL source is `NEXT_PUBLIC_APP_URL` via shared helper.

## Key Files
- `marketing-site/src/components/Navigation.tsx`
- `marketing-site/src/components/landing/Hero.tsx`
- `marketing-site/src/components/Footer.tsx`
- `marketing-site/src/lib/site-urls.ts`
- `marketing-site/.env.local.example`
