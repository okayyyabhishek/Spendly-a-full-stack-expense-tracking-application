import { ArrowDownRight, ArrowUpRight, CreditCard, Plus, ReceiptText, Wallet } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { getCategoryAnalysis, getDashboard, getMonthlyAnalysis, getTransactions } from '../api/ledger'
import { ApiError } from '../api/client'
import { Button, Card, EmptyState, ErrorNotice, LoadingBlock, PageHeader, Progress } from '../components/ui'
import { TransactionModal } from '../features/transactions/TransactionModal'
import type { CategoryAnalysis, DashboardSummary, TimeAnalysis, Transaction } from '../types/api'
import { compactMoney, displayDate, money, toMonthLabel } from '../utils/format'

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [categories, setCategories] = useState<CategoryAnalysis[]>([])
  const [series, setSeries] = useState<TimeAnalysis[]>([])
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modalType, setModalType] = useState<'income' | 'expense' | null>(null)

  const load = useCallback(() => {
    setIsLoading(true); setError(null)
    const now = new Date()
    void Promise.all([getDashboard(now.getMonth() + 1, now.getFullYear()), getCategoryAnalysis(), getMonthlyAnalysis(6), getTransactions({ page: 1, page_size: 5 })])
      .then(([dashboard, categoryData, timeData, transactions]) => { setSummary(dashboard); setCategories(categoryData); setSeries(timeData); setRecentTransactions(transactions.items) })
      .catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : 'We could not load your financial overview.'))
      .finally(() => setIsLoading(false))
  }, [])
  useEffect(load, [load])

  if (isLoading) return <LoadingBlock label="Calculating your financial picture…" />
  if (error || !summary) return <ErrorNotice message={error ?? 'Your dashboard is unavailable.'} onRetry={load} />

  const chartData = series.map((item) => ({ ...item, label: toMonthLabel(item.period), income: Number(item.income), expenses: Number(item.expenses) }))
  const pieData = categories.map((item) => ({ ...item, amount: Number(item.amount) }))
  return <>
    <PageHeader eyebrow="YOUR OVERVIEW" title="Money, with momentum." description="A live read of what is coming in, going out, and still in your corner." action={<div className="quick-actions"><Button onClick={() => setModalType('expense')}><Plus size={17} /> Add expense</Button><Button variant="secondary" onClick={() => setModalType('income')}><Plus size={17} /> Add income</Button></div>} />
    <section className="balance-hero"><div><p>Available balance</p><h2>{money(summary.total_balance)}</h2><span><ArrowUpRight size={15} /> {money(summary.monthly_savings)} saved this month</span></div><div className="balance-hero__orb" aria-hidden="true" /></section>
    <section className="stat-grid">
      <Stat icon={<ArrowUpRight size={19} />} label="Total income" value={money(summary.total_income)} detail={`${money(summary.monthly_income)} this month`} tone="income" />
      <Stat icon={<ArrowDownRight size={19} />} label="Total expenses" value={money(summary.total_expenses)} detail={`${money(summary.current_month_spending)} this month`} tone="expense" />
      <Stat icon={<Wallet size={19} />} label="Monthly budget" value={summary.remaining_monthly_budget === null ? 'Not set' : money(summary.remaining_monthly_budget)} detail={summary.budget_utilization === null ? 'Set a budget to track it' : `${summary.budget_utilization}% used`} tone="neutral" />
    </section>
    <section className="dashboard-grid dashboard-grid--charts">
      <Card className="chart-card"><div className="card-heading"><div><p className="eyebrow">CASH FLOW</p><h2>Income & spending</h2></div><span>Last 6 months</span></div>{chartData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData} margin={{ top: 8, right: 6, left: -20, bottom: 0 }}><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#7A847E', fontSize: 12 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#7A847E', fontSize: 12 }} tickFormatter={(value) => compactMoney(value)} /><Tooltip formatter={(value) => money(Number(value))} contentStyle={{ borderRadius: 14, border: '1px solid #E2E7DE', boxShadow: '0 10px 30px rgba(27,36,31,.08)' }} /><Legend iconType="circle" /><Line type="monotone" dataKey="income" stroke="#73A847" strokeWidth={3} dot={false} /><Line type="monotone" dataKey="expenses" stroke="#E26F59" strokeWidth={3} dot={false} /></LineChart></ResponsiveContainer></div> : <ChartEmpty />}</Card>
      <Card className="chart-card"><div className="card-heading"><div><p className="eyebrow">SPENDING MIX</p><h2>Where it went</h2></div></div>{pieData.length ? <div className="pie-layout"><div className="pie-wrap"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={pieData} dataKey="amount" nameKey="category_name" innerRadius="62%" outerRadius="88%" paddingAngle={4}>{pieData.map((item) => <Cell key={item.category_id} fill={item.color ?? '#8E9A91'} />)}</Pie><Tooltip formatter={(value) => money(Number(value))} /></PieChart></ResponsiveContainer></div><div className="category-key">{categories.slice(0, 4).map((item) => <div key={item.category_id}><span style={{ background: item.color ?? '#8E9A91' }} /><p>{item.category_name}</p><strong>{item.percentage}%</strong></div>)}</div></div> : <ChartEmpty />}</Card>
    </section>
    <section className="dashboard-grid dashboard-grid--lower">
      <Card><div className="card-heading"><div><p className="eyebrow">BUDGET STATUS</p><h2>This month</h2></div></div>{summary.budget_utilization === null ? <div className="inline-empty"><CreditCard size={19} /><p>Set an overall budget to watch your monthly pace.</p></div> : <><div className="budget-number"><strong>{summary.budget_utilization}%</strong><span>of your budget used</span></div><Progress value={Number(summary.budget_utilization)} status={Number(summary.budget_utilization) > 100 ? 'exceeded' : Number(summary.budget_utilization) >= 80 ? 'warning' : 'on_track'} /><p className="budget-caption">{money(summary.remaining_monthly_budget)} remains this month.</p></>}</Card>
      <Card className="recent-card"><div className="card-heading"><div><p className="eyebrow">RECENT ACTIVITY</p><h2>Latest transactions</h2></div><a href="/transactions">See all</a></div>{recentTransactions.length ? <div className="recent-list">{recentTransactions.map((transaction) => <div className="recent-row" key={transaction.id}><span className={`category-dot category-dot--${transaction.type}`} style={{ background: transaction.category.color ?? undefined }} /><div><strong>{transaction.description || transaction.category.name}</strong><p>{transaction.category.name} · {displayDate(transaction.transaction_date)}</p></div><b className={transaction.type === 'income' ? 'amount-income' : 'amount-expense'}>{transaction.type === 'income' ? '+' : '−'}{money(transaction.amount)}</b></div>)}</div> : <EmptyState icon={<ReceiptText size={23} />} title="No activity yet" body="Your newest transactions will appear here." />}</Card>
    </section>
    {modalType && <TransactionModal initialType={modalType} onClose={() => setModalType(null)} onSaved={() => { setModalType(null); load() }} />}
  </>
}

function Stat({ icon, label, value, detail, tone }: { icon: React.ReactNode; label: string; value: string; detail: string; tone: 'income' | 'expense' | 'neutral' }) { return <Card className="stat-card"><span className={`stat-card__icon stat-card__icon--${tone}`}>{icon}</span><p>{label}</p><strong>{value}</strong><small>{detail}</small></Card> }
function ChartEmpty() { return <div className="chart-empty">Your charts will take shape as you add transactions.</div> }
