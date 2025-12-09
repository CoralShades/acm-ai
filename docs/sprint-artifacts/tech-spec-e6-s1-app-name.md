# Tech Spec: E6-S1 - Update Application Name and Title

> **Story:** E6-S1
> **Epic:** Rebranding to ACM-AI
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Update all application branding from "Open Notebook" to "ACM-AI" across frontend and backend.

---

## User Story

**As a** user
**I want** the app to be called "ACM-AI"
**So that** I know its purpose

---

## Acceptance Criteria

- [ ] Browser tab title: "ACM-AI"
- [ ] Header shows "ACM-AI" logo/text
- [ ] package.json name updated
- [ ] API docs title updated

---

## Technical Design

### 1. Frontend Title and Metadata

Update `frontend/src/app/layout.tsx`:

```tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    default: 'ACM-AI',
    template: '%s | ACM-AI',
  },
  description: 'AI-powered Asbestos Containing Material Register analysis and management',
  keywords: ['ACM', 'asbestos', 'SAMP', 'compliance', 'AI'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

### 2. Header Component Update

Update `frontend/src/components/layout/AppHeader.tsx` or equivalent:

```tsx
export function AppHeader() {
  return (
    <header className="border-b">
      <div className="flex items-center h-14 px-4">
        {/* Logo/Brand */}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">A</span>
          </div>
          <span className="font-semibold text-lg">ACM-AI</span>
        </Link>

        {/* Rest of header... */}
      </div>
    </header>
  );
}
```

### 3. Sidebar Brand Update

Update `frontend/src/components/layout/AppSidebar.tsx`:

```tsx
export function AppSidebar() {
  return (
    <aside className="w-64 border-r flex flex-col">
      {/* Brand */}
      <div className="h-14 flex items-center px-4 border-b">
        <Link href="/" className="flex items-center gap-2">
          <Logo className="w-8 h-8" />
          <span className="font-semibold">ACM-AI</span>
        </Link>
      </div>

      {/* Navigation... */}
    </aside>
  );
}
```

### 4. Package.json Update

Update `frontend/package.json`:

```json
{
  "name": "acm-ai-frontend",
  "version": "1.0.0",
  "description": "ACM-AI Frontend - Asbestos Register Management"
}
```

### 5. Backend API Docs Update

Update `api/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(
    title="ACM-AI API",
    description="API for ACM-AI - Asbestos Containing Material Register Analysis",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
```

### 6. Environment and Config

Create/update config for branding:

```tsx
// frontend/src/config/branding.ts
export const BRANDING = {
  name: 'ACM-AI',
  fullName: 'ACM-AI - Asbestos Register Management',
  tagline: 'AI-powered compliance document analysis',
  description: 'Analyze and manage Asbestos Containing Material registers with AI assistance',
} as const;
```

Use throughout app:

```tsx
import { BRANDING } from '@/config/branding';

<title>{BRANDING.name}</title>
<h1>{BRANDING.fullName}</h1>
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/layout.tsx` | Update metadata |
| `frontend/src/components/layout/AppHeader.tsx` | Update brand |
| `frontend/src/components/layout/AppSidebar.tsx` | Update brand |
| `frontend/package.json` | Update name |
| `api/main.py` | Update FastAPI title |
| `frontend/src/config/branding.ts` | New - centralized branding |

---

## Dependencies

None - can be done independently

---

## Testing

1. Open app - verify browser tab shows "ACM-AI"
2. Check header shows "ACM-AI" text/logo
3. Check sidebar shows "ACM-AI" brand
4. Visit /api/docs - verify title shows "ACM-AI API"
5. Search codebase for "Open Notebook" - ensure none remain in user-facing locations

---

## Estimated Complexity

**Low** - Simple text and metadata changes

---
