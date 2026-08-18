import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { LoadingBlock } from './ui'
import { useAuth } from '../features/auth/AuthContext'

export function ProtectedRoute() {
  const { user, isReady } = useAuth()
  const location = useLocation()
  if (!isReady) return <main className="route-loader"><LoadingBlock label="Opening your secure ledger…" /></main>
  return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location }} />
}
