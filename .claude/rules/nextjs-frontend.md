---
paths:
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
  - "frontend/**/*.js"
  - "frontend/**/*.jsx"
---

# Next.js Frontend Rules for ACM-AI

## Framework
- Next.js 15 with App Router
- React 19 with Turbopack

## Component Structure

### Base UI Components
Location: `frontend/src/components/ui/`
- shadcn/ui-style components
- Use Radix UI primitives

### Feature Components
- `notebooks/` - Notebook management
- `sources/` - Source/document handling
- `notes/` - Note management
- `common/` - Shared components

## State Management

### Server State
Use React Query (`@tanstack/react-query`):
```tsx
const { data, isLoading } = useQuery({
  queryKey: ['notebooks'],
  queryFn: fetchNotebooks,
});
```

### Client State
Use Zustand stores in `frontend/src/stores/`:
```tsx
import { useNotebookStore } from '@/stores/notebookStore';
```

## Forms
- React Hook Form for form state
- Zod for validation schemas

## Styling
- Tailwind CSS 4
- Use `cn()` utility for class merging
- Follow design system in `ui/` components

## API Calls
- Use axios client from `frontend/src/lib/`
- All API routes proxied through `/api/*` to backend
