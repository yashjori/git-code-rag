import { type FormEvent, useState } from 'react'

type Mode = 'login' | 'signup'

interface Props {
  isLoggingIn: boolean
  loginError: string | null
  onSubmit: (mode: Mode, username: string, password: string) => Promise<void>
  onModeChange: () => void
}

// Mirrors SignupRequest's constraints in app/models/schemas.py, so most
// mistakes are caught before a round-trip. The backend still validates.
const USERNAME_PATTERN = '[A-Za-z0-9._\\-]+'
const MIN_PASSWORD_LENGTH = 8

export function LoginPage({ isLoggingIn, loginError, onSubmit, onModeChange }: Props) {
  const [mode, setMode] = useState<Mode>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const isSignup = mode === 'signup'

  function switchMode() {
    setMode(isSignup ? 'login' : 'signup')
    setConfirmPassword('')
    setLocalError(null)
    onModeChange()
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!username.trim() || !password) return
    if (isSignup && password !== confirmPassword) {
      setLocalError('Passwords do not match.')
      return
    }
    setLocalError(null)
    try {
      await onSubmit(mode, username.trim(), password)
    } catch {
      // loginError already reflects this.
    }
  }

  const error = localError ?? loginError
  const inputClass =
    'rounded border border-line bg-panel-2 px-2.5 py-1.5 font-mono text-sm text-fg focus-visible:border-amber'
  const labelClass = 'font-mono text-xs uppercase tracking-wide text-muted'

  return (
    <div className="flex h-screen items-center justify-center bg-ink px-6">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-amber" aria-hidden />
          <h1 className="font-mono text-sm font-medium text-fg">git-code-assistant</h1>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-4 rounded border border-line bg-panel p-6"
        >
          <p className="font-mono text-sm text-amber">{isSignup ? '$ signup' : '$ login'}</p>

          <label className="flex flex-col gap-1.5">
            <span className={labelClass}>Username</span>
            <input
              type="text"
              name="username"
              autoComplete="username"
              autoFocus
              required
              minLength={isSignup ? 3 : undefined}
              maxLength={isSignup ? 32 : undefined}
              pattern={isSignup ? USERNAME_PATTERN : undefined}
              title={isSignup ? '3-32 characters: letters, digits, . _ -' : undefined}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className={inputClass}
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className={labelClass}>Password</span>
            <input
              type="password"
              name="password"
              autoComplete={isSignup ? 'new-password' : 'current-password'}
              required
              minLength={isSignup ? MIN_PASSWORD_LENGTH : undefined}
              maxLength={isSignup ? 72 : undefined}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={inputClass}
            />
            {isSignup && (
              <span className="font-mono text-xs text-muted">
                At least {MIN_PASSWORD_LENGTH} characters.
              </span>
            )}
          </label>

          {isSignup && (
            <label className="flex flex-col gap-1.5">
              <span className={labelClass}>Confirm password</span>
              <input
                type="password"
                name="confirm-password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                className={inputClass}
              />
            </label>
          )}

          <button
            type="submit"
            disabled={isLoggingIn}
            className="mt-1 rounded bg-amber px-3 py-1.5 text-sm font-medium text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSignup
              ? isLoggingIn
                ? 'Creating account…'
                : 'Create account'
              : isLoggingIn
                ? 'Signing in…'
                : 'Sign in'}
          </button>

          {error && (
            <p role="alert" className="font-mono text-xs text-red">
              {error}
            </p>
          )}
        </form>

        <p className="mt-4 text-center text-xs text-muted">
          {isSignup ? 'Already have an account? ' : "Don't have an account? "}
          <button
            type="button"
            onClick={switchMode}
            className="font-mono text-amber transition-opacity hover:opacity-80"
          >
            {isSignup ? 'Sign in' : 'Create one'}
          </button>
        </p>
      </div>
    </div>
  )
}
