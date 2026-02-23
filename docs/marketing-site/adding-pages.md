# Adding Pages

How to add new routes, components, and sections to the marketing site.

## Adding a New Page Route

Next.js App Router uses file-system routing. To add a new page:

1. Create the route directory and files:
   ```
   src/app/my-page/
     page.tsx      ← The page component
     layout.tsx    ← (Optional) Page-specific metadata
   ```

2. For a server-rendered page with metadata:
   ```typescript
   // src/app/my-page/page.tsx
   import type { Metadata } from "next";

   export const metadata: Metadata = {
     title: "My Page",
     description: "Description for SEO",
   };

   export default function MyPage() {
     return <div>...</div>;
   }
   ```

3. For a client-side interactive page (with Framer Motion, etc.):
   ```typescript
   // src/app/my-page/layout.tsx — metadata in layout (server component)
   import type { Metadata } from "next";

   export const metadata: Metadata = {
     title: "My Page",
     description: "Description for SEO",
   };

   export default function MyPageLayout({
     children,
   }: { children: React.ReactNode }) {
     return children;
   }
   ```

   ```typescript
   // src/app/my-page/page.tsx — interactive content (client component)
   "use client";

   import { motion } from "framer-motion";
   import { fadeUp } from "@/lib/animations";
   import { useInView } from "@/hooks/useInView";

   export default function MyPage() {
     const { ref, isInView } = useInView({ threshold: 0.1 });
     return (
       <div ref={ref}>
         <motion.div variants={fadeUp} initial="hidden" animate={isInView ? "visible" : "hidden"}>
           ...
         </motion.div>
       </div>
     );
   }
   ```

4. Add the page to the Navigation component (`src/components/Navigation.tsx`):
   ```typescript
   const navLinks = [
     // ... existing links
     { href: "/my-page", label: "My Page" },
   ];
   ```

5. Add the page to `public/sitemap.xml`.

## Adding a Landing Page Section

1. Create the component in `src/components/landing/`:
   ```typescript
   // src/components/landing/MySection.tsx
   "use client";

   import { motion } from "framer-motion";
   import { fadeUp } from "@/lib/animations";
   import { useInView } from "@/hooks/useInView";

   export function MySection() {
     const { ref, isInView } = useInView({ threshold: 0.1 });

     return (
       <section className="py-20 px-6" ref={ref}>
         <div className="max-w-6xl mx-auto">
           <motion.div
             variants={fadeUp}
             initial="hidden"
             animate={isInView ? "visible" : "hidden"}
           >
             <h2 className="text-3xl font-bold text-vaea-navy">Section Title</h2>
             {/* Content */}
           </motion.div>
         </div>
       </section>
     );
   }
   ```

2. Import and add it to `src/app/page.tsx`:
   ```typescript
   import { MySection } from "@/components/landing/MySection";
   // ... in the JSX:
   <MySection />
   ```

## Adding a Demo Section

1. Create the component in `src/components/demo/`:
   ```typescript
   // src/components/demo/MyDemoSection.tsx
   "use client";

   import { motion } from "framer-motion";
   import { fadeUp } from "@/lib/animations";
   import { useInView } from "@/hooks/useInView";

   export function MyDemoSection() {
     const { ref, isInView } = useInView({ threshold: 0.1 });

     return (
       <div className="space-y-4" ref={ref}>
         <motion.div variants={fadeUp} initial="hidden" animate={isInView ? "visible" : "hidden"}>
           <h2 className="text-xl font-bold text-vaea-navy">New Section</h2>
         </motion.div>
       </div>
     );
   }
   ```

2. Add to `src/app/demo/page.tsx` in the section list.

3. Update the sidebar in `src/components/demo/DemoSidebar.tsx`:
   ```typescript
   const sections = [
     // ... existing sections
     { id: "my-section", icon: Star, label: "My Section", key: "9" },
   ];
   ```

## Adding an API Route

Create a route handler in `src/app/api/`:

```typescript
// src/app/api/my-endpoint/route.ts
import { NextResponse } from "next/server";

const FALLBACK = { status: "unknown", data: null };

export async function GET(): Promise<NextResponse> {
  const token = process.env.MY_API_TOKEN;

  const headers = {
    "Cache-Control": "public, s-maxage=60, stale-while-revalidate=120",
  };

  if (!token) {
    return NextResponse.json(FALLBACK, { headers });
  }

  try {
    // Fetch from external API
    const res = await fetch("https://api.example.com/data", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    return NextResponse.json(data, { headers });
  } catch {
    return NextResponse.json(FALLBACK, { headers });
  }
}
```

Add the env var to `.env.local.example` and document it.

## Component Patterns

### Animation Pattern
All visible sections use the same scroll-trigger pattern:
```typescript
const { ref, isInView } = useInView({ threshold: 0.1 });
// Wrap content in:
<motion.div variants={fadeUp} initial="hidden" animate={isInView ? "visible" : "hidden"}>
```

Available animation variants from `src/lib/animations.ts`:
- `fadeUp` — Fade in + slide up (most common)
- `fadeIn` — Simple fade
- `slideInLeft` / `slideInRight` — Horizontal slide
- `scaleIn` — Scale from 0.9 to 1
- `staggerContainer` — Parent for staggered children (0.1s delay)
- `staggerFast` — Faster stagger (0.05s delay)

### Data Pattern
Centralize data in `src/lib/sprint-data.ts` or `src/lib/epic-data.ts`, then import in components. Avoid hardcoding numbers that might change.

### Live Data Pattern
Use SWR for any data that should refresh:
```typescript
import useSWR from "swr";
const fetcher = (url: string) => fetch(url).then((r) => r.json());
const { data, error, isLoading } = useSWR("/api/my-endpoint", fetcher, {
  refreshInterval: 60000,
});
```
