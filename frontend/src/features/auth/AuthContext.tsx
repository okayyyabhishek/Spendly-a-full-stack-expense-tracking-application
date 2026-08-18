import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

import * as authApi from '../../api/auth'
import { ApiError } from '../../api/client'
import type { User } from '../../types/api'

interface AuthContextValue {
  user: User | null
  isReady: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (name: string, email: string, password: string, confirmPassword: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)
const TOKEN_KEY = 'pulse_ledger_token'
const USER_KEY = 'pulse_ledger_user'

function persistSession(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem(USER_KEY)
      return saved ? (JSON.parse(saved) as User) : null
    } catch {
      clearSession()
      return null
    }
  })
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setIsReady(true)
      return
    }
    void authApi
      .getMe()
      .then((profile) => {
        persistSession(token, profile)
        setUser(profile)
      })
      .catch(() => {
        clearSession()
        setUser(null)
      })
      .finally(() => setIsReady(true))
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isReady,
      async signIn(email, password) {
        const response = await authApi.login({ email, password })
        persistSession(response.access_token, response.user)
        setUser(response.user)
      },
      async signUp(name, email, password, confirmPassword) {
        const response = await authApi.register({ name, email, password, confirm_password: confirmPassword })
        persistSession(response.access_token, response.user)
        setUser(response.user)
      },
      async signOut() {
        try {
          await authApi.logout()
        } catch (error) {
          if (!(error instanceof ApiError) || error.status !== 401) throw error
        } finally {
          clearSession()
          setUser(null)
        }
      },
    }),
    [isReady, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider.')
  return context
}
