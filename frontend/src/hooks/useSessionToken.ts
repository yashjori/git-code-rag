import { useEffect, useState } from 'react'
import type { Provider } from '../api/types'

// Session-scoped only: cleared when the tab closes, never sent anywhere
// except as part of an index request, never written to localStorage or
// any server-side store. This is what lets different people use the same
// deployment with their own credentials without a login system - the
// browser tab itself is the per-user boundary.
const STORAGE_PREFIX = 'git-code-assistant:token:'

function readToken(provider: Provider): string {
  try {
    return sessionStorage.getItem(STORAGE_PREFIX + provider) ?? ''
  } catch {
    return ''
  }
}

export function useSessionToken(provider: Provider) {
  const [token, setTokenState] = useState(() => readToken(provider))

  useEffect(() => {
    setTokenState(readToken(provider))
  }, [provider])

  function setToken(value: string) {
    setTokenState(value)
    try {
      if (value) {
        sessionStorage.setItem(STORAGE_PREFIX + provider, value)
      } else {
        sessionStorage.removeItem(STORAGE_PREFIX + provider)
      }
    } catch {
      // sessionStorage unavailable (e.g. private browsing) - the token
      // still works for this submission via component state, it just
      // won't be remembered for the next one.
    }
  }

  return [token, setToken] as const
}
