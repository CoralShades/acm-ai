'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/hooks/use-auth'
import { useSidebarStore } from '@/lib/stores/sidebar-store'
import { Logo } from '@/components/brand/Logo'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import { Separator } from '@/components/ui/separator'
import { VendorAttribution } from '@/components/brand/VendorAttribution'
import { UserMenu } from '@/components/auth/UserMenu'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  LogOut,
  ChevronLeft,
  ChevronDown,
  Menu,
  Upload,
  Command,
  Settings,
  ExternalLink,
} from 'lucide-react'
import { getFilteredNavigation, getConfigureItems, type NavGroup } from '@/config/navigation'
import { MARKETING_URL, MARKETING_DOCS_URL } from '@/lib/site-urls'
import { useCreateDialogs } from '@/lib/hooks/use-create-dialogs'

const isAcmMode = process.env.NEXT_PUBLIC_ACM_MODE !== 'false'

export function AppSidebar() {
  const pathname = usePathname()
  const { logout, user, authMode } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isJwtMode = authMode === 'jwt'
  const { isCollapsed, expandedSections, toggleCollapse, toggleSection } =
    useSidebarStore()
  const router = useRouter()
  const { openSourceDialog } = useCreateDialogs()

  const [isMac, setIsMac] = useState(true) // Default to Mac for SSR

  const navigation = useMemo(() => getFilteredNavigation(isAcmMode), [])
  const configureItems = useMemo(() => getConfigureItems(isAcmMode), [])

  // Detect platform for keyboard shortcut display
  useEffect(() => {
    setIsMac(navigator.userAgent.toLowerCase().includes('mac'))
  }, [])

  // Check if a nav item is active (exact match for root, prefix match for others)
  const isItemActive = (item: { href: string; external?: boolean }) =>
    item.external ? false : item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)

  // Check if any item in a section is active
  const isSectionActive = (section: NavGroup) =>
    section.items.some((item) => isItemActive(item))

  return (
    <TooltipProvider delayDuration={0}>
      <div
        data-testid="app-sidebar"
        className={cn(
          'app-sidebar flex h-full flex-col bg-sidebar border-sidebar-border border-r transition-all duration-300',
          isCollapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Header with Logo */}
        <div
          className={cn(
            'flex h-16 items-center group border-b border-sidebar-border/50',
            isCollapsed ? 'justify-center px-2' : 'justify-between px-4'
          )}
        >
          {isCollapsed ? (
            <div className="relative flex items-center justify-center w-full">
              <Logo
                variant="icon"
                iconClassName="w-8 h-8 transition-opacity group-hover:opacity-0"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleCollapse}
                className="absolute text-sidebar-foreground hover:bg-sidebar-accent opacity-0 group-hover:opacity-100 transition-opacity"
                aria-label="Expand sidebar"
              >
                <Menu className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <>
              <Logo variant="full" className="text-sidebar-foreground" />
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleCollapse}
                className="text-sidebar-foreground hover:bg-sidebar-accent"
                aria-label="Collapse sidebar"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>

        <nav
          className={cn(
            'flex-1 overflow-y-auto py-4',
            isCollapsed ? 'px-2' : 'px-3'
          )}
        >
          {/* Upload Document button - directly opens AddSourceDialog */}
          <div className={cn('mb-4', isCollapsed ? 'px-0' : 'px-0')}>
            {isCollapsed ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    onClick={openSourceDialog}
                    variant="default"
                    size="sm"
                    className="w-full justify-center px-2 bg-primary hover:bg-primary/90 text-primary-foreground border-0"
                    aria-label="Upload Document"
                  >
                    <Upload className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">Upload Document</TooltipContent>
              </Tooltip>
            ) : (
              <Button
                onClick={openSourceDialog}
                variant="default"
                size="sm"
                className="w-full justify-start bg-primary hover:bg-primary/90 text-primary-foreground border-0"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Document
              </Button>
            )}
          </div>

          <Separator className="my-2" />

          {/* Navigation Sections with Collapsible Groups */}
          {navigation
            .filter((section) => section.title !== 'Configure')
            .map((section, index) => {
            const isExpanded = expandedSections[section.title] ?? true
            const hasActiveItem = isSectionActive(section)

            return (
              <div key={section.title}>
                {index > 0 && <Separator className="my-2" />}

                {isCollapsed ? (
                  // Collapsed mode: show items directly with tooltips
                  <div className="space-y-1">
                    {section.items.map((item) => {
                      const isActive = isItemActive(item)
                      return (
                        <Tooltip key={item.name}>
                          <TooltipTrigger asChild>
                            <Link
                              href={item.href}
                              target={item.external ? '_blank' : undefined}
                              rel={item.external ? 'noopener noreferrer' : undefined}
                              className={item.animated ? 'group/ai-editor' : undefined}
                            >
                              <Button
                                variant={isActive ? 'secondary' : 'ghost'}
                                className={cn(
                                  'w-full justify-center px-2 text-sidebar-foreground',
                                  isActive &&
                                    'bg-sidebar-accent text-sidebar-accent-foreground'
                                )}
                                aria-label={item.name}
                              >
                                <item.icon className={cn(
                                  'h-4 w-4',
                                  item.animated && 'transition-transform duration-500 ease-in-out group-hover/ai-editor:rotate-12 group-hover/ai-editor:scale-110'
                                )} />
                              </Button>
                            </Link>
                          </TooltipTrigger>
                          <TooltipContent side="right">
                            {item.name}
                          </TooltipContent>
                        </Tooltip>
                      )
                    })}
                  </div>
                ) : (
                  // Expanded mode: show collapsible sections
                  <Collapsible
                    open={isExpanded}
                    onOpenChange={() => toggleSection(section.title)}
                  >
                    <CollapsibleTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className={cn(
                          'w-full justify-between px-3 py-1.5 h-auto text-xs font-semibold uppercase tracking-wider',
                          hasActiveItem
                            ? 'text-sidebar-foreground'
                            : 'text-sidebar-foreground/60 hover:text-sidebar-foreground'
                        )}
                      >
                        <span>{section.title}</span>
                        <ChevronDown
                          className={cn(
                            'h-3 w-3 transition-transform duration-200',
                            isExpanded && 'rotate-180'
                          )}
                        />
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="space-y-1 pt-1">
                      {section.items.map((item) => {
                        const isActive = isItemActive(item)
                        return (
                          <Link
                            key={item.name}
                            href={item.href}
                            target={item.external ? '_blank' : undefined}
                            rel={item.external ? 'noopener noreferrer' : undefined}
                            className={item.animated ? 'group/ai-editor' : undefined}
                          >
                            <Button
                              variant={isActive ? 'secondary' : 'ghost'}
                              className={cn(
                                'w-full justify-start gap-3 text-sidebar-foreground',
                                isActive &&
                                  'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                              )}
                            >
                              <item.icon className={cn(
                                'h-4 w-4',
                                item.animated && 'transition-transform duration-500 ease-in-out group-hover/ai-editor:rotate-12 group-hover/ai-editor:scale-110'
                              )} />
                              <span>{item.name}</span>
                              {item.badge && (
                                <span className="ml-auto text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded-full">
                                  {item.badge}
                                </span>
                              )}
                            </Button>
                          </Link>
                        )
                      })}
                    </CollapsibleContent>
                  </Collapsible>
                )}
              </div>
            )
          })}
        </nav>

        {/* Footer */}
        <div
          className={cn(
            'border-t border-sidebar-border p-3 space-y-2',
            isCollapsed && 'px-2'
          )}
        >
          {/* Vendor Attribution */}
          {!isCollapsed && <VendorAttribution className="mb-1" />}

          {/* Command Palette hint */}
          {!isCollapsed && (
            <div className="px-3 py-1.5 text-xs text-sidebar-foreground/60 rounded-md bg-sidebar-accent/30">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <Command className="h-3 w-3" />
                  Quick actions
                </span>
                <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                  {isMac ? <span className="text-xs">⌘</span> : <span>Ctrl+</span>}
                  K
                </kbd>
              </div>
              <p className="mt-1 text-[10px] text-sidebar-foreground/40">
                Navigation, search, ask, theme
              </p>
            </div>
          )}

          {/* User Menu (JWT mode) */}
          {isJwtMode && <UserMenu collapsed={isCollapsed} />}

          {/* Settings Dropdown — shown for admins or non-JWT mode */}
          {(!isJwtMode || isAdmin) && (
            <>
              {isCollapsed ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      className="w-full justify-center"
                      onClick={() => router.push('/settings')}
                      aria-label="Settings"
                    >
                      <Settings className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">Settings</TooltipContent>
                </Tooltip>
              ) : (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-full justify-start gap-3"
                    >
                      <Settings className="h-4 w-4" />
                      Settings
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" side="top" className="w-56">
                    {configureItems.map((item) => (
                      <DropdownMenuItem key={item.name} asChild>
                        <Link href={item.href} className="flex items-center gap-2">
                          <item.icon className="h-4 w-4" />
                          {item.name}
                        </Link>
                      </DropdownMenuItem>
                    ))}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <div className="flex items-center gap-2">
                        <ThemeToggle />
                      </div>
                    </DropdownMenuItem>
                    {!isJwtMode && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={logout}
                          className="text-destructive focus:text-destructive"
                        >
                          <LogOut className="h-4 w-4 mr-2" />
                          Sign Out
                        </DropdownMenuItem>
                      </>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </>
          )}

          {/* Footer links */}
          {!isCollapsed && (
            <div className="flex items-center justify-center gap-3 pt-1 text-[10px] text-sidebar-foreground/40">
              <a href={MARKETING_URL} target="_blank" rel="noopener noreferrer" className="flex items-center gap-0.5 hover:text-sidebar-foreground/60 transition-colors">
                VAEA
                <ExternalLink className="h-2.5 w-2.5" />
              </a>
              <span>·</span>
              <a href={MARKETING_DOCS_URL} target="_blank" rel="noopener noreferrer" className="flex items-center gap-0.5 hover:text-sidebar-foreground/60 transition-colors">
                Docs
                <ExternalLink className="h-2.5 w-2.5" />
              </a>
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  )
}
