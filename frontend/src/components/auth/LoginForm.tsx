'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/hooks/use-auth'
import { useAuthStore } from '@/lib/stores/auth-store'
import { getConfig } from '@/lib/config'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, Shield } from 'lucide-react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { BRANDING } from '@/config/branding'

export function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, isLoading, error, authMode } = useAuth()
  const { authRequired, checkAuthRequired, hasHydrated, isAuthenticated } = useAuthStore()
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [configInfo, setConfigInfo] = useState<{ apiUrl: string; version: string; buildTime: string } | null>(null)
  const router = useRouter()

  const isJwtMode = authMode === 'jwt'

  useEffect(() => {
    getConfig().then(cfg => {
      setConfigInfo({
        apiUrl: cfg.apiUrl,
        version: cfg.version,
        buildTime: cfg.buildTime,
      })
    }).catch(err => {
      console.error('Failed to load config:', err)
    })
  }, [])

  useEffect(() => {
    if (!hasHydrated) return

    const checkAuth = async () => {
      try {
        const required = await checkAuthRequired()
        if (!required) {
          const savedPath = sessionStorage.getItem('redirectAfterLogin')
          if (savedPath) {
            sessionStorage.removeItem('redirectAfterLogin')
            router.push(savedPath)
          } else {
            router.push('/jobs')
          }
        }
      } catch {
        // On error, assume auth is required
      } finally {
        setIsCheckingAuth(false)
      }
    }

    if (authRequired !== null) {
      if (!authRequired && isAuthenticated) {
        const savedPath = sessionStorage.getItem('redirectAfterLogin')
        if (savedPath) {
          sessionStorage.removeItem('redirectAfterLogin')
          router.push(savedPath)
        } else {
          router.push('/jobs')
        }
      } else {
        setIsCheckingAuth(false)
      }
    } else {
      void checkAuth()
    }
  }, [hasHydrated, authRequired, checkAuthRequired, router, isAuthenticated])

  if (!hasHydrated || isCheckingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingSpinner />
      </div>
    )
  }

  if (authRequired === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Connection Error</CardTitle>
            <CardDescription>Unable to connect to the API server</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-2 text-red-600 text-sm">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  {error || 'Unable to connect to server. Please check if the API is running.'}
                </div>
              </div>
              {configInfo && (
                <div className="space-y-2 text-xs text-muted-foreground border-t pt-3">
                  <div className="font-medium">Diagnostic Information:</div>
                  <div className="space-y-1 font-mono">
                    <div>Version: {configInfo.version}</div>
                    <div>Built: {new Date(configInfo.buildTime).toLocaleString()}</div>
                    <div className="break-all">API URL: {configInfo.apiUrl}</div>
                  </div>
                </div>
              )}
              <Button onClick={() => window.location.reload()} className="w-full">
                Retry Connection
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (isJwtMode) {
      if (email.trim() && password.trim()) {
        await login(email, password)
      }
    } else {
      if (password.trim()) {
        await login(password)
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-muted/30 p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Branding header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold tracking-tight">{BRANDING.name}</h1>
          </div>
          <p className="text-sm text-muted-foreground">
            {BRANDING.tagline}
          </p>
        </div>

        <Card className="border-border/50 shadow-lg">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-lg">Sign in to your account</CardTitle>
            <CardDescription>
              {isJwtMode
                ? 'Enter your email and password to continue'
                : 'Enter your password to access the application'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {isJwtMode && (
                <div className="space-y-1.5">
                  <label htmlFor="email" className="text-sm font-medium">
                    Email
                  </label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    autoComplete="email"
                    autoFocus
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="current-password"
                  autoFocus={!isJwtMode}
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 dark:bg-red-950/20 rounded-md p-2.5">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={
                  isLoading ||
                  !password.trim() ||
                  (isJwtMode && !email.trim())
                }
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            {configInfo && (
              <div className="text-xs text-center text-muted-foreground pt-4 mt-4 border-t">
                <div>v{configInfo.version}</div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          {BRANDING.footer.vendor}
        </p>
      </div>
    </div>
  )
}
