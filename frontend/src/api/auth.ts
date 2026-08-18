import { apiRequest } from './client'
import type { AuthResponse, User } from '../types/api'

export const register = (payload: { name: string; email: string; password: string; confirm_password: string }) =>
  apiRequest<AuthResponse>('/auth/register', { method: 'POST', body: payload, authenticated: false })

export const login = (payload: { email: string; password: string }) =>
  apiRequest<AuthResponse>('/auth/login', { method: 'POST', body: payload, authenticated: false })

export const logout = () => apiRequest<void>('/auth/logout', { method: 'POST' })

export const getMe = () => apiRequest<User>('/auth/me')
