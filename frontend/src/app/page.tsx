import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Logo } from '@/components/brand/Logo'
import {
  FileText,
  TableProperties,
  MessageSquare,
  Shield,
  Upload,
  ArrowRight,
} from 'lucide-react'
import Link from 'next/link'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <div className="flex justify-center mb-6">
          <Logo variant="full" className="text-4xl" iconClassName="w-12 h-12" />
        </div>

        <h1 className="text-4xl font-bold tracking-tight mb-4">
          AI-Powered ACM Register Analysis
        </h1>

        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
          Upload your SAMP documents and instantly extract, analyze, and manage
          Asbestos Containing Material data with AI assistance.
        </p>

        <div className="flex gap-4 justify-center flex-wrap">
          <Button size="lg" asChild>
            <Link href="/sources">
              <Upload className="w-5 h-5 mr-2" />
              Upload Your First Document
            </Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link href="/notebooks">
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
  )
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType
  title: string
  description: string
}) {
  return (
    <Card className="p-6">
      <Icon className="w-10 h-10 text-primary mb-4" />
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </Card>
  )
}

function QuickStartStep({
  number,
  title,
  description,
}: {
  number: number
  title: string
  description: string
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
  )
}
