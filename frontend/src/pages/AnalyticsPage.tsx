import { BarChart3, FileSpreadsheet, FileText, TrendingDown, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Bar, BarChart, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { downloadExport, getCategoryAnalysis, getMetrics, getMonthlyAnalysis, getMonthlySummary } from '../api/ledger'
import { ApiError } from '../api/client'
import { Button, Card, EmptyState, ErrorNotice, LoadingBlock, PageHeader } from '../components/ui'
import { useToast } from '../components/toast'
import type { CategoryAnalysis, FinancialMetrics, MonthlySummary, TimeAnalysis } from '../types/api'
import { compactMoney, currentMonthValue, displayDate, downloadBlob, money, toMonthLabel } from '../utils/format'

export function AnalyticsPage() {
  const { showToast } = useToast()
  const [monthValue, setMonthValue] = useState(currentMonthValue())
  const [metrics, setMetrics] = useState<FinancialMetrics | null>(null)
  const [categories, setCategories] = useState<CategoryAnalysis[]>([])
  const [series, setSeries] = useState<TimeAnalysis[]>([])
  const [summary, setSummary] = useState<MonthlySummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState<'csv' | 'pdf' | null>(null)
  const [year, month] = monthValue.split('-').map(Number)
  const load = () => { setIsLoading(true); setError(null); const from = `${monthValue}-01`; const to = new Date(year, month, 0).toISOString().slice(0, 10); void Promise.all([getMetrics(), getCategoryAnalysis(from, to), getMonthlyAnalysis(6), getMonthlySummary(month, year)]).then(([nextMetrics, nextCategories, nextSeries, nextSummary]) => { setMetrics(nextMetrics); setCategories(nextCategories); setSeries(nextSeries); setSummary(nextSummary) }).catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : 'Could not calculate insights right now.')).finally(() => setIsLoading(false)) }
  useEffect(load, [month, year, monthValue])
  async function exportData(format: 'csv' | 'pdf') { setExporting(format); try { const from_date = `${monthValue}-01`; const to_date = new Date(year, month, 0).toISOString().slice(0, 10); const file = await downloadExport(format, { from_date, to_date }); downloadBlob(file, `spendly-${monthValue}.${format}`); showToast(`${format.toUpperCase()} report downloaded.`) } catch (requestError) { showToast(requestError instanceof ApiError ? requestError.message : 'Could not download your report.', 'error') } finally { setExporting(null) } }
  if (isLoading) return <LoadingBlock label="Turning your ledger into insights…" />
  if (error || !metrics || !summary) return <ErrorNotice message={error ?? 'Insights are unavailable.'} onRetry={load} />
  const chartData = series.map((point) => ({ ...point, label: toMonthLabel(point.period), income: Number(point.income), expenses: Number(point.expenses) }))
  const pieData = categories.map((category) => ({ ...category, amount: Number(category.amount) }))
  return <>
    <PageHeader eyebrow="MONEY INTELLIGENCE" title="The story behind the spend." description="Real patterns from your ledger, ready when you are." action={<div className="quick-actions"><Button variant="secondary" loading={exporting === 'csv'} onClick={() => void exportData('csv')}><FileSpreadsheet size={17} /> CSV</Button><Button variant="secondary" loading={exporting === 'pdf'} onClick={() => void exportData('pdf')}><FileText size={17} /> PDF report</Button></div>} />
    <div className="period-picker"><label><span>Insight month</span><input type="month" value={monthValue} onChange={(event) => setMonthValue(event.target.value)} /></label></div>
    <section className="metric-grid"><Metric label="Average daily spend" value={money(metrics.average_daily_spending)} icon={<TrendingDown size={19} />} /><Metric label="Average monthly spend" value={money(metrics.average_monthly_spending)} icon={<BarChart3 size={19} />} /><Metric label="Savings rate" value={`${metrics.savings_rate}%`} icon={<TrendingUp size={19} />} /><Metric label="Highest expense" value={money(metrics.highest_individual_expense)} icon={<TrendingDown size={19} />} /></section>
    <section className="dashboard-grid dashboard-grid--charts"><Card className="chart-card"><div className="card-heading"><div><p className="eyebrow">MONTHLY FLOW</p><h2>Income vs expenses</h2></div><span>6 months</span></div>{chartData.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartData} margin={{ top: 8, right: 5, left: -20 }}><XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#7A847E', fontSize: 12 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#7A847E', fontSize: 12 }} tickFormatter={(value) => compactMoney(value)} /><Tooltip formatter={(value) => money(Number(value))} contentStyle={{ borderRadius: 14, border: '1px solid #E2E7DE' }} /><Legend iconType="circle" /><Bar dataKey="income" fill="#73A847" radius={[5, 5, 0, 0]} /><Bar dataKey="expenses" fill="#E26F59" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></div> : <ChartEmpty />}</Card><Card className="chart-card"><div className="card-heading"><div><p className="eyebrow">SELECTED MONTH</p><h2>Spending by category</h2></div></div>{pieData.length ? <div className="pie-layout"><div className="pie-wrap"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={pieData} dataKey="amount" nameKey="category_name" innerRadius="62%" outerRadius="88%" paddingAngle={4}>{pieData.map((item) => <Cell key={item.category_id} fill={item.color ?? '#8E9A91'} />)}</Pie><Tooltip formatter={(value) => money(Number(value))} /></PieChart></ResponsiveContainer></div><div className="category-key">{categories.slice(0, 5).map((item) => <div key={item.category_id}><span style={{ background: item.color ?? '#8E9A91' }} /><p>{item.category_name}</p><strong>{item.percentage}%</strong></div>)}</div></div> : <ChartEmpty />}</Card></section>
    <section className="insight-summary"><Card><div className="card-heading"><div><p className="eyebrow">{new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric' }).format(new Date(year, month - 1)).toUpperCase()}</p><h2>Monthly summary</h2></div></div><div className="summary-amounts"><div><span>Income</span><strong className="amount-income">+{money(summary.total_income)}</strong></div><div><span>Expenses</span><strong className="amount-expense">−{money(summary.total_expenses)}</strong></div><div><span>Savings</span><strong>{money(summary.savings)}</strong></div></div><p className="insight-callout">{summary.spending_change_percent === null ? 'Add a previous month of activity to see a comparison.' : Number(summary.spending_change_percent) > 0 ? `Your spending is ${summary.spending_change_percent}% higher than last month.` : `Your spending is ${Math.abs(Number(summary.spending_change_percent))}% lower than last month.`}</p></Card><Card><div className="card-heading"><div><p className="eyebrow">BIGGEST MOVES</p><h2>Top expenses</h2></div></div>{summary.biggest_transactions.length ? <div className="biggest-list">{summary.biggest_transactions.map((transaction) => <div key={transaction.id}><div><strong>{transaction.description || transaction.category_name}</strong><p>{transaction.category_name} · {displayDate(transaction.transaction_date)}</p></div><b>{money(transaction.amount)}</b></div>)}</div> : <EmptyState icon={<BarChart3 size={22} />} title="No expenses yet" body="This list grows from real expenses in the selected month." />}</Card></section>
  </>
}

function Metric({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) { return <Card className="metric-card"><span>{icon}</span><p>{label}</p><strong>{value}</strong></Card> }
function ChartEmpty() { return <div className="chart-empty">Your first entries will shape this chart.</div> }
