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
  Search,
  TrendingUp,
  Clock,
  ExternalLink,
} from 'lucide-react';
import Link from 'next/link';
import { RiskChart } from '@/components/dashboard/RiskChart';
import { RecentSourcesList } from '@/components/dashboard/RecentSourcesList';

function DashboardPageContent() {
  const { data: sources, isLoading: sourcesLoading, error: sourcesError } = useSources();
  const { data: acmSummary, isLoading: acmLoading, error: acmError } = useACMSummary();

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
        {/* Total Sources - Small */}
        <BentoCard size="sm" isLoading={sourcesLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Total Sources</BentoCardTitle>
            <BentoCardIcon>
              <FileText className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            {sourcesError ? (
              <p className="text-sm text-destructive">Failed to load sources</p>
            ) : (
              <>
                <BentoCardValue>{totalSources}</BentoCardValue>
                <p className="text-sm text-muted-foreground mt-1">
                  {recentActivityCount > 0
                    ? `${recentActivityCount} added this week`
                    : 'Documents uploaded'}
                </p>
              </>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* High Risk Count - Small */}
        <BentoCard size="sm" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>High Risk Items</BentoCardTitle>
            <BentoCardIcon className="bg-danger-100 text-danger-600">
              <AlertTriangle className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            {acmError ? (
              <p className="text-sm text-destructive">Failed to load</p>
            ) : (
              <>
                <BentoCardValue className="text-danger-600">
                  {acmSummary?.highRisk || 0}
                </BentoCardValue>
                <p className="text-sm text-muted-foreground mt-1">
                  Require attention
                </p>
              </>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* Medium Risk Count - Small */}
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
                <BentoCardValue className="text-warning-600">
                  {acmSummary?.mediumRisk || 0}
                </BentoCardValue>
                <p className="text-sm text-muted-foreground mt-1">
                  Monitor regularly
                </p>
              </>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* Low Risk Count - Small */}
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
                <BentoCardValue className="text-success-600">
                  {acmSummary?.lowRisk || 0}
                </BentoCardValue>
                <p className="text-sm text-muted-foreground mt-1">
                  In good condition
                </p>
              </>
            )}
          </BentoCardContent>
        </BentoCard>

        {/* Risk Distribution Chart - Large */}
        <BentoCard size="lg" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Risk Distribution</BentoCardTitle>
          </BentoCardHeader>
          <BentoCardContent>
            <RiskChart data={acmSummary} />
          </BentoCardContent>
          <BentoCardFooter>
            <Link href="/acm" className="text-sm text-primary hover:underline">
              View all ACM data &rarr;
            </Link>
          </BentoCardFooter>
        </BentoCard>

        {/* Recent Uploads - Medium */}
        <BentoCard size="md" isLoading={sourcesLoading}>
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
            <Link href="/sources" className="text-sm text-primary hover:underline">
              View all sources &rarr;
            </Link>
          </BentoCardFooter>
        </BentoCard>

        {/* Quick Actions - Medium */}
        <BentoCard size="md">
          <BentoCardHeader>
            <BentoCardTitle>Quick Actions</BentoCardTitle>
          </BentoCardHeader>
          <BentoCardContent className="space-y-3">
            <Button asChild className="w-full justify-start">
              <Link href="/sources?action=upload">
                <Upload className="w-4 h-4 mr-2" />
                Upload New Document
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link href="/sources">
                <Search className="w-4 h-4 mr-2" />
                Search Sources
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link href="/acm">
                <ExternalLink className="w-4 h-4 mr-2" />
                View ACM Register
              </Link>
            </Button>
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
