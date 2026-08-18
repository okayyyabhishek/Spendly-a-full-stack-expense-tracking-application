import { apiDownload, apiRequest } from './client'
import type {
  AppNotification,
  Budget,
  Category,
  CategoryAnalysis,
  DashboardSummary,
  FinancialMetrics,
  MonthlySummary,
  NotificationPage,
  RecurringTransaction,
  TimeAnalysis,
  Transaction,
  TransactionPage,
} from '../types/api'

const queryString = (params: Record<string, string | number | undefined | null>) => {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value))
  })
  const value = query.toString()
  return value ? `?${value}` : ''
}

export const getCategories = (type?: string) => apiRequest<Category[]>(`/categories${queryString({ type })}`)
export const createCategory = (payload: object) => apiRequest<Category>('/categories', { method: 'POST', body: payload })
export const updateCategory = (id: number, payload: object) => apiRequest<Category>(`/categories/${id}`, { method: 'PUT', body: payload })
export const deleteCategory = (id: number) => apiRequest<void>(`/categories/${id}`, { method: 'DELETE' })

export const getTransactions = (params: Record<string, string | number | undefined | null>) =>
  apiRequest<TransactionPage>(`/transactions${queryString(params)}`)
export const createTransaction = (payload: object) => apiRequest<Transaction>('/transactions', { method: 'POST', body: payload })
export const updateTransaction = (id: number, payload: object) => apiRequest<Transaction>(`/transactions/${id}`, { method: 'PUT', body: payload })
export const deleteTransaction = (id: number) => apiRequest<void>(`/transactions/${id}`, { method: 'DELETE' })

export const getBudgets = (month: number, year: number) => apiRequest<Budget[]>(`/budgets${queryString({ month, year })}`)
export const createBudget = (payload: object) => apiRequest<Budget>('/budgets', { method: 'POST', body: payload })
export const updateBudget = (id: number, payload: object) => apiRequest<Budget>(`/budgets/${id}`, { method: 'PUT', body: payload })
export const deleteBudget = (id: number) => apiRequest<void>(`/budgets/${id}`, { method: 'DELETE' })

export const getRecurring = () => apiRequest<RecurringTransaction[]>('/recurring')
export const createRecurring = (payload: object) => apiRequest<RecurringTransaction>('/recurring', { method: 'POST', body: payload })
export const updateRecurring = (id: number, payload: object) => apiRequest<RecurringTransaction>(`/recurring/${id}`, { method: 'PUT', body: payload })
export const deleteRecurring = (id: number) => apiRequest<void>(`/recurring/${id}`, { method: 'DELETE' })

export const getDashboard = (month: number, year: number) => apiRequest<DashboardSummary>(`/analytics/summary${queryString({ month, year })}`)
export const getCategoryAnalysis = (from_date?: string, to_date?: string) =>
  apiRequest<CategoryAnalysis[]>(`/analytics/categories${queryString({ from_date, to_date })}`)
export const getMonthlyAnalysis = (months: number) => apiRequest<TimeAnalysis[]>(`/analytics/monthly${queryString({ months })}`)
export const getMetrics = () => apiRequest<FinancialMetrics>('/analytics/metrics')
export const getMonthlySummary = (month: number, year: number) =>
  apiRequest<MonthlySummary>(`/analytics/monthly-summary${queryString({ month, year })}`)

export const getNotifications = () => apiRequest<NotificationPage>('/notifications')
export const markNotificationRead = (id: number) => apiRequest<AppNotification>(`/notifications/${id}/read`, { method: 'PATCH' })
export const markAllNotificationsRead = () => apiRequest<void>('/notifications/mark-all-read', { method: 'POST' })

export const downloadExport = (format: 'csv' | 'pdf', params: Record<string, string | number | undefined | null>) =>
  apiDownload(`/export/${format}${queryString(params)}`)
