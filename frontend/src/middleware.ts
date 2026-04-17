import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const REDIRECTS: Record<string, string> = {
  '/sources': '/documents',
  '/advanced': '/settings',
  '/models': '/settings/models',
}

const PUBLIC_PATHS = ['/login', '/config']

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl

  // Handle legacy redirects first
  if (pathname in REDIRECTS) {
    return NextResponse.redirect(new URL(`${REDIRECTS[pathname]}${search}`, request.url))
  }

  // Skip public paths (login page, config bootstrap route)
  if (PUBLIC_PATHS.includes(pathname)) {
    return NextResponse.next()
  }

  // Check for auth token in cookie (synced from localStorage by auth store)
  const token = request.cookies.get('acm_token')?.value

  if (!token) {
    const loginUrl = new URL('/login', request.url)
    if (pathname !== '/') {
      loginUrl.searchParams.set('redirect', pathname)
    }
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|brand|logo|icon).*)',
  ],
}
