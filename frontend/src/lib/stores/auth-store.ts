import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { getApiUrl } from '@/lib/config'
import type { User } from '@/lib/types/auth'

interface AuthState {
  isAuthenticated: boolean
  token: string | null
  user: User | null
  isLoading: boolean
  error: string | null
  lastAuthCheck: number | null
  isCheckingAuth: boolean
  hasHydrated: boolean
  authRequired: boolean | null
  authMode: 'legacy' | 'jwt' | 'none' | null
  setHasHydrated: (state: boolean) => void
  checkAuthRequired: () => Promise<boolean>
  login: (email: string, password: string) => Promise<boolean>
  loginLegacy: (password: string) => Promise<boolean>
  logout: () => void
  checkAuth: () => Promise<boolean>
  fetchMe: () => Promise<void>
}

function setCookie(name: string, value: string, days: number) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
}

function deleteCookie(name: string) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      token: null,
      user: null,
      isLoading: false,
      error: null,
      lastAuthCheck: null,
      isCheckingAuth: false,
      hasHydrated: false,
      authRequired: null,
      authMode: null,

      setHasHydrated: (state: boolean) => {
        set({ hasHydrated: state })
      },

      checkAuthRequired: async () => {
        try {
          const apiUrl = await getApiUrl()
          const response = await fetch(`${apiUrl}/api/auth/status`, {
            cache: 'no-store',
          })

          if (!response.ok) {
            throw new Error(`Auth status check failed: ${response.status}`)
          }

          const data = await response.json()
          const required = data.auth_enabled || false
          const mode = data.mode || 'none'
          set({ authRequired: required, authMode: mode })

          if (!required) {
            set({ isAuthenticated: true, token: 'not-required', user: null })
          }

          return required
        } catch (error) {
          console.error('Failed to check auth status:', error)

          if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
            set({
              error: 'Unable to connect to server. Please check if the API is running.',
              authRequired: null,
            })
          } else {
            set({ authRequired: true })
          }
          throw error
        }
      },

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const apiUrl = await getApiUrl()
          const response = await fetch(`${apiUrl}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          })

          if (response.ok) {
            const data = await response.json()
            // Sync token to cookie for Next.js middleware
            setCookie('acm_token', data.token, 1)
            set({
              isAuthenticated: true,
              token: data.token,
              user: data.user,
              isLoading: false,
              lastAuthCheck: Date.now(),
              error: null,
            })
            return true
          } else {
            const errorData = await response.json().catch(() => ({}))
            set({
              error: errorData.detail || 'Invalid email or password',
              isLoading: false,
              isAuthenticated: false,
              token: null,
              user: null,
            })
            return false
          }
        } catch (error) {
          console.error('Login error:', error)
          set({
            error: error instanceof TypeError && error.message.includes('Failed to fetch')
              ? 'Unable to connect to server.'
              : 'An unexpected error occurred',
            isLoading: false,
            isAuthenticated: false,
            token: null,
            user: null,
          })
          return false
        }
      },

      loginLegacy: async (password: string) => {
        set({ isLoading: true, error: null })
        try {
          const apiUrl = await getApiUrl()
          const response = await fetch(`${apiUrl}/api/notebooks`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${password}`,
              'Content-Type': 'application/json',
            },
          })

          if (response.ok) {
            setCookie('acm_token', password, 1)
            set({
              isAuthenticated: true,
              token: password,
              user: null,
              isLoading: false,
              lastAuthCheck: Date.now(),
              error: null,
            })
            return true
          } else {
            set({
              error: response.status === 401 ? 'Invalid password.' : `Authentication failed (${response.status})`,
              isLoading: false,
              isAuthenticated: false,
              token: null,
              user: null,
            })
            return false
          }
        } catch (error) {
          console.error('Legacy login error:', error)
          set({
            error: 'Unable to connect to server.',
            isLoading: false,
            isAuthenticated: false,
            token: null,
            user: null,
          })
          return false
        }
      },

      logout: () => {
        deleteCookie('acm_token')
        set({
          isAuthenticated: false,
          token: null,
          user: null,
          error: null,
        })
      },

      fetchMe: async () => {
        const { token } = get()
        if (!token || token === 'not-required') return
        try {
          const apiUrl = await getApiUrl()
          const response = await fetch(`${apiUrl}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` },
          })
          if (response.ok) {
            const user = await response.json()
            set({ user })
          }
        } catch {
          // Non-fatal — user info is optional
        }
      },

      checkAuth: async () => {
        const state = get()
        const { token, lastAuthCheck, isCheckingAuth, isAuthenticated } = state

        if (isCheckingAuth) return isAuthenticated
        if (!token) return false

        const now = Date.now()
        if (isAuthenticated && lastAuthCheck && (now - lastAuthCheck) < 30000) {
          return true
        }

        set({ isCheckingAuth: true })

        try {
          const apiUrl = await getApiUrl()
          // Use /auth/me for JWT mode, /notebooks for legacy
          const endpoint = state.authMode === 'jwt' ? '/api/auth/me' : '/api/notebooks'
          const response = await fetch(`${apiUrl}${endpoint}`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          })

          if (response.ok) {
            set({
              isAuthenticated: true,
              lastAuthCheck: now,
              isCheckingAuth: false,
            })
            return true
          } else {
            deleteCookie('acm_token')
            set({
              isAuthenticated: false,
              token: null,
              user: null,
              lastAuthCheck: null,
              isCheckingAuth: false,
            })
            return false
          }
        } catch (error) {
          console.error('checkAuth error:', error)
          deleteCookie('acm_token')
          set({
            isAuthenticated: false,
            token: null,
            user: null,
            lastAuthCheck: null,
            isCheckingAuth: false,
          })
          return false
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        isAuthenticated: state.isAuthenticated,
        authRequired: state.authRequired,
        authMode: state.authMode,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
        // Sync token to cookie on rehydrate
        if (state?.token && state.token !== 'not-required') {
          setCookie('acm_token', state.token, 1)
        }
      },
    }
  )
)
