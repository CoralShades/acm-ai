'use client'

import { useAuthStore } from '@/lib/stores/auth-store'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export function useAuth() {
  const router = useRouter()
  const {
    isAuthenticated,
    isLoading,
    user,
    login,
    loginLegacy,
    logout,
    checkAuth,
    checkAuthRequired,
    fetchMe,
    error,
    hasHydrated,
    authRequired,
    authMode,
  } = useAuthStore()

  useEffect(() => {
    if (hasHydrated) {
      if (authRequired === null) {
        checkAuthRequired().then((required) => {
          if (required) {
            checkAuth()
          }
        }).catch(() => {})
      } else if (authRequired) {
        checkAuth()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasHydrated, authRequired])

  // Fetch user profile when authenticated in JWT mode
  useEffect(() => {
    if (isAuthenticated && authMode === 'jwt' && !user) {
      fetchMe()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, authMode])

  const handleLogin = async (emailOrPassword: string, password?: string) => {
    let success: boolean
    if (authMode === 'jwt' && password) {
      // JWT mode: email + password
      success = await login(emailOrPassword, password)
    } else {
      // Legacy mode: password only
      success = await loginLegacy(emailOrPassword)
    }

    if (success) {
      const redirectPath = sessionStorage.getItem('redirectAfterLogin')
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin')
        router.push(redirectPath)
      } else {
        router.push('/jobs')
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
    isLoading: isLoading || !hasHydrated,
    error,
    user,
    authMode,
    login: handleLogin,
    logout: handleLogout,
  }
}
