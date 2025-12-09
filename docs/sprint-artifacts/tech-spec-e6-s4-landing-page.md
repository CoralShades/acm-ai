# Tech Spec: E6-S4 - Update Landing/Home Page

> **Story:** E6-S4
> **Epic:** Rebranding to ACM-AI
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Redesign the landing/home page to explain ACM-AI's purpose and guide new users to upload their first document.

---

## User Story

**As a** new user
**I want** to understand what ACM-AI does
**So that** I can start using it effectively

---

## Acceptance Criteria

- [ ] Hero section explains ACM-AI purpose
- [ ] Key features listed
- [ ] Quick start instructions visible
- [ ] Call-to-action to upload first document

---

## Technical Design

### 1. Landing Page Structure

Update `frontend/src/app/page.tsx`:

```tsx
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Logo } from '@/components/brand/Logo';
import {
  FileText,
  TableProperties,
  MessageSquare,
  Shield,
  Upload,
  ArrowRight,
} from 'lucide-react';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Logo variant="full" className="justify-center mb-6 text-4xl" />

        <h1 className="text-4xl font-bold tracking-tight mb-4">
          AI-Powered ACM Register Analysis
        </h1>

        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
          Upload your SAMP documents and instantly extract, analyze, and manage
          Asbestos Containing Material data with AI assistance.
        </p>

        <div className="flex gap-4 justify-center">
          <Button size="lg" asChild>
            <Link href="/sources/new">
              <Upload className="w-5 h-5 mr-2" />
              Upload Your First Document
            </Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link href="/dashboard">
              View Dashboard
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-2xl font-bold text-center mb-12">
          Everything You Need for ACM Compliance
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <FeatureCard
            icon={FileText}
            title="Smart Extraction"
            description="Automatically extract ACM register data from PDF documents using AI-powered table recognition."
          />
          <FeatureCard
            icon={TableProperties}
            title="Interactive Spreadsheet"
            description="View, sort, filter, and search your ACM data in a powerful spreadsheet interface."
          />
          <FeatureCard
            icon={MessageSquare}
            title="AI Chat Assistant"
            description="Ask natural questions about your ACM data and get instant, cited answers."
          />
          <FeatureCard
            icon={Shield}
            title="Risk Visualization"
            description="Quickly identify high-risk items with color-coded risk status indicators."
          />
        </div>
      </section>

      {/* Quick Start Section */}
      <section className="container mx-auto px-4 py-16">
        <Card className="p-8 bg-primary/5 border-primary/20">
          <h2 className="text-2xl font-bold mb-6">Quick Start</h2>
          <ol className="space-y-4">
            <QuickStartStep
              number={1}
              title="Upload your SAMP document"
              description="Drag and drop your PDF or click to browse"
            />
            <QuickStartStep
              number={2}
              title="Enable ACM extraction"
              description="Toggle on ACM extraction during upload"
            />
            <QuickStartStep
              number={3}
              title="View extracted data"
              description="See your ACM register in the spreadsheet view"
            />
            <QuickStartStep
              number={4}
              title="Ask questions"
              description="Use the AI chat to query your data"
            />
          </ol>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 text-center text-muted-foreground">
        <p>ACM-AI - AI-powered asbestos compliance management</p>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) {
  return (
    <Card className="p-6">
      <Icon className="w-10 h-10 text-primary mb-4" />
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </Card>
  );
}

function QuickStartStep({
  number,
  title,
  description,
}: {
  number: number;
  title: string;
  description: string;
}) {
  return (
    <li className="flex items-start gap-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
        {number}
      </div>
      <div>
        <p className="font-medium">{title}</p>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </li>
  );
}
```

### 2. Dashboard Redirect for Logged-in Users

If user has existing sources, redirect to dashboard:

```tsx
// In page.tsx or middleware
import { redirect } from 'next/navigation';

export default async function LandingPage() {
  // Check if user has sources
  const sources = await getSources();
  if (sources.length > 0) {
    redirect('/dashboard');
  }

  return <LandingContent />;
}
```

### 3. Empty State for Dashboard

When dashboard has no data, show welcome:

```tsx
// frontend/src/app/(dashboard)/page.tsx
export default function DashboardPage() {
  const { data: sources, isLoading } = useSources();

  if (isLoading) return <Loading />;

  if (!sources?.length) {
    return <EmptyDashboard />;
  }

  return <DashboardContent sources={sources} />;
}

function EmptyDashboard() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
      <FileText className="w-16 h-16 text-muted-foreground mb-4" />
      <h2 className="text-2xl font-bold mb-2">No Documents Yet</h2>
      <p className="text-muted-foreground mb-6">
        Upload your first SAMP document to get started
      </p>
      <Button asChild>
        <Link href="/sources/new">
          <Upload className="w-5 h-5 mr-2" />
          Upload Document
        </Link>
      </Button>
    </div>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/page.tsx` | Redesign landing page |
| `frontend/src/app/(dashboard)/page.tsx` | Add empty state |

---

## Dependencies

- E6-S1: Application name (for consistent branding)
- E6-S2: Logo (for hero section)
- E6-S3: Color theme (for styling)

---

## Testing

1. Visit app as new user - verify landing page shows
2. Check hero section content
3. Verify feature cards are visible
4. Click "Upload" button - verify navigation
5. Test responsive layout on mobile
6. Verify empty dashboard shows upload prompt

---

## Estimated Complexity

**Low** - Static content page with simple components

---
