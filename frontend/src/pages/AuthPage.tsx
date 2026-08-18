import { ArrowRight, Eye, EyeOff, LockKeyhole, Sparkles } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '../api/client'
import { AppLogo } from '../components/AppLogo'
import { Button } from '../components/ui'
import { useAuth } from '../features/auth/AuthContext'

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const { user, signIn, signUp } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const isRegister = mode === 'register'

  if (user) return <Navigate to="/" replace />

  const update = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm((current) => ({ ...current, [key]: event.target.value }))
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    if (isRegister && form.password !== form.confirmPassword) {
      setError('Your passwords do not match.')
      return
    }
    setIsSubmitting(true)
    try {
      if (isRegister) await signUp(form.name, form.email, form.password, form.confirmPassword)
      else await signIn(form.email, form.password)
      const intended = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname
      navigate(intended || '/', { replace: true })
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Unable to continue right now. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-shell">
      <aside className="auth-poster">
        <AppLogo />
        <div className="auth-poster__copy">
          <p className="eyebrow">A CALMER MONEY ROUTINE</p>
          <h1>Know your next move, not just your last spend.</h1>
          <p>Capture every rupee, understand your rhythm, and make space for what matters.</p>
        </div>
        <div className="auth-poster__note"><Sparkles size={17} /> Private by design. Your data stays yours.</div>
      </aside>
      <section className="auth-panel">
        <div className="auth-panel__inner">
          <div className="auth-mobile-logo"><AppLogo /></div>
          <p className="eyebrow">{isRegister ? 'START YOUR LEDGER' : 'WELCOME BACK'}</p>
          <h2>{isRegister ? 'A clearer money story starts here.' : 'Good to see you again.'}</h2>
          <p className="auth-subtitle">{isRegister ? 'Create your secure account in a minute.' : 'Sign in to your private finance workspace.'}</p>
          <form className="auth-form" onSubmit={submit}>
            {isRegister && <label><span>Name</span><input required minLength={2} value={form.name} onChange={update('name')} placeholder="Your full name" autoComplete="name" /></label>}
            <label><span>Email address</span><input required type="email" value={form.email} onChange={update('email')} placeholder="you@example.com" autoComplete="email" /></label>
            <label><span>Password</span><div className="password-input"><input required minLength={isRegister ? 8 : 1} type={showPassword ? 'text' : 'password'} value={form.password} onChange={update('password')} placeholder={isRegister ? '8+ characters, upper/lowercase and number' : 'Your password'} autoComplete={isRegister ? 'new-password' : 'current-password'} /><button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword((current) => !current)}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
            {isRegister && <label><span>Confirm password</span><input required minLength={8} type={showPassword ? 'text' : 'password'} value={form.confirmPassword} onChange={update('confirmPassword')} placeholder="Repeat your password" autoComplete="new-password" /></label>}
            {error && <p className="form-error" role="alert">{error}</p>}
            <Button type="submit" loading={isSubmitting} className="auth-submit">{isRegister ? 'Create my account' : 'Sign in'} <ArrowRight size={17} /></Button>
          </form>
          <p className="auth-switch">{isRegister ? 'Already have an account?' : 'New to Spendly?'} <Link to={isRegister ? '/login' : '/register'}>{isRegister ? 'Sign in' : 'Create an account'}</Link></p>
          <p className="auth-security"><LockKeyhole size={14} /> Passwords are securely hashed and never stored in plain text.</p>
        </div>
      </section>
    </main>
  )
}
