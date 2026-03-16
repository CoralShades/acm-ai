'use client';

import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { DashboardSkeleton } from '@/components/skeletons/DashboardSkeleton';
import { AppShell } from '@/components/layout/AppShell'
import { BentoGrid } from '@/components/ui/bento-grid';
import {
  BentoCard,
  BentoCardHeader,
  BentoCardTitle,
  BentoCardContent,
  BentoCardFooter,
  BentoCardIcon,
  BentoCardValue,
} from '@/components/ui/bento-card';
import { Button } from '@/components/ui/button';
import { useSources } from '@/lib/hooks/use-sources';
import { useACMSummary } from '@/lib/hooks/use-acm-summary';
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  Upload,
  TrendingUp,
  Clock,
  Building2,
  ClipboardList,
} from 'lucide-react';
import Link from 'next/link';
import { useCreateDialogs } from '@/lib/hooks/use-create-dialogs';
import { RiskChart } from '@/components/dashboard/RiskChart';
import { RecentSourcesList } from '@/components/dashboard/RecentSourcesList';

function DashboardPageContent() {
  const { data: sources, isLoading: sourcesLoading, error: sourcesError } = useSources();
  const { data: acmSummary, isLoading: acmLoading, error: acmError } = useACMSummary();
  const { openSourceDialog } = useCreateDialogs();

  const totalSources = sources?.length || 0;

  // Sort sources by created date (newest first) and take top 5
  const recentSources = sources
    ? [...sources]
        .sort((a, b) => {
          const dateA = a.created ? new Date(a.created).getTime() : 0;
          const dateB = b.created ? new Date(b.created).getTime() : 0;
          return dateB - dateA;
        })
        .slice(0, 5)
    : [];

  // Calculate recent activity (sources created in last 7 days)
  const recentActivityCount = sources
    ? sources.filter((s) => {
        if (!s.created) return false;
        const created = new Date(s.created);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return created > weekAgo;
      }).length
    : 0;

  // Document extraction stats
  const extracting = sources?.filter((s) => s.review_status === 'extracting').length ?? 0;
  const published = sources?.filter((s) => !s.review_status || s.review_status === 'published').length ?? 0;
  const totalBuildings = sources?.reduce((sum, s) => sum + (s.building_count ?? 0), 0) ?? 0;
  const totalRecords = sources?.reduce((sum, s) => sum + (s.insights_count ?? 0), 0) ?? 0;

  if (sourcesLoading || acmLoading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="flex h-full w-full max-w-none flex-col overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Your ACM compliance overview
        </p>
      </div>

      <BentoGrid columns={4} gap="md">
        {/* === Row 1: Document-centric stats (primary) === */}

        {/* Total Documents */}
        <BentoCard size="sm" isLoading={sourcesLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Total Documents</BentoCardTitle>
            <BentoCardIcon>
              <FileText className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            {sourcesError ? (
              <p className="text-sm text-destructive">Failed to load</p>
            ) : (
              <>
                <BentoCardValue>{totalSources}</BentoCardValue>
                <p className="text-sm text-muted-foreground mt-1">
                  {recentActivityCount > 0 ? `${recentActivityCount} added this week` : 'Uploaded'}
                </p>
              </>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* AI Extracted */}
        <BentoCard size="sm" isLoading={sourcesLoading}>
          <BentoCardHeader>
            <BentoCardTitle>AI Extracted</BentoCardTitle>
            <BentoCardIcon className="bg-emerald-100 text-emerald-600 dark:bg-emerald-900 dark:text-emerald-300">
              <CheckCircle className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <BentoCardValue className="text-emerald-600 dark:text-emerald-400">{published}</BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              {extracting > 0 ? `${extracting} in progress` : 'Completed'}
            </p>
          </BentoCardContent>
        </BentoCard>

        {/* Total Buildings */}
        <BentoCard size="sm" isLoading={sourcesLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Buildings</BentoCardTitle>
            <BentoCardIcon>
              <Building2 className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <BentoCardValue>{totalBuildings}</BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              Across all documents
            </p>
          </BentoCardContent>
        </BentoCard>

        {/* Total ACM Records */}
        <BentoCard size="sm" isLoading={sourcesLoading}>
          <BentoCardHeader>
            <BentoCardTitle>ACM Records</BentoCardTitle>
            <BentoCardIcon>
              <ClipboardList className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <BentoCardValue>{totalRecords}</BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              Items extracted
            </p>
          </BentoCardContent>
        </BentoCard>

        {/* === Row 2: Recent Uploads + Quick Actions (primary) === */}

        {/* Recent Uploads - Large */}
        <BentoCard size="lg" isLoading={sourcesLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Recent Uploads</BentoCardTitle>
            <BentoCardIcon>
              <Clock className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <RecentSourcesList sources={recentSources} />
          </BentoCardContent>
          <BentoCardFooter>
            <Link href="/jobs" className="text-sm text-primary hover:underline">
              View all jobs →
            </Link>
          </BentoCardFooter>
        </BentoCard>

        {/* Quick Actions */}
        <BentoCard size="md">
          <BentoCardHeader>
            <BentoCardTitle>Quick Actions</BentoCardTitle>
          </BentoCardHeader>
          <BentoCardContent className="space-y-3">
            <Button onClick={openSourceDialog} className="w-full justify-start">
              <Upload className="w-4 h-4 mr-2" />
              Upload New Document
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link href="/jobs">
                <ClipboardList className="w-4 h-4 mr-2" />
                View All Jobs
              </Link>
            </Button>
          </BentoCardContent>
        </BentoCard>

        {/* === Row 3: Risk profile (secondary priority) === */}

        {/* High Risk */}
        <BentoCard size="sm" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>High Risk</BentoCardTitle>
            <BentoCardIcon className="bg-danger-100 text-danger-600">
              <AlertTriangle className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            {acmError ? (
              <p className="text-sm text-destructive">Failed to load</p>
            ) : (
              <>
                <BentoCardValue className="text-danger-600">{acmSummary?.highRisk || 0}</BentoCardValue>
                <p className="text-sm text-muted-foreground mt-1">Require attention</p>
              </>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* Medium Risk */}
        <BentoCard size="sm" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Medium Risk</BentoCardTitle>
            <BentoCardIcon className="bg-warning-100 text-warning-600">
              <TrendingUp className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            {acmError ? (
              <p className="text-sm text-destructive">Failed to load</p>
            ) : (
              <>
                <BentoCardValue className="text-warning-600">{acmSummary?.mediumRisk || 0}</BentoCardValue>
                <p className="text-sm text-muted-foreground mt-1">Monitor regularly</p>
              </>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* Low Risk */}
        <BentoCard size="sm" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Low Risk</BentoCardTitle>
            <BentoCardIcon className="bg-success-100 text-success-600">
              <CheckCircle className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            {acmError ? (
              <p className="text-sm text-destructive">Failed to load</p>
            ) : (
              <>
                <BentoCardValue className="text-success-600">{acmSummary?.lowRisk || 0}</BentoCardValue>
                <p className="text-sm text-muted-foreground mt-1">In good condition</p>
              </>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* Risk Distribution Chart */}
        <BentoCard size="sm" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Risk Distribution</BentoCardTitle>
          </BentoCardHeader>
          <BentoCardContent>
            <RiskChart data={acmSummary} />
          </BentoCardContent>
        </BentoCard>
      </BentoGrid>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Dashboard"
          reloadUrl="/"
        />
      )}
    >
      <AppShell>
        <DashboardPageContent />
      </AppShell>
    </ErrorBoundary>
  )
}
