import { type FormEvent, useState } from 'react'

interface Props {
  isLoggingIn: boolean
  loginError: string | null
  onLogin: (username: string, password: string) => Promise<void>
}

export function LoginPage({ isLoggingIn, loginError, onLogin }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!username.trim() || !password) return
    try {
      await onLogin(username.trim(), password)
    } catch {
      // loginError already reflects this.
    }
  }

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
          <p className="font-mono text-sm text-amber">$ login</p>

          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-xs uppercase tracking-wide text-muted">
              Username
            </span>
            <input
              type="text"
              name="username"
              autoComplete="username"
              autoFocus
              required
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className="rounded border border-line bg-panel-2 px-2.5 py-1.5 font-mono text-sm text-fg focus-visible:border-amber"
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-xs uppercase tracking-wide text-muted">
              Password
            </span>
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="rounded border border-line bg-panel-2 px-2.5 py-1.5 font-mono text-sm text-fg focus-visible:border-amber"
            />
          </label>

          <button
            type="submit"
            disabled={isLoggingIn}
            className="mt-1 rounded bg-amber px-3 py-1.5 text-sm font-medium text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoggingIn ? 'Signing in…' : 'Sign in'}
          </button>

          {loginError && (
            <p role="alert" className="font-mono text-xs text-red">
              {loginError}
            </p>
          )}
        </form>
      </div>
    </div>
  )
}
