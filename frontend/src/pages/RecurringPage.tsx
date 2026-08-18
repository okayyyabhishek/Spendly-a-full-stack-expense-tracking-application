import { CalendarClock, Pencil, Plus, Power, Trash2 } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'

import { createRecurring, deleteRecurring, getCategories, getRecurring, updateRecurring } from '../api/ledger'
import { ApiError } from '../api/client'
import { Button, Card, ConfirmDialog, EmptyState, ErrorNotice, LoadingBlock, Modal, PageHeader } from '../components/ui'
import { useToast } from '../components/toast'
import type { Category, Frequency, PaymentMethod, RecurringTransaction, TransactionType } from '../types/api'
import { displayDate, money, paymentLabel } from '../utils/format'

const frequencies: Array<{ value: Frequency; label: string }> = [{ value: 'daily', label: 'Daily' }, { value: 'weekly', label: 'Weekly' }, { value: 'monthly', label: 'Monthly' }, { value: 'yearly', label: 'Yearly' }]
const paymentMethods: Array<{ value: PaymentMethod; label: string }> = [{ value: 'upi', label: 'UPI' }, { value: 'cash', label: 'Cash' }, { value: 'credit_card', label: 'Credit card' }, { value: 'debit_card', label: 'Debit card' }, { value: 'bank_transfer', label: 'Bank transfer' }, { value: 'other', label: 'Other' }]

export function RecurringPage() {
  const { showToast } = useToast()
  const [items, setItems] = useState<RecurringTransaction[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<RecurringTransaction | null | undefined>(undefined)
  const [deleting, setDeleting] = useState<RecurringTransaction | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const load = () => { setIsLoading(true); setError(null); void getRecurring().then(setItems).catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : 'Could not load recurring transactions.')).finally(() => setIsLoading(false)) }
  useEffect(load, [])
  async function toggle(item: RecurringTransaction) {
    try { await updateRecurring(item.id, { active: !item.active }); showToast(item.active ? 'Schedule paused.' : 'Schedule resumed.'); load() }
    catch (requestError) { showToast(requestError instanceof ApiError ? requestError.message : 'Could not update this schedule.', 'error') }
  }
  async function remove() { if (!deleting) return; setIsDeleting(true); try { await deleteRecurring(deleting.id); showToast('Recurring schedule removed.'); setDeleting(null); load() } catch (requestError) { showToast(requestError instanceof ApiError ? requestError.message : 'Could not remove this schedule.', 'error') } finally { setIsDeleting(false) } }

  return <>
    <PageHeader eyebrow="ON REPEAT" title="The expenses that keep coming." description="Set it once. Due occurrences are added to your secure ledger automatically." action={<Button onClick={() => setEditing(null)}><Plus size={17} /> Add recurring</Button>} />
    {isLoading ? <LoadingBlock label="Checking your recurring schedule…" /> : error ? <ErrorNotice message={error} onRetry={load} /> : !items.length ? <EmptyState icon={<CalendarClock size={24} />} title="Nothing on repeat yet" body="Rent, subscriptions, bills, and other regular money moves belong here." action={<Button onClick={() => setEditing(null)}><Plus size={17} /> Create schedule</Button>} /> : <section className="recurring-list">{items.map((item) => <Card className={`recurring-card ${item.active ? '' : 'recurring-card--paused'}`} key={item.id}><div className="recurring-card__main"><span className={`category-dot category-dot--${item.type}`} style={{ background: item.category.color ?? undefined }} /><div><div className="recurring-card__title"><h2>{item.description || item.category.name}</h2>{!item.active && <span>Paused</span>}</div><p>{item.category.name} · {paymentLabel(item.payment_method)} · {item.frequency}</p><small>Next due {displayDate(item.next_due_date)}</small></div></div><div className="recurring-card__value"><strong className={item.type === 'income' ? 'amount-income' : 'amount-expense'}>{item.type === 'income' ? '+' : '−'}{money(item.amount)}</strong><span>{item.frequency}</span></div><div className="row-actions"><button aria-label={item.active ? 'Pause schedule' : 'Resume schedule'} onClick={() => void toggle(item)}><Power size={16} /></button><button aria-label="Edit schedule" onClick={() => setEditing(item)}><Pencil size={16} /></button><button className="row-actions__delete" aria-label="Delete schedule" onClick={() => setDeleting(item)}><Trash2 size={16} /></button></div></Card>)}</section>}
    {editing !== undefined && <RecurringModal schedule={editing} onClose={() => setEditing(undefined)} onSaved={(message) => { showToast(message); setEditing(undefined); load() }} />}
    {deleting && <ConfirmDialog title="Remove this recurring schedule?" body="Future due transactions will no longer be created. Existing ledger entries will stay intact." onClose={() => setDeleting(null)} onConfirm={() => void remove()} loading={isDeleting} />}
  </>
}

function RecurringModal({ schedule, onClose, onSaved }: { schedule: RecurringTransaction | null; onClose: () => void; onSaved: (message: string) => void }) {
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({ type: schedule?.type ?? 'expense' as TransactionType, amount: schedule?.amount ?? '', category_id: schedule?.category_id ? String(schedule.category_id) : '', description: schedule?.description ?? '', payment_method: schedule?.payment_method ?? 'upi' as PaymentMethod, frequency: schedule?.frequency ?? 'monthly' as Frequency, start_date: schedule?.start_date ?? new Date().toISOString().slice(0, 10), end_date: schedule?.end_date ?? '' })
  useEffect(() => { void getCategories(form.type).then((nextCategories) => { setCategories(nextCategories); setForm((current) => ({ ...current, category_id: nextCategories.some((item) => item.id === Number(current.category_id)) ? current.category_id : String(nextCategories[0]?.id ?? '') })) }).catch(() => setError('Could not load your categories.')) }, [form.type])
  const update = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setForm((current) => ({ ...current, [key]: event.target.value }))
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setError(null); if (!form.category_id) { setError('Choose a category.'); return } setBusy(true); try { const payload = { ...form, category_id: Number(form.category_id), end_date: form.end_date || null, description: form.description || null }; if (schedule) await updateRecurring(schedule.id, payload); else await createRecurring(payload); onSaved(schedule ? 'Recurring schedule updated.' : 'Recurring schedule created.') } catch (requestError) { setError(requestError instanceof ApiError ? requestError.message : 'Could not save this schedule.') } finally { setBusy(false) } }
  return <Modal title={schedule ? 'Edit recurring schedule' : 'Create recurring schedule'} onClose={onClose}><form className="form-grid" onSubmit={submit}><div className="segmented-control"><button type="button" className={form.type === 'expense' ? 'active expense' : ''} onClick={() => setForm((current) => ({ ...current, type: 'expense', category_id: '' }))}>Expense</button><button type="button" className={form.type === 'income' ? 'active income' : ''} onClick={() => setForm((current) => ({ ...current, type: 'income', category_id: '' }))}>Income</button></div><label className="form-field"><span>Amount</span><div className="currency-input"><span>₹</span><input required min="0.01" step="0.01" type="number" value={form.amount} onChange={update('amount')} /></div></label><label className="form-field"><span>Category</span><select required value={form.category_id} onChange={update('category_id')}><option value="">Choose a category</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label><label className="form-field"><span>Frequency</span><select value={form.frequency} onChange={update('frequency')}>{frequencies.map((frequency) => <option key={frequency.value} value={frequency.value}>{frequency.label}</option>)}</select></label><label className="form-field"><span>Payment method</span><select value={form.payment_method} onChange={update('payment_method')}>{paymentMethods.map((method) => <option key={method.value} value={method.value}>{method.label}</option>)}</select></label><label className="form-field"><span>Starts</span><input required type="date" value={form.start_date} onChange={update('start_date')} /></label><label className="form-field"><span>Ends <em>optional</em></span><input type="date" value={form.end_date} min={form.start_date} onChange={update('end_date')} /></label><label className="form-field form-field--full"><span>Note <em>optional</em></span><textarea rows={2} maxLength={1000} placeholder="e.g. Apartment rent" value={form.description} onChange={update('description')} /></label>{error && <p className="form-error form-field--full">{error}</p>}<div className="modal-actions form-field--full"><Button type="button" variant="ghost" onClick={onClose}>Cancel</Button><Button type="submit" loading={busy}>{schedule ? 'Save changes' : 'Create schedule'}</Button></div></form></Modal>
}
