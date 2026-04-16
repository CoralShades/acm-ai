'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { apiClient } from '@/lib/api/client'
import { useAuth } from '@/lib/hooks/use-auth'
import { toast } from 'sonner'
import {
  Users,
  Plus,
  Pencil,
  KeyRound,
  UserX,
  UserCheck,
  Shield,
  AlertCircle,
} from 'lucide-react'

interface UserRecord {
  id: string
  email: string
  username: string
  role: 'admin' | 'user'
  status: 'active' | 'inactive'
  name?: string
  created_at?: string
  last_login?: string
}

export default function UsersSettingsPage() {
  return (
    <ErrorBoundary
      fallback={(props: { error?: Error; resetError: () => void }) => (
        <PageErrorFallback {...props} pageName="User Management" reloadUrl="/settings/users" />
      )}
    >
      <UsersContent />
    </ErrorBoundary>
  )
}

function UsersContent() {
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuth()
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<UserRecord | null>(null)
  const [resetPasswordUser, setResetPasswordUser] = useState<UserRecord | null>(null)
  const [deactivateUser, setDeactivateUser] = useState<UserRecord | null>(null)
  const [reactivateUser, setReactivateUser] = useState<UserRecord | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const res = await apiClient.get('/auth/admin/users')
      return res.data as { users: UserRecord[]; total: number }
    },
  })

  const users = data?.users ?? []

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-4xl space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">User Management</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Create and manage user accounts
              </p>
            </div>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add User
            </Button>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <Users className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Users</CardTitle>
                  <CardDescription>
                    {data ? `${data.total} registered user${data.total !== 1 ? 's' : ''}` : 'Loading...'}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading && (
                <div className="text-sm text-muted-foreground py-8 text-center">Loading users...</div>
              )}
              {error && (
                <div className="flex items-center gap-2 text-red-600 text-sm py-4">
                  <AlertCircle className="h-4 w-4" />
                  <span>Failed to load users. Make sure you have admin access.</span>
                </div>
              )}
              {!isLoading && !error && users.length === 0 && (
                <div className="text-sm text-muted-foreground py-8 text-center">No users found.</div>
              )}
              {users.length > 0 && (
                <div className="space-y-1">
                  {/* Header */}
                  <div className="grid grid-cols-[1fr_1fr_80px_80px_140px] gap-3 px-3 py-2 text-xs font-medium text-muted-foreground border-b">
                    <div>User</div>
                    <div>Email</div>
                    <div>Role</div>
                    <div>Status</div>
                    <div className="text-right">Actions</div>
                  </div>
                  {/* Rows */}
                  {users.map((u) => (
                    <div
                      key={u.id}
                      className="grid grid-cols-[1fr_1fr_80px_80px_140px] gap-3 px-3 py-2.5 items-center text-sm hover:bg-muted/50 rounded-md"
                    >
                      <div>
                        <div className="font-medium flex items-center gap-1.5">
                          {u.name || u.username}
                          {u.id === currentUser?.id && (
                            <Badge variant="outline" className="text-[10px] px-1 py-0">you</Badge>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">@{u.username}</div>
                      </div>
                      <div className="text-muted-foreground truncate">{u.email}</div>
                      <div>
                        <Badge variant={u.role === 'admin' ? 'default' : 'secondary'} className="text-xs">
                          {u.role === 'admin' && <Shield className="h-3 w-3 mr-1" />}
                          {u.role}
                        </Badge>
                      </div>
                      <div>
                        <Badge
                          variant={u.status === 'active' ? 'outline' : 'destructive'}
                          className="text-xs"
                        >
                          {u.status}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          title="Edit user"
                          onClick={() => setEditUser(u)}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          title="Reset password"
                          onClick={() => setResetPasswordUser(u)}
                        >
                          <KeyRound className="h-3.5 w-3.5" />
                        </Button>
                        {u.id !== currentUser?.id && (
                          u.status === 'active' ? (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-red-600 hover:text-red-700"
                              title="Deactivate user"
                              onClick={() => setDeactivateUser(u)}
                            >
                              <UserX className="h-3.5 w-3.5" />
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-green-600 hover:text-green-700"
                              title="Reactivate user"
                              onClick={() => setReactivateUser(u)}
                            >
                              <UserCheck className="h-3.5 w-3.5" />
                            </Button>
                          )
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Dialogs */}
      <CreateUserDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['admin-users'] })}
      />
      <EditUserDialog
        user={editUser}
        onOpenChange={(open) => !open && setEditUser(null)}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['admin-users'] })}
      />
      <ResetPasswordDialog
        user={resetPasswordUser}
        onOpenChange={(open) => !open && setResetPasswordUser(null)}
      />
      <DeactivateDialog
        user={deactivateUser}
        onOpenChange={(open) => !open && setDeactivateUser(null)}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['admin-users'] })}
      />
      <ReactivateDialog
        user={reactivateUser}
        onOpenChange={(open) => !open && setReactivateUser(null)}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['admin-users'] })}
      />
    </AppShell>
  )
}

// ─── Create User Dialog ──────────────────────────────────────────

function CreateUserDialog({
  open,
  onOpenChange,
  onSuccess,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'admin' | 'user'>('user')

  const mutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/auth/admin/users', {
        name: name || undefined,
        email,
        username,
        password,
        role,
      })
      return res.data
    },
    onSuccess: () => {
      toast.success('User created successfully')
      onOpenChange(false)
      resetForm()
      onSuccess()
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to create user')
    },
  })

  const resetForm = () => {
    setName('')
    setEmail('')
    setUsername('')
    setPassword('')
    setRole('user')
  }

  const handleClose = (open: boolean) => {
    if (!open) resetForm()
    onOpenChange(open)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create New User</DialogTitle>
          <DialogDescription>Add a new user account to the system.</DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            mutation.mutate()
          }}
          className="space-y-4"
        >
          <div className="space-y-1.5">
            <label htmlFor="create-name" className="text-sm font-medium">Display Name</label>
            <Input
              id="create-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              disabled={mutation.isPending}
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="create-email" className="text-sm font-medium">Email *</label>
            <Input
              id="create-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              required
              disabled={mutation.isPending}
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="create-username" className="text-sm font-medium">Username *</label>
            <Input
              id="create-username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="johndoe"
              required
              disabled={mutation.isPending}
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="create-password" className="text-sm font-medium">Password *</label>
            <Input
              id="create-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 chars, mixed case + number"
              required
              disabled={mutation.isPending}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Role</label>
            <Select value={role} onValueChange={(v) => setRole(v as 'admin' | 'user')}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user">User</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={mutation.isPending || !email.trim() || !username.trim() || !password.trim()}
            >
              {mutation.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Edit User Dialog ────────────────────────────────────────────

function EditUserDialog({
  user,
  onOpenChange,
  onSuccess,
}: {
  user: UserRecord | null
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}) {
  const [role, setRole] = useState<'admin' | 'user'>('user')
  const [name, setName] = useState('')
  const open = !!user

  useEffect(() => {
    if (user) {
      setRole(user.role)
      setName(user.name || '')
    }
  }, [user])

  const mutation = useMutation({
    mutationFn: async () => {
      if (!user) return
      const res = await apiClient.patch(`/auth/admin/users/${user.id}`, {
        role,
        name: name || undefined,
      })
      return res.data
    },
    onSuccess: () => {
      toast.success('User updated successfully')
      onOpenChange(false)
      onSuccess()
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to update user')
    },
  })

  const handleClose = (open: boolean) => {
    if (!open) {
      setRole('user')
      setName('')
    }
    onOpenChange(open)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit User</DialogTitle>
          <DialogDescription>
            Update details for {user?.email}
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            mutation.mutate()
          }}
          className="space-y-4"
        >
          <div className="space-y-1.5">
            <label htmlFor="edit-name" className="text-sm font-medium">Display Name</label>
            <Input
              id="edit-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={mutation.isPending}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Role</label>
            <Select value={role} onValueChange={(v) => setRole(v as 'admin' | 'user')}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user">User</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Reset Password Dialog ───────────────────────────────────────

function ResetPasswordDialog({
  user,
  onOpenChange,
}: {
  user: UserRecord | null
  onOpenChange: (open: boolean) => void
}) {
  const [newPassword, setNewPassword] = useState('')

  const mutation = useMutation({
    mutationFn: async () => {
      if (!user) return
      const res = await apiClient.post(`/auth/admin/users/${user.id}/reset-password`, {
        new_password: newPassword,
      })
      return res.data
    },
    onSuccess: () => {
      toast.success('Password reset successfully')
      onOpenChange(false)
      setNewPassword('')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to reset password')
    },
  })

  const handleClose = (open: boolean) => {
    if (!open) setNewPassword('')
    onOpenChange(open)
  }

  return (
    <Dialog open={!!user} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reset Password</DialogTitle>
          <DialogDescription>
            Set a new password for {user?.email}
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            mutation.mutate()
          }}
          className="space-y-4"
        >
          <div className="space-y-1.5">
            <label htmlFor="reset-password" className="text-sm font-medium">New Password</label>
            <Input
              id="reset-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Min 8 chars, mixed case + number"
              required
              disabled={mutation.isPending}
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending || !newPassword.trim()}>
              {mutation.isPending ? 'Resetting...' : 'Reset Password'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Deactivate / Reactivate Dialogs ─────────────────────────────

function DeactivateDialog({
  user,
  onOpenChange,
  onSuccess,
}: {
  user: UserRecord | null
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}) {
  const mutation = useMutation({
    mutationFn: async () => {
      if (!user) return
      await apiClient.delete(`/auth/admin/users/${user.id}`)
    },
    onSuccess: () => {
      toast.success('User deactivated')
      onOpenChange(false)
      onSuccess()
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to deactivate user')
    },
  })

  return (
    <ConfirmDialog
      open={!!user}
      onOpenChange={onOpenChange}
      title="Deactivate User"
      description={`Are you sure you want to deactivate ${user?.email}? They will be immediately logged out and unable to sign in.`}
      confirmText="Deactivate"
      confirmVariant="destructive"
      onConfirm={() => mutation.mutate()}
      isLoading={mutation.isPending}
    />
  )
}

function ReactivateDialog({
  user,
  onOpenChange,
  onSuccess,
}: {
  user: UserRecord | null
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}) {
  const mutation = useMutation({
    mutationFn: async () => {
      if (!user) return
      await apiClient.patch(`/auth/admin/users/${user.id}`, { status: 'active' })
    },
    onSuccess: () => {
      toast.success('User reactivated')
      onOpenChange(false)
      onSuccess()
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail || 'Failed to reactivate user')
    },
  })

  return (
    <ConfirmDialog
      open={!!user}
      onOpenChange={onOpenChange}
      title="Reactivate User"
      description={`Reactivate ${user?.email}? They will be able to sign in again.`}
      confirmText="Reactivate"
      onConfirm={() => mutation.mutate()}
      isLoading={mutation.isPending}
    />
  )
}
