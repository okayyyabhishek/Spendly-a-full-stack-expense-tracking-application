import { ChevronLeft, ChevronRight, Filter, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { deleteTransaction, getCategories, getTransactions } from '../api/ledger'
import { ApiError } from '../api/client'
import { ConfirmDialog, Button, EmptyState, ErrorNotice, LoadingBlock, PageHeader } from '../components/ui'
import { useToast } from '../components/toast'
import { TransactionModal } from '../features/transactions/TransactionModal'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import type { Category, PaymentMethod, Transaction, TransactionPage as TransactionPageResult, TransactionType } from '../types/api'
import { displayDate, money, paymentLabel } from '../utils/format'

const paymentOptions: Array<{ value: PaymentMethod; label: string }> = [
  { value: 'cash', label: 'Cash' }, { value: 'upi', label: 'UPI' }, { value: 'credit_card', label: 'Credit card' },
  { value: 'debit_card', label: 'Debit card' }, { value: 'bank_transfer', label: 'Bank transfer' }, { value: 'other', label: 'Other' },
]

export function TransactionsPage() {
  const { showToast } = useToast()
  const [categories, setCategories] = useState<Category[]>([])
  const [page, setPage] = useState(1)
  const [result, setResult] = useState<TransactionPageResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search)
  const [filters, setFilters] = useState({ type: '', category_id: '', payment_method: '', from_date: '', to_date: '', min_amount: '', max_amount: '' })
  const [modal, setModal] = useState<{ transaction?: Transaction; type?: TransactionType } | null>(null)
  const [deleting, setDeleting] = useState<Transaction | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const query = useMemo(() => ({ page, page_size: 12, search: debouncedSearch, ...filters }), [page, debouncedSearch, filters])
  const refreshCategories = () => void getCategories().then(setCategories).catch(() => undefined)
  const load = () => {
    setIsLoading(true); setError(null)
    void getTransactions(query)
      .then(setResult)
      .catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : 'We could not load your transactions.'))
      .finally(() => setIsLoading(false))
  }
  useEffect(refreshCategories, [])
  useEffect(load, [query])

  const updateFilter = (key: keyof typeof filters, value: string) => { setPage(1); setFilters((current) => ({ ...current, [key]: value })) }
  async function remove() {
    if (!deleting) return
    setIsDeleting(true)
    try { await deleteTransaction(deleting.id); showToast('Transaction deleted.'); setDeleting(null); load() }
    catch (requestError) { showToast(requestError instanceof ApiError ? requestError.message : 'Could not delete this transaction.', 'error') }
    finally { setIsDeleting(false) }
  }

  return <>
    <PageHeader eyebrow="LEDGER" title="Every move, in one place." description="Search, filter, and refine your complete money history." action={<div className="quick-actions"><Button onClick={() => setModal({ type: 'expense' })}><Plus size={17} /> Add expense</Button><Button variant="secondary" onClick={() => setModal({ type: 'income' })}><Plus size={17} /> Add income</Button></div>} />
    <section className="ledger-toolbar"><label className="search-field"><Search size={18} /><input value={search} onChange={(event) => { setPage(1); setSearch(event.target.value) }} placeholder="Search description or category" /></label><Button variant="secondary" className={showFilters ? 'button--selected' : ''} onClick={() => setShowFilters((current) => !current)}><Filter size={17} /> Filters</Button></section>
    {showFilters && <section className="filter-panel">
      <label><span>Type</span><select value={filters.type} onChange={(event) => updateFilter('type', event.target.value)}><option value="">All types</option><option value="expense">Expenses</option><option value="income">Income</option></select></label>
      <label><span>Category</span><select value={filters.category_id} onChange={(event) => updateFilter('category_id', event.target.value)}><option value="">All categories</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name} ({category.type})</option>)}</select></label>
      <label><span>Payment method</span><select value={filters.payment_method} onChange={(event) => updateFilter('payment_method', event.target.value)}><option value="">All methods</option>{paymentOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
      <label><span>From</span><input type="date" value={filters.from_date} onChange={(event) => updateFilter('from_date', event.target.value)} /></label>
      <label><span>To</span><input type="date" value={filters.to_date} onChange={(event) => updateFilter('to_date', event.target.value)} /></label>
      <label><span>Minimum amount</span><input inputMode="decimal" type="number" min="0" value={filters.min_amount} onChange={(event) => updateFilter('min_amount', event.target.value)} placeholder="₹ 0" /></label>
      <label><span>Maximum amount</span><input inputMode="decimal" type="number" min="0" value={filters.max_amount} onChange={(event) => updateFilter('max_amount', event.target.value)} placeholder="No limit" /></label>
      <Button variant="ghost" onClick={() => { setFilters({ type: '', category_id: '', payment_method: '', from_date: '', to_date: '', min_amount: '', max_amount: '' }); setSearch(''); setPage(1) }}>Clear all</Button>
    </section>}
    {isLoading ? <LoadingBlock label="Loading transactions…" /> : error ? <ErrorNotice message={error} onRetry={load} /> : !result?.items.length ? <EmptyState icon={<Search size={23} />} title="No transactions found" body="Try a different filter, or add your first income or expense." action={<Button onClick={() => setModal({ type: 'expense' })}><Plus size={17} /> Add a transaction</Button>} /> : <section className="ledger-card"><div className="ledger-meta"><span>{result.total} transaction{result.total === 1 ? '' : 's'}</span><span>Page {result.page} of {result.total_pages}</span></div><div className="transaction-table"><div className="transaction-table__head"><span>Date</span><span>Transaction</span><span>Category</span><span>Payment</span><span>Amount</span><span>Actions</span></div>{result.items.map((transaction) => <article className="transaction-row" key={transaction.id}><span className="transaction-date">{displayDate(transaction.transaction_date)}</span><div className="transaction-description"><strong>{transaction.description || transaction.category.name}</strong>{transaction.recurring_transaction_id && <small>Recurring</small>}</div><span className="category-pill"><i style={{ background: transaction.category.color ?? '#829085' }} />{transaction.category.name}</span><span className="payment-method">{paymentLabel(transaction.payment_method)}</span><strong className={transaction.type === 'income' ? 'amount-income' : 'amount-expense'}>{transaction.type === 'income' ? '+' : '−'}{money(transaction.amount)}</strong><div className="row-actions"><button aria-label="Edit transaction" onClick={() => setModal({ transaction })}><Pencil size={16} /></button><button className="row-actions__delete" aria-label="Delete transaction" onClick={() => setDeleting(transaction)}><Trash2 size={16} /></button></div></article>)}</div><div className="pagination"><Button variant="ghost" disabled={page === 1} onClick={() => setPage((current) => current - 1)}><ChevronLeft size={17} /> Previous</Button><Button variant="ghost" disabled={page >= result.total_pages} onClick={() => setPage((current) => current + 1)}>Next <ChevronRight size={17} /></Button></div></section>}
    {modal && <TransactionModal transaction={modal.transaction} initialType={modal.type} onClose={() => setModal(null)} onSaved={(message) => { showToast(message); setModal(null); load() }} />}
    {deleting && <ConfirmDialog title="Delete this transaction?" body="This removes the entry from your ledger and updates your financial insights. This cannot be undone." loading={isDeleting} onClose={() => setDeleting(null)} onConfirm={() => void remove()} />}
  </>
}
