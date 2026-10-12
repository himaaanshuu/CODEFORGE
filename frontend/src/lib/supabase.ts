/**
 * Supabase web SDK initialization (@supabase/supabase-js v2).
 *
 * Configuration comes from VITE_SUPABASE_* env vars (see .env.local.example).
 * When configuration is missing, `supabaseConfigError` is set and every
 * auth helper fails with that error — there is no mock fallback.
 */

import { createClient, type SupabaseClient, type User } from '@supabase/supabase-js'

export type { User }

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined

function init(): { client: SupabaseClient | null; error: string | null } {
  if (supabaseUrl && supabaseAnonKey) {
    try {
      return { client: createClient(supabaseUrl, supabaseAnonKey), error: null }
    } catch (error) {
      return {
        client: null,
        error: `Supabase failed to initialize: ${
          error instanceof Error ? error.message : String(error)
        }`,
      }
    }
  }
  const missing: string[] = []
  if (!supabaseUrl) missing.push('VITE_SUPABASE_URL')
  if (!supabaseAnonKey) missing.push('VITE_SUPABASE_ANON_KEY')
  return {
    client: null,
    error: `Supabase is not configured (missing ${missing.join(
      ', ',
    )}). Add them to frontend/.env.local.`,
  }
}

const initialized = init()
const supabase: SupabaseClient | null = initialized.client
let cachedUser: User | null = null

/**
 * GitHub OAuth access token from the Supabase session.
 *
 * Supabase emits `provider_token` only once — immediately after the OAuth
 * sign-in redirect — so we capture it here and keep a local copy; later
 * page loads read the stored value. Used solely to call api.github.com
 * for the signed-in user's own repositories.
 */
const GITHUB_TOKEN_KEY = 'codeforge.github_provider_token'
let cachedGitHubToken: string | null = null
try {
  cachedGitHubToken = window.localStorage.getItem(GITHUB_TOKEN_KEY)
} catch {
  cachedGitHubToken = null
}

/** Human-readable configuration problem, or null when Supabase is ready. */
export const supabaseConfigError: string | null = initialized.error

if (supabase) {
  supabase.auth.onAuthStateChange((_event, session) => {
    cachedUser = session?.user ?? null
    if (session?.provider_token) {
      cachedGitHubToken = session.provider_token
      try {
        window.localStorage.setItem(GITHUB_TOKEN_KEY, session.provider_token)
      } catch {
        /* storage unavailable — in-memory copy still works this load */
      }
    }
  })
}

/** True when Supabase auth is usable in this browser build. */
export function isSupabaseReady(): boolean {
  return supabase !== null
}

function requireClient(): SupabaseClient {
  if (!supabase) {
    throw new Error(supabaseConfigError ?? 'Supabase is not initialized.')
  }
  return supabase
}

/** Subscribe to auth state changes. Returns an unsubscribe function. */
export function watchAuth(callback: (user: User | null) => void): () => void {
  if (!supabase) {
    callback(null)
    return () => undefined
  }
  const { data } = supabase.auth.onAuthStateChange((_event, session) => {
    callback(session?.user ?? null)
  })
  return () => data.subscription.unsubscribe()
}

/** Start the GitHub OAuth sign-in flow. Throws the Supabase error message on failure. */
export async function signInWithGitHub(): Promise<void> {
  const { error } = await requireClient().auth.signInWithOAuth({
    provider: 'github',
    options: { redirectTo: window.location.origin },
  })
  if (error) {
    throw new Error(error.message)
  }
}

/** Sign the current user out. */
export async function signOutUser(): Promise<void> {
  cachedGitHubToken = null
  try {
    window.localStorage.removeItem(GITHUB_TOKEN_KEY)
  } catch {
    /* storage unavailable */
  }
  const { error } = await requireClient().auth.signOut()
  if (error) {
    throw new Error(error.message)
  }
}

/** Current signed-in user, or null. */
export function currentUser(): User | null {
  return cachedUser
}

/**
 * Access token of the current session for API authorization headers, or null
 * when nobody is signed in. Never logs or persists the token.
 */
export async function getCurrentAccessToken(): Promise<string | null> {
  if (!supabase) return null
  try {
    const { data } = await supabase.auth.getSession()
    return data.session?.access_token ?? null
  } catch {
    return null
  }
}

/**
 * GitHub OAuth provider token for the signed-in user, or null when nobody
 * has signed in with GitHub in this browser. Never logs the token.
 */
export function getGitHubProviderToken(): string | null {
  return cachedGitHubToken
}
