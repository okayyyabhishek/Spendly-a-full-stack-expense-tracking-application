import { useEffect, useState, type FormEvent } from 'react'

import { getCategories, createTransaction, updateTransaction } from '../../api/ledger'
import { ApiError } from '../../api/client'
import { Button, Modal } from '../../components/ui'
import type { Category, PaymentMethod, Transaction, TransactionType } from '../../types/api'

const paymentMethods: Array<{ value: PaymentMethod; label: string }> = [
  { value: 'upi', label: 'UPI' }, { value: 'cash', label: 'Cash' }, { value: 'credit_card', label: 'Credit card' },
  { value: 'debit_card', label: 'Debit card' }, { value: 'bank_transfer', label: 'Bank transfer' }, { value: 'other', label: 'Other' },
]

const today = () => new Date().toISOString().slice(0, 10)

export function TransactionModal({ transaction, initialType = 'expense', onClose, onSaved }: { transaction?: Transaction | null; initialType?: TransactionType; onClose: () => void; onSaved: (message: string) => void }) {
  const [categories, setCategories] = useState<Category[]>([])
  const [isLoadingCategories, setIsLoadingCategories] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    type: transaction?.type ?? initialType,
    amount: transaction?.amount ?? '',
    category_id: transaction?.category_id ? String(transaction.category_id) : '',
    description: transaction?.description ?? '',
    payment_method: transaction?.payment_method ?? 'upi' as PaymentMethod,
    transaction_date: transaction?.transaction_date ?? today(),
  })

  useEffect(() => {
    setIsLoadingCategories(true)
    void getCategories(form.type)
      .then((items) => {
        setCategories(items)
        setForm((current) => ({ ...current, category_id: items.some((item) => item.id === Number(current.category_id)) ? current.category_id : String(items[0]?.id ?? '') }))
      })
      .catch(() => setError('Could not load your categories. Please try again.'))
      .finally(() => setIsLoadingCategories(false))
  }, [form.type])

  const update = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setForm((current) => ({ ...current, [key]: event.target.value }))

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    if (!form.category_id) { setError('Choose a category to continue.'); return }
    setIsSaving(true)
    try {
      const payload = { ...form, amount: form.amount, category_id: Number(form.category_id), description: form.description || null }
      if (transaction) await updateTransaction(transaction.id, payload)
      else await createTransaction(payload)
      onSaved(transaction ? 'Transaction updated.' : `${form.type === 'expense' ? 'Expense' : 'Income'} added to your ledger.`)
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Could not save this transaction.')
    } finally { setIsSaving(false) }
  }

  return <Modal title={transaction ? 'Edit transaction' : `Add ${initialType === 'expense' ? 'expense' : 'income'}`} onClose={onClose}>
    <form className="form-grid" onSubmit={submit}>
      <div className="segmented-control"><button type="button" className={form.type === 'expense' ? 'active expense' : ''} onClick={() => setForm((current) => ({ ...current, type: 'expense', category_id: '' }))}>Expense</button><button type="button" className={form.type === 'income' ? 'active income' : ''} onClick={() => setForm((current) => ({ ...current, type: 'income', category_id: '' }))}>Income</button></div>
      <label className="form-field"><span>Amount</span><div className="currency-input"><span>₹</span><input required inputMode="decimal" min="0.01" step="0.01" type="number" value={form.amount} onChange={update('amount')} placeholder="0.00" autoFocus /></div></label>
      <label className="form-field"><span>Category</span><select required disabled={isLoadingCategories} value={form.category_id} onChange={update('category_id')}><option value="">{isLoadingCategories ? 'Loading categories…' : 'Choose a category'}</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
      <label className="form-field"><span>Date</span><input required type="date" value={form.transaction_date} onChange={update('transaction_date')} /></label>
      <label className="form-field"><span>Payment method</span><select value={form.payment_method} onChange={update('payment_method')}>{paymentMethods.map((method) => <option key={method.value} value={method.value}>{method.label}</option>)}</select></label>
      <label className="form-field form-field--full"><span>Note <em>optional</em></span><textarea rows={3} maxLength={1000} value={form.description} onChange={update('description')} placeholder="What was this for?" /></label>
      {error && <p className="form-error form-field--full" role="alert">{error}</p>}
      <div className="modal-actions form-field--full"><Button variant="ghost" type="button" onClick={onClose}>Cancel</Button><Button type="submit" loading={isSaving}>{transaction ? 'Save changes' : 'Add to ledger'}</Button></div>
    </form>
  </Modal>
}
