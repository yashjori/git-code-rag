import { useCallback, useEffect, useState } from 'react'
import { ApiError, api, setUnauthorizedHandler } from '../api/client'

type AuthStatus = 'checking' | 'authenticated' | 'anonymous'

export function useAuth() {
  const [status, setStatus] = useState<AuthStatus>('checking')
  const [username, setUsername] = useState<string | null>(null)
  const [loginError, setLoginError] = useState<string | null>(null)
  const [isLoggingIn, setIsLoggingIn] = useState(false)

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setStatus('anonymous')
      setUsername(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  useEffect(() => {
    let cancelled = false
    api
      .currentUser()
      .then((result) => {
        if (cancelled) return
        setUsername(result.username)
        setStatus('authenticated')
      })
      .catch(() => {
        if (cancelled) return
        setStatus('anonymous')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (usernameInput: string, password: string) => {
    setIsLoggingIn(true)
    setLoginError(null)
    try {
      const result = await api.login({ username: usernameInput, password })
      setUsername(result.username)
      setStatus('authenticated')
    } catch (error) {
      setLoginError(error instanceof ApiError ? error.message : 'Could not log in.')
      throw error
    } finally {
      setIsLoggingIn(false)
    }
  }, [])

  const logout = useCallback(async () => {
    await api.logout().catch(() => {
      // Already logged out server-side (e.g. expired session) - either
      // way the client should drop back to the login screen.
    })
    setUsername(null)
    setStatus('anonymous')
  }, [])

  return { status, username, isLoggingIn, loginError, login, logout }
}
