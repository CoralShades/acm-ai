import { Fragment } from 'react'
import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  const hasHiddenMiddle = items.length > 2

  return (
    <nav aria-label="Breadcrumb" className={cn('flex', className)}>
      <ol className="flex items-center gap-1.5 text-sm">
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          const isMiddle = index > 0 && !isLast

          return (
            <Fragment key={index}>
              {/* Mobile ellipsis - inserted before last item when middle items hidden */}
              {isLast && hasHiddenMiddle && (
                <li className="flex md:hidden items-center gap-1.5" aria-hidden="true">
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />
                  <span className="text-muted-foreground">&hellip;</span>
                </li>
              )}

              <li
                className={cn(
                  'flex items-center gap-1.5',
                  isMiddle && hasHiddenMiddle && 'hidden md:flex'
                )}
              >
                {index > 0 && (
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />
                )}

                {item.href && !isLast ? (
                  <Link
                    href={item.href}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {item.label}
                  </Link>
                ) : (
                  <span
                    className={cn(
                      isLast
                        ? 'text-foreground font-medium truncate'
                        : 'text-muted-foreground'
                    )}
                    aria-current={isLast ? 'page' : undefined}
                  >
                    {item.label}
                  </span>
                )}
              </li>
            </Fragment>
          )
        })}
      </ol>
    </nav>
  )
}
