export interface User {
  id: string
  email: string
  username: string
  role: 'admin' | 'user'
  name: string
}

export interface AuthState {
  isAuthenticated: boolean
  token: string | null
  user: User | null
  isLoading: boolean
  error: string | null
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}
