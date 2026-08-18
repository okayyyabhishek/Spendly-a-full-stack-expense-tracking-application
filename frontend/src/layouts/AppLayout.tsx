import { Bell, ChartNoAxesCombined, ChevronDown, CircleDollarSign, LayoutDashboard, LogOut, ReceiptText, RefreshCw, Tags, WalletCards, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { getNotifications, markAllNotificationsRead, markNotificationRead } from '../api/ledger'
import { AppLogo } from '../components/AppLogo'
import { Button } from '../components/ui'
import { useToast } from '../components/toast'
import { useAuth } from '../features/auth/AuthContext'
import type { NotificationPage } from '../types/api'
import { displayDate } from '../utils/format'

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/transactions', label: 'Transactions', icon: ReceiptText },
  { to: '/budgets', label: 'Budgets', icon: WalletCards },
  { to: '/recurring', label: 'Recurring', icon: RefreshCw },
  { to: '/analytics', label: 'Insights', icon: ChartNoAxesCombined },
  { to: '/categories', label: 'Categories', icon: Tags },
]

export function AppLayout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [showNotifications, setShowNotifications] = useState(false)
  const [notificationPage, setNotificationPage] = useState<NotificationPage>({ items: [], unread_count: 0 })
  const [notificationError, setNotificationError] = useState(false)

  const refreshNotifications = () => {
    void getNotifications()
      .then((page) => { setNotificationPage(page); setNotificationError(false) })
      .catch(() => setNotificationError(true))
  }
  useEffect(refreshNotifications, [])

  async function signOutNow() {
    try {
      await signOut()
      navigate('/login')
    } catch {
      showToast('We could not sign you out. Please try again.', 'error')
    }
  }

  async function openNotificationCenter() {
    setShowNotifications((current) => !current)
    refreshNotifications()
  }

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <AppLogo />
        <nav aria-label="Main navigation" className="sidebar-nav">
          {navItems.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link ${isActive ? 'nav-link--active' : ''}`}><Icon size={19} /><span>{label}</span></NavLink>)}
        </nav>
        <div className="sidebar-footer"><div className="sidebar-hint"><CircleDollarSign size={18} /><span>Every number here comes from your secure ledger.</span></div><button className="signout" onClick={() => void signOutNow()}><LogOut size={18} /> Sign out</button></div>
      </aside>
      <div className="app-content">
        <header className="topbar"><div className="topbar__mobile-brand"><AppLogo /></div><div className="topbar__right"><div className="notifications-wrap"><button className="icon-button icon-button--notification" onClick={() => void openNotificationCenter()} aria-label="View notifications"><Bell size={20} />{notificationPage.unread_count > 0 && <span>{notificationPage.unread_count > 9 ? '9+' : notificationPage.unread_count}</span>}</button>{showNotifications && <NotificationPopover page={notificationPage} hasError={notificationError} onClose={() => setShowNotifications(false)} onRead={(id) => void markNotificationRead(id).then(refreshNotifications).catch(() => showToast('Could not update notification.', 'error'))} onReadAll={() => void markAllNotificationsRead().then(refreshNotifications).catch(() => showToast('Could not update notifications.', 'error'))} />}</div><div className="user-chip"><span>{user?.name.charAt(0).toUpperCase()}</span><div><strong>{user?.name}</strong><small>{user?.email}</small></div><ChevronDown size={16} /></div></div></header>
        <main className="page-content"><Outlet /></main>
      </div>
      <nav className="bottom-nav" aria-label="Mobile navigation">{navItems.slice(0, 5).map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} className={({ isActive }) => `bottom-nav__item ${isActive ? 'bottom-nav__item--active' : ''}`}><Icon size={19} /><span>{label}</span></NavLink>)}</nav>
    </div>
  )
}

function NotificationPopover({ page, hasError, onRead, onReadAll, onClose }: { page: NotificationPage; hasError: boolean; onRead: (id: number) => void; onReadAll: () => void; onClose: () => void }) {
  return <section className="notification-popover" aria-label="Notifications"><header><div><p className="eyebrow">UPDATES</p><h2>Heads up</h2></div><button className="icon-button" onClick={onClose} aria-label="Close notifications"><X size={18} /></button></header>{hasError ? <p className="popover-empty">Your notifications could not be loaded.</p> : page.items.length === 0 ? <p className="popover-empty">You’re all caught up.</p> : <><div className="notification-list">{page.items.map((notice) => <button className={`notification-item ${notice.is_read ? '' : 'notification-item--unread'}`} key={notice.id} onClick={() => !notice.is_read && onRead(notice.id)}><span /><div><strong>{notice.title}</strong>{notice.body && <p>{notice.body}</p>}<small>{displayDate(notice.created_at.slice(0, 10))}</small></div></button>)}</div>{page.unread_count > 0 && <Button variant="ghost" onClick={onReadAll}>Mark all as read</Button>}</>}</section>
}
