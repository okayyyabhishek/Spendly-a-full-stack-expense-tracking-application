export type TransactionType = 'income' | 'expense'
export type PaymentMethod = 'cash' | 'upi' | 'credit_card' | 'debit_card' | 'bank_transfer' | 'other'
export type Frequency = 'daily' | 'weekly' | 'monthly' | 'yearly'

export interface User {
  id: number
  name: string
  email: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export interface Category {
  id: number
  name: string
  type: TransactionType
  color: string | null
  icon: string | null
  created_at: string
}

export interface Transaction {
  id: number
  type: TransactionType
  amount: string
  category_id: number
  category: Category
  description: string | null
  payment_method: PaymentMethod
  transaction_date: string
  recurring_transaction_id: number | null
  created_at: string
  updated_at: string
}

export interface TransactionPage {
  items: Transaction[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface Budget {
  id: number
  amount: string
  month: number
  year: number
  category: Category | null
  spent: string
  remaining: string
  percent_used: string
  status: 'on_track' | 'warning' | 'exceeded'
  created_at: string
}

export interface RecurringTransaction {
  id: number
  type: TransactionType
  amount: string
  category_id: number
  category: Category
  description: string | null
  payment_method: PaymentMethod
  frequency: Frequency
  start_date: string
  end_date: string | null
  next_due_date: string
  active: boolean
  created_at: string
  updated_at: string
}

export interface DashboardSummary {
  total_balance: string
  total_income: string
  total_expenses: string
  current_month_spending: string
  remaining_monthly_budget: string | null
  monthly_income: string
  monthly_expenses: string
  monthly_savings: string
  budget_utilization: string | null
}

export interface CategoryAnalysis {
  category_id: number
  category_name: string
  color: string | null
  amount: string
  percentage: string
}

export interface TimeAnalysis {
  period: string
  income: string
  expenses: string
  net: string
}

export interface FinancialMetrics {
  total_income: string
  total_expenses: string
  net_balance: string
  average_daily_spending: string
  average_monthly_spending: string
  highest_spending_category: string | null
  highest_individual_expense: string
  savings_rate: string
}

export interface MonthlySummary {
  month: number
  year: number
  total_income: string
  total_expenses: string
  savings: string
  budget_utilization: string | null
  spending_change_percent: string | null
  top_categories: CategoryAnalysis[]
  biggest_transactions: Array<{
    id: number
    description: string | null
    category_name: string
    amount: string
    transaction_date: string
  }>
}

export interface AppNotification {
  id: number
  kind: 'budget_warning' | 'budget_exceeded' | 'recurring_due' | 'monthly_summary'
  title: string
  body: string | null
  is_read: boolean
  created_at: string
}

export interface NotificationPage {
  items: AppNotification[]
  unread_count: number
}
