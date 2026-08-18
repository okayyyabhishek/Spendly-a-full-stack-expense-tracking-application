import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './components/ProtectedRoute'
import { ToastProvider } from './components/toast'
import { LoadingBlock } from './components/ui'
import { AuthProvider } from './features/auth/AuthContext'
import { AppLayout } from './layouts/AppLayout'

const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage').then((module) => ({ default: module.AnalyticsPage })))
const AuthPage = lazy(() => import('./pages/AuthPage').then((module) => ({ default: module.AuthPage })))
const BudgetsPage = lazy(() => import('./pages/BudgetsPage').then((module) => ({ default: module.BudgetsPage })))
const CategoriesPage = lazy(() => import('./pages/CategoriesPage').then((module) => ({ default: module.CategoriesPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })))
const RecurringPage = lazy(() => import('./pages/RecurringPage').then((module) => ({ default: module.RecurringPage })))
const TransactionsPage = lazy(() => import('./pages/TransactionsPage').then((module) => ({ default: module.TransactionsPage })))

export default function App() {
  return <BrowserRouter><AuthProvider><ToastProvider><Suspense fallback={<main className="route-loader"><LoadingBlock label="Loading your workspace…" /></main>}><Routes>
    <Route element={<ProtectedRoute />}><Route element={<AppLayout />}>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/transactions" element={<TransactionsPage />} />
      <Route path="/budgets" element={<BudgetsPage />} />
      <Route path="/recurring" element={<RecurringPage />} />
      <Route path="/analytics" element={<AnalyticsPage />} />
      <Route path="/categories" element={<CategoriesPage />} />
    </Route></Route>
    <Route path="/login" element={<AuthPage mode="login" />} />
    <Route path="/register" element={<AuthPage mode="register" />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></Suspense></ToastProvider></AuthProvider></BrowserRouter>
}
