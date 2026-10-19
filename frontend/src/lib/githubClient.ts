/**
 * GitHub REST client — lists the signed-in user's own repositories.
 *
 * Uses the GitHub OAuth provider token from the Supabase session (see
 * lib/supabase.ts). Real api.github.com data only — no mock repos.
 */

import type { RepoSummary } from '../types'
import { clearGitHubProviderToken, getGitHubProviderToken } from './supabase'

/** Thrown when the GitHub token is missing or rejected — the user must reconnect. */
export class GitHubAuthError extends Error {}

interface GitHubRepo {
  name: string
  full_name: string
  language: string | null
  stargazers_count: number
  updated_at: string
  private: boolean
  fork: boolean
}

function formatUpdated(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return 'unknown'
  const seconds = Math.max(0, Math.floor((Date.now() - then) / 1000))
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  const months = Math.floor(days / 30)
  if (months < 12) return `${months}mo ago`
  return `${Math.floor(months / 12)}y ago`
}

/**
 * Fetch the authenticated GitHub user's repositories (up to one page of 100,
 * most recently updated first). Throws a descriptive error when the GitHub
 * token is missing or the API rejects the request — never returns fake data.
 */
export async function fetchGitHubRepos(): Promise<RepoSummary[]> {
  const token = getGitHubProviderToken()
  if (!token) {
    throw new GitHubAuthError(
      'No GitHub token in this session — reconnect GitHub to load your repositories.',
    )
  }
  const res = await fetch(
    'https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner,collaborator,organization_member',
    {
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${token}`,
        'X-GitHub-Api-Version': '2022-11-28',
      },
    },
  )
  if (!res.ok) {
    let detail = `GitHub API ${res.status}`
    try {
      const body = (await res.json()) as { message?: string }
      if (body.message) detail = `${detail}: ${body.message}`
    } catch {
      /* keep status-only message */
    }
    if (res.status === 401) {
      // Stale token — drop it so a fresh GitHub sign-in re-issues one.
      clearGitHubProviderToken()
      throw new GitHubAuthError(
        'GitHub API 401: Bad credentials — the GitHub token expired. Reconnect GitHub to continue.',
      )
    }
    throw new Error(detail)
  }
  const repos = (await res.json()) as GitHubRepo[]
  return repos.map((r) => ({
    owner: r.full_name.split('/')[0] ?? '',
    name: r.name,
    language: r.language ?? '—',
    stars: r.stargazers_count,
    updated: formatUpdated(r.updated_at),
    visibility: r.private ? 'private' : 'public',
    fork: r.fork,
  }))
}
