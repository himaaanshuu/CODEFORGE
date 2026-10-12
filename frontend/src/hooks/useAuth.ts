import { useEffect, useState } from 'react'
import { watchAuth, type User } from '../lib/supabase'

export type AuthStatus = 'loading' | 'signed-out' | 'signed-in'

export interface AuthState {
  status: AuthStatus
  user: User | null
}

/**
 * Live Supabase auth state for the whole app.
 * `loading` lasts only until the first onAuthStateChange callback —
 * no timers, no simulated responses.
 */
export function useAuth(): AuthState {
  const [state, setState] = useState<AuthState>({ status: 'loading', user: null })

  useEffect(() => {
    const unsubscribe = watchAuth((user) => {
      setState({ status: user ? 'signed-in' : 'signed-out', user })
    })
    return unsubscribe
  }, [])

  return state
}
