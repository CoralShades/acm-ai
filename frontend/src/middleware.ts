import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const REDIRECTS: Record<string, string> = {
  '/sources': '/documents',
  '/advanced': '/settings',
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname in REDIRECTS) {
    return NextResponse.redirect(new URL(REDIRECTS[pathname], request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|brand|logo|icon).*)',
  ],
}