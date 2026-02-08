'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

/**
 * Redirect /sources to /documents.
 * The full sources page was merged into /documents as part of E14-S7.
 * This client-side redirect complements the middleware redirect for
 * cases where Next.js client-side navigation bypasses middleware.
 */
export default function SourcesPage() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/documents')
  }, [router])

  return null
}
