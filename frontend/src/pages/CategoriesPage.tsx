import { Pencil, Plus, Tags, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { createCategory, deleteCategory, getCategories, updateCategory } from '../api/ledger'
import { ApiError } from '../api/client'
import { Button, Card, ConfirmDialog, EmptyState, ErrorNotice, LoadingBlock, Modal, PageHeader } from '../components/ui'
import { useToast } from '../components/toast'
import type { Category, TransactionType } from '../types/api'

const colors = ['#73A847', '#F2994A', '#3B82F6', '#A855F7', '#EC4899', '#14B8A6', '#EF4444', '#64748B']

export function CategoriesPage() {
  const { showToast } = useToast()
  const [categories, setCategories] = useState<Category[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Category | null | undefined>(undefined)
  const [deleting, setDeleting] = useState<Category | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const load = () => { setIsLoading(true); setError(null); void getCategories().then(setCategories).catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : 'Could not load your categories.')).finally(() => setIsLoading(false)) }
  useEffect(load, [])
  const grouped = useMemo(() => ({ expense: categories.filter((category) => category.type === 'expense'), income: categories.filter((category) => category.type === 'income') }), [categories])
  async function remove() { if (!deleting) return; setIsDeleting(true); try { await deleteCategory(deleting.id); showToast('Category deleted.'); setDeleting(null); load() } catch (requestError) { showToast(requestError instanceof ApiError ? requestError.message : 'This category could not be deleted.', 'error') } finally { setIsDeleting(false) } }
  return <>
    <PageHeader eyebrow="YOUR LABELS" title="Make your money yours." description="Create the categories that make your spending feel instantly familiar." action={<Button onClick={() => setEditing(null)}><Plus size={17} /> New category</Button>} />
    {isLoading ? <LoadingBlock label="Loading your categories…" /> : error ? <ErrorNotice message={error} onRetry={load} /> : !categories.length ? <EmptyState icon={<Tags size={24} />} title="No categories yet" body="Create one to start organizing each transaction." action={<Button onClick={() => setEditing(null)}><Plus size={17} /> Add category</Button>} /> : <div className="category-groups"><CategoryGroup title="Expenses" description="What you spend" items={grouped.expense} onEdit={setEditing} onDelete={setDeleting} /><CategoryGroup title="Income" description="What you earn" items={grouped.income} onEdit={setEditing} onDelete={setDeleting} /></div>}
    {editing !== undefined && <CategoryModal category={editing} onClose={() => setEditing(undefined)} onSaved={(message) => { showToast(message); setEditing(undefined); load() }} />}
    {deleting && <ConfirmDialog title="Delete this category?" body="You can only delete categories that have not been used in transactions, budgets, or schedules." onClose={() => setDeleting(null)} onConfirm={() => void remove()} loading={isDeleting} />}
  </>
}

function CategoryGroup({ title, description, items, onEdit, onDelete }: { title: string; description: string; items: Category[]; onEdit: (category: Category) => void; onDelete: (category: Category) => void }) { return <section><div className="section-heading"><div><p className="eyebrow">{description.toUpperCase()}</p><h2>{title}</h2></div><span>{items.length}</span></div><div className="category-grid">{items.map((category) => <Card className="category-card" key={category.id}><span className="category-card__color" style={{ background: category.color ?? '#829085' }} /><div><strong>{category.name}</strong><p>{category.icon ? category.icon.replaceAll('-', ' ') : 'Personal category'}</p></div><div className="row-actions"><button aria-label={`Edit ${category.name}`} onClick={() => onEdit(category)}><Pencil size={16} /></button><button className="row-actions__delete" aria-label={`Delete ${category.name}`} onClick={() => onDelete(category)}><Trash2 size={16} /></button></div></Card>)}</div></section> }

function CategoryModal({ category, onClose, onSaved }: { category: Category | null; onClose: () => void; onSaved: (message: string) => void }) {
  const [name, setName] = useState(category?.name ?? '')
  const [type, setType] = useState<TransactionType>(category?.type ?? 'expense')
  const [color, setColor] = useState(category?.color ?? colors[0])
  const [icon, setIcon] = useState(category?.icon ?? '')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setError(null); setBusy(true); try { const payload = { name, type, color, icon: icon || null }; if (category) await updateCategory(category.id, payload); else await createCategory(payload); onSaved(category ? 'Category updated.' : 'Category created.') } catch (requestError) { setError(requestError instanceof ApiError ? requestError.message : 'Could not save this category.') } finally { setBusy(false) } }
  return <Modal title={category ? 'Edit category' : 'Create category'} onClose={onClose}><form className="form-grid" onSubmit={submit}><label className="form-field form-field--full"><span>Name</span><input required maxLength={80} value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Coffee runs" autoFocus /></label><div className="segmented-control"><button type="button" className={type === 'expense' ? 'active expense' : ''} onClick={() => setType('expense')}>Expense</button><button type="button" className={type === 'income' ? 'active income' : ''} onClick={() => setType('income')}>Income</button></div><label className="form-field"><span>Icon label <em>optional</em></span><input maxLength={40} value={icon} onChange={(event) => setIcon(event.target.value)} placeholder="e.g. coffee" /></label><div className="form-field form-field--full"><span>Colour</span><div className="color-options">{colors.map((option) => <button type="button" key={option} aria-label={`Use ${option}`} className={color === option ? 'selected' : ''} style={{ background: option }} onClick={() => setColor(option)} />)}</div></div>{error && <p className="form-error form-field--full">{error}</p>}<div className="modal-actions form-field--full"><Button type="button" variant="ghost" onClick={onClose}>Cancel</Button><Button type="submit" loading={busy}>{category ? 'Save changes' : 'Create category'}</Button></div></form></Modal>
}
