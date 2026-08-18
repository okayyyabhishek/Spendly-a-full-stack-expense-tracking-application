import { CircleDollarSign, Pencil, Plus, Target, Trash2 } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'

import { createBudget, deleteBudget, getBudgets, getCategories, updateBudget } from '../api/ledger'
import { ApiError } from '../api/client'
import { Button, Card, ConfirmDialog, EmptyState, ErrorNotice, LoadingBlock, Modal, PageHeader, Progress } from '../components/ui'
import { useToast } from '../components/toast'
import type { Budget, Category } from '../types/api'
import { currentMonthValue, money } from '../utils/format'

export function BudgetsPage() {
  const { showToast } = useToast()
  const [monthValue, setMonthValue] = useState(currentMonthValue())
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Budget | null | undefined>(undefined)
  const [deleting, setDeleting] = useState<Budget | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [formBusy, setFormBusy] = useState(false)

  const [year, month] = monthValue.split('-').map(Number)
  const load = () => {
    setIsLoading(true); setError(null)
    void Promise.all([getBudgets(month, year), getCategories('expense')])
      .then(([nextBudgets, nextCategories]) => { setBudgets(nextBudgets); setCategories(nextCategories) })
      .catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : 'Could not load your budgets.'))
      .finally(() => setIsLoading(false))
  }
  useEffect(load, [month, year])

  async function remove() {
    if (!deleting) return
    setIsDeleting(true)
    try { await deleteBudget(deleting.id); showToast('Budget deleted.'); setDeleting(null); load() }
    catch (requestError) { showToast(requestError instanceof ApiError ? requestError.message : 'Could not delete this budget.', 'error') }
    finally { setIsDeleting(false) }
  }
  return <>
    <PageHeader eyebrow="SPENDING PLAN" title="Give every rupee a role." description="Set a gentle boundary for the month, overall or by category." action={<Button onClick={() => setEditing(null)}><Plus size={17} /> New budget</Button>} />
    <div className="period-picker"><label><span>Budget month</span><input type="month" value={monthValue} onChange={(event) => setMonthValue(event.target.value)} /></label></div>
    {isLoading ? <LoadingBlock label="Calculating budget progress…" /> : error ? <ErrorNotice message={error} onRetry={load} /> : !budgets.length ? <EmptyState icon={<Target size={24} />} title="No budgets for this month" body="An overall budget is a simple place to begin." action={<Button onClick={() => setEditing(null)}><Plus size={17} /> Set a budget</Button>} /> : <section className="budget-grid">{budgets.map((budget) => <BudgetCard key={budget.id} budget={budget} onEdit={() => setEditing(budget)} onDelete={() => setDeleting(budget)} />)}</section>}
    {editing !== undefined && <BudgetModal budget={editing} categories={categories} month={month} year={year} busy={formBusy} onClose={() => setEditing(undefined)} onSave={async (payload) => { setFormBusy(true); try { if (editing) await updateBudget(editing.id, { amount: payload.amount }); else await createBudget(payload); showToast(editing ? 'Budget updated.' : 'Budget created.'); setEditing(undefined); load() } catch (requestError) { throw requestError } finally { setFormBusy(false) } }} />}
    {deleting && <ConfirmDialog title="Delete this budget?" body="Its spending history will stay in your ledger, but this budget target will be removed." loading={isDeleting} onClose={() => setDeleting(null)} onConfirm={() => void remove()} />}
  </>
}

function BudgetCard({ budget, onEdit, onDelete }: { budget: Budget; onEdit: () => void; onDelete: () => void }) {
  const icon = budget.category ? <span className="budget-card__dot" style={{ background: budget.category.color ?? '#839084' }} /> : <CircleDollarSign size={19} />
  const title = budget.category?.name ?? 'Overall monthly budget'
  const progress = Number(budget.percent_used)
  return <Card className={`budget-card budget-card--${budget.status}`}><div className="budget-card__head"><div className="budget-card__title">{icon}<div><p>{budget.category ? 'Category target' : 'Total spending cap'}</p><h2>{title}</h2></div></div><div className="row-actions"><button aria-label={`Edit ${title}`} onClick={onEdit}><Pencil size={16} /></button><button className="row-actions__delete" aria-label={`Delete ${title}`} onClick={onDelete}><Trash2 size={16} /></button></div></div><div className="budget-card__numbers"><div><span>Spent</span><strong>{money(budget.spent)}</strong></div><div><span>Remaining</span><strong>{money(budget.remaining)}</strong></div></div><Progress value={progress} status={budget.status} /><div className="budget-card__footer"><span>{progress}% used</span><span>{money(budget.amount)} planned</span></div>{budget.status !== 'on_track' && <p className="budget-card__alert">{budget.status === 'exceeded' ? 'This budget has been exceeded.' : 'You’re getting close to this limit.'}</p>}</Card>
}

function BudgetModal({ budget, categories, month, year, busy, onClose, onSave }: { budget: Budget | null; categories: Category[]; month: number; year: number; busy: boolean; onClose: () => void; onSave: (payload: { amount: string; category_id?: number; month: number; year: number }) => Promise<void> }) {
  const [amount, setAmount] = useState(budget?.amount ?? '')
  const [scope, setScope] = useState(budget?.category ? 'category' : 'overall')
  const [categoryId, setCategoryId] = useState(budget?.category?.id ? String(budget.category.id) : '')
  const [error, setError] = useState<string | null>(null)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null)
    if (scope === 'category' && !categoryId) { setError('Choose a category for this target.'); return }
    try { await onSave({ amount, ...(scope === 'category' ? { category_id: Number(categoryId) } : {}), month, year }) }
    catch (requestError) { setError(requestError instanceof ApiError ? requestError.message : 'Could not save this budget.') }
  }
  return <Modal title={budget ? 'Edit budget' : 'Create a budget'} onClose={onClose}><form className="form-grid" onSubmit={submit}>{!budget && <div className="segmented-control"><button type="button" className={scope === 'overall' ? 'active' : ''} onClick={() => setScope('overall')}>Overall</button><button type="button" className={scope === 'category' ? 'active' : ''} onClick={() => setScope('category')}>By category</button></div>}<label className="form-field"><span>Monthly amount</span><div className="currency-input"><span>₹</span><input required min="0.01" step="0.01" type="number" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="0.00" autoFocus /></div></label>{!budget && scope === 'category' && <label className="form-field"><span>Expense category</span><select required value={categoryId} onChange={(event) => setCategoryId(event.target.value)}><option value="">Choose a category</option>{categories.map((category) => <option value={category.id} key={category.id}>{category.name}</option>)}</select></label>}<p className="form-hint form-field--full">This target applies to {new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric' }).format(new Date(year, month - 1))}.</p>{error && <p className="form-error form-field--full">{error}</p>}<div className="modal-actions form-field--full"><Button variant="ghost" type="button" onClick={onClose}>Cancel</Button><Button type="submit" loading={busy}>{budget ? 'Save changes' : 'Set budget'}</Button></div></form></Modal>
}
