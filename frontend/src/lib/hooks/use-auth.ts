'use client'

import { useAuthStore } from '@/lib/stores/auth-store'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export function useAuth() {
  const router = useRouter()
  const {
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkAuth,
    checkAuthRequired,
    error,
    hasHydrated,
    authRequired
  } = useAuthStore()

  useEffect(() => {
    // Only check auth after the store has hydrated from localStorage
    if (hasHydrated) {
      if (authRequired === null) {
        // First visit or cleared storage — need to check if auth is required
        checkAuthRequired().then((required) => {
          if (required) {
            checkAuth()
          }
        })
      } else if (authRequired === false) {
        // Auth not required — ensure authenticated flag is set
        if (!isAuthenticated) {
          checkAuthRequired()
        }
      } else {
        // Auth is required — validate credentials (checkAuth skips if checked recently)
        checkAuth()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasHydrated])

  const handleLogin = async (password: string) => {
    const success = await login(password)
    if (success) {
      // Check if there's a stored redirect path
      const redirectPath = sessionStorage.getItem('redirectAfterLogin')
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin')
        router.push(redirectPath)
      } else {
        router.push('/notebooks')
      }
    }
    return success
  }

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return {
    isAuthenticated,
    isLoading: isLoading || !hasHydrated, // Treat lack of hydration as loading
    error,
    login: handleLogin,
    logout: handleLogout
  }
}