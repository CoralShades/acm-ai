'use client';

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

export default function DashboardPage() {
  const { data: sources, isLoading: sourcesLoading } = useSources();
  const { data: acmSummary, isLoading: acmLoading } = useACMSummary();

  const totalSources = sources?.length || 0;
  const recentSources = sources?.slice(0, 5) || [];

  return (
    <div className="p-6">
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
            <BentoCardValue>{totalSources}</BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              Documents uploaded
            </p>
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
            <BentoCardValue className="text-danger-600">
              {acmSummary?.highRisk || 0}
            </BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              Require attention
            </p>
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
            <BentoCardValue className="text-warning-600">
              {acmSummary?.mediumRisk || 0}
            </BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              Monitor regularly
            </p>
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
            <BentoCardValue className="text-success-600">
              {acmSummary?.lowRisk || 0}
            </BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              In good condition
            </p>
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
              <Link href="/sources">
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
