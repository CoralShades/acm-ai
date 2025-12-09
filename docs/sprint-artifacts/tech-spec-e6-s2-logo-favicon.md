# Tech Spec: E6-S2 - Create New Logo and Favicon

> **Story:** E6-S2
> **Epic:** Rebranding to ACM-AI
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Design and implement a professional logo and favicon for ACM-AI that conveys compliance, safety, and AI assistance.

---

## User Story

**As a** user
**I want** a professional logo for ACM-AI
**So that** the app looks polished

---

## Acceptance Criteria

- [ ] Logo designed (SVG format)
- [ ] Favicon created (multiple sizes)
- [ ] Logo used in header
- [ ] Favicon appears in browser tab

---

## Technical Design

### 1. Logo Design Concept

**Design Direction:**
- Clean, professional, compliance-focused
- Colors: Blue (trust, safety) + accent
- Shape: Shield or document icon with AI element
- Typography: Modern sans-serif

**Logo Variants:**
- Full logo (icon + text)
- Icon only (for small spaces)
- Monochrome (for dark/light modes)

### 2. SVG Logo Component

Create `frontend/src/components/brand/Logo.tsx`:

```tsx
interface LogoProps {
  variant?: 'full' | 'icon';
  className?: string;
}

export function Logo({ variant = 'full', className }: LogoProps) {
  if (variant === 'icon') {
    return (
      <svg
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
      >
        {/* Shield shape with document/data icon */}
        <path
          d="M16 2L4 7v9c0 8.4 5.12 16.24 12 18 6.88-1.76 12-9.6 12-18V7L16 2z"
          fill="currentColor"
          className="text-primary"
        />
        {/* AI circuit pattern */}
        <path
          d="M12 12h8M12 16h8M12 20h5"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <circle cx="22" cy="20" r="2" fill="white" />
      </svg>
    );
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Logo variant="icon" className="w-8 h-8" />
      <span className="font-semibold text-lg">ACM-AI</span>
    </div>
  );
}
```

### 3. Favicon Files

Generate favicon set in `frontend/public/`:

```
public/
  favicon.ico          # 16x16, 32x32, 48x48 (ICO format)
  icon.svg             # Vector favicon for modern browsers
  apple-touch-icon.png # 180x180 for iOS
  icon-192.png         # 192x192 for Android/PWA
  icon-512.png         # 512x512 for PWA splash
```

### 4. Favicon Meta Tags

Update `frontend/src/app/layout.tsx`:

```tsx
export const metadata: Metadata = {
  title: 'ACM-AI',
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: '32x32' },
      { url: '/icon.svg', type: 'image/svg+xml' },
    ],
    apple: '/apple-touch-icon.png',
  },
  manifest: '/manifest.json',
};
```

### 5. PWA Manifest

Create `frontend/public/manifest.json`:

```json
{
  "name": "ACM-AI",
  "short_name": "ACM-AI",
  "description": "AI-powered Asbestos Register Management",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### 6. Logo Generation Script (Optional)

Use a tool to generate favicons from SVG:

```bash
# Using sharp or similar
npx sharp-cli icon.svg -o favicon-16.png -w 16 -h 16
npx sharp-cli icon.svg -o favicon-32.png -w 32 -h 32
npx sharp-cli icon.svg -o apple-touch-icon.png -w 180 -h 180
npx sharp-cli icon.svg -o icon-192.png -w 192 -h 192
npx sharp-cli icon.svg -o icon-512.png -w 512 -h 512
```

Or use online tools:
- https://realfavicongenerator.net/
- https://favicon.io/

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/brand/Logo.tsx` | New - Logo component |
| `frontend/public/favicon.ico` | New/Replace |
| `frontend/public/icon.svg` | New |
| `frontend/public/apple-touch-icon.png` | New |
| `frontend/public/icon-192.png` | New |
| `frontend/public/icon-512.png` | New |
| `frontend/public/manifest.json` | New/Update |
| `frontend/src/app/layout.tsx` | Update icons metadata |

---

## Dependencies

- E6-S1: Application name update (for consistency)

---

## Testing

1. Load app - verify favicon in browser tab
2. Bookmark page - verify icon shows correctly
3. Add to home screen (mobile) - verify icon
4. Check logo in header at different sizes
5. Toggle dark mode - verify logo visibility
6. Check PWA manifest with Lighthouse

---

## Design Resources

Consider using:
- Figma/Sketch for logo design
- https://heroicons.com/ for icon inspiration
- https://realfavicongenerator.net/ for favicon generation

---

## Estimated Complexity

**Medium** - Requires design work and multiple file formats

---
