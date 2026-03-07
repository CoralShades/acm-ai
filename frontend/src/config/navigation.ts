import {
  LayoutDashboard,
  Search,
  Bot,
  FileWarning,
  ClipboardList,
  FlaskConical,
  FileCode,
  Cog,
  SlidersHorizontal,
  Activity,
  BookOpen,
  Podcast,
  Wand2,
  Layers,
  ListChecks,
  House,
  BookText,
} from 'lucide-react'
import { MARKETING_DOCS_URL, MARKETING_URL } from '@/lib/site-urls'

export interface NavItem {
  name: string
  href: string
  icon: React.ElementType
  badge?: string
  external?: boolean
  /** Hide this item when ACM mode is active */
  hideInAcm?: boolean
  /** Only show this item when ACM mode is active */
  acmOnly?: boolean
}

export interface NavGroup {
  title: string
  items: NavItem[]
}

/**
 * Full navigation configuration. Items marked `hideInAcm` are hidden in ACM-focused mode.
 * Items marked `acmOnly` are only visible in ACM mode.
 */
export const navigationConfig: NavGroup[] = [
  {
    title: 'Workspace',
    items: [
      { name: 'Dashboard', href: '/', icon: LayoutDashboard },
      { name: 'Jobs', href: '/jobs', icon: ClipboardList },
      { name: 'ACM Register', href: '/acm', icon: FileWarning, acmOnly: true },
      { name: 'Notebooks', href: '/notebooks', icon: BookOpen, hideInAcm: true },
      { name: 'Podcasts', href: '/podcasts', icon: Podcast, hideInAcm: true },
      { name: 'Transformations', href: '/transformations', icon: Wand2, hideInAcm: true },
      { name: 'Search', href: '/search', icon: Search },
      { name: 'Visit Landing', href: MARKETING_URL, icon: House, external: true },
      { name: 'Documentation', href: MARKETING_DOCS_URL, icon: BookText, external: true },
    ],
  },
  {
    title: 'Configure',
    items: [
      { name: 'Extraction Monitor', href: '/extraction-monitor', icon: Activity, acmOnly: true },
      { name: 'Extraction', href: '/settings/extraction', icon: FlaskConical, acmOnly: true },
      { name: 'AI Models', href: '/settings/models', icon: Bot },
      { name: 'Parsers', href: '/settings/parsers', icon: FileCode },
      { name: 'Field Schema', href: '/settings/field-schema', icon: ListChecks, acmOnly: true },
      { name: 'Processing', href: '/settings/processing', icon: Cog },
      { name: 'General', href: '/settings', icon: SlidersHorizontal },
    ],
  },
  {
    title: 'Advanced',
    items: [
      { name: 'Advanced', href: '/advanced', icon: Layers, hideInAcm: true },
    ],
  },
]

/**
 * Filter navigation based on ACM mode. Removes hidden items and empty groups.
 */
export function getFilteredNavigation(isAcmMode: boolean): NavGroup[] {
  return navigationConfig
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => {
        if (isAcmMode && item.hideInAcm) return false
        if (!isAcmMode && item.acmOnly) return false
        return true
      }),
    }))
    .filter((group) => group.items.length > 0)
}
