'use client'

import { useAuth } from '@/lib/hooks/use-auth'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { ModalProvider } from '@/components/providers/ModalProvider'
import { CreateDialogsProvider } from '@/lib/hooks/use-create-dialogs'
import { CopilotProvider } from '@/components/providers/CopilotProvider'
import { CommandPalette } from '@/components/common/CommandPalette'
import { KeyboardShortcutSheet } from '@/components/common/KeyboardShortcutSheet'
import { NavigationShortcuts } from '@/components/common/NavigationShortcuts'
import { OfflineBanner } from '@/components/common/OfflineBanner'
import { useAuthStore } from '@/lib/stores/auth-store'
import { toast } from 'sonner'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const [hasCheckedAuth, setHasCheckedAuth] = useState(false)
  const { authRequired, checkAuth } = useAuthStore()

  useEffect(() => {
    // Mark that we've completed the initial auth check
    if (!isLoading) {
      setHasCheckedAuth(true)

      // Redirect to login if not authenticated
      if (!isAuthenticated) {
        // Store the current path to redirect back after login
        const currentPath = window.location.pathname + window.location.search
        sessionStorage.setItem('redirectAfterLogin', currentPath)
        router.push('/login')
      }
    }
  }, [isAuthenticated, isLoading, router])

  // Periodic session validation (every 5 minutes)
  useEffect(() => {
    if (!isAuthenticated || authRequired === false) return

    const interval = setInterval(async () => {
      console.log('Checking session validity...')
      const valid = await checkAuth()

      if (!valid) {
        toast.warning('Session expired', {
          description: 'Your session has expired. Please log in again.',
          duration: Infinity,
          action: {
            label: 'Log In',
            onClick: () => {
              // Store current path for redirect after login
              sessionStorage.setItem('redirectAfterLogin', window.location.pathname)
              router.push('/login')
            },
          },
        })
      }
    }, 5 * 60 * 1000) // Check every 5 minutes

    return () => clearInterval(interval)
  }, [isAuthenticated, authRequired, checkAuth, router])

  // Check on window focus (tab activation)
  useEffect(() => {
    if (!isAuthenticated || authRequired === false) return

    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'visible') {
        console.log('Tab activated, checking session...')
        const valid = await checkAuth()

        if (!valid) {
          toast.warning('Session expired', {
            description: 'Your session expired while you were away. Please log in again.',
            duration: Infinity,
            action: {
              label: 'Log In',
              onClick: () => {
                sessionStorage.setItem('redirectAfterLogin', window.location.pathname)
                router.push('/login')
              },
            },
          })
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [isAuthenticated, authRequired, checkAuth, router])

  // Show loading spinner during initial auth check or while loading
  if (isLoading || !hasCheckedAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  // Don't render anything if not authenticated (during redirect)
  if (!isAuthenticated) {
    return null
  }

  return (
    <ErrorBoundary>
      <OfflineBanner />
      <CopilotProvider>
      <CreateDialogsProvider>
        <main id="main-content">
          {children}
        </main>
        <ModalProvider />
        <CommandPalette />
        <KeyboardShortcutSheet />
        <NavigationShortcuts />
      </CreateDialogsProvider>
      </CopilotProvider>
    </ErrorBoundary>
  )
}
