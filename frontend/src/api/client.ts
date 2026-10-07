import type {
  ApiErrorBody,
  ChatQueryRequest,
  ChatQueryResponse,
  CurrentUserResponse,
  DeleteRepositoryResponse,
  IndexRepositoryRequest,
  IndexRepositoryResponse,
  LoginRequest,
  RepositoryListResponse,
  RepositoryStatusResponse,
} from './types'

// Vite bakes VITE_-prefixed env vars in at build time. Never hardcode the
// backend origin - a built bundle must be able to point at any deployment.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// Session is an HttpOnly cookie the browser attaches automatically - the
// app just needs to know when a request came back unauthenticated so it
// can drop back to the login screen. Login/logout calls themselves don't
// trigger this (a wrong password is an expected 401, not "you got logged
// out").
let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

function extractErrorMessage(body: ApiErrorBody | undefined, fallback: string): string {
  if (!body || !body.detail) return fallback
  if (typeof body.detail === 'string') return body.detail
  return body.detail.map((item) => item.msg).join('; ') || fallback
}

async function request<T>(
  path: string,
  init?: RequestInit,
  options?: { skipUnauthorizedHandler?: boolean },
): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      // 'include' (not 'same-origin'): local dev is genuinely cross-origin
      // (frontend :5173, backend :8000/8010), and the session cookie must
      // still flow there. Safe because CORS only allows explicit,
      // configured origins (never '*') with allow_credentials.
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError(`Could not reach the backend at ${API_BASE_URL}`, 0)
  }

  if (!response.ok) {
    if (response.status === 401 && !options?.skipUnauthorizedHandler) {
      onUnauthorized?.()
    }
    let body: ApiErrorBody | undefined
    try {
      body = await response.json()
    } catch {
      body = undefined
    }
    throw new ApiError(
      extractErrorMessage(body, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  login: (body: LoginRequest) =>
    request<CurrentUserResponse>(
      '/api/v1/auth/login',
      { method: 'POST', body: JSON.stringify(body) },
      { skipUnauthorizedHandler: true },
    ),

  signup: (body: LoginRequest) =>
    request<CurrentUserResponse>(
      '/api/v1/auth/signup',
      { method: 'POST', body: JSON.stringify(body) },
      { skipUnauthorizedHandler: true },
    ),

  logout: () => request<{ status: string }>('/api/v1/auth/logout', { method: 'POST' }),

  currentUser: () =>
    request<CurrentUserResponse>('/api/v1/auth/me', undefined, { skipUnauthorizedHandler: true }),

  listRepositories: () => request<RepositoryListResponse>('/api/v1/repositories'),

  indexRepository: (body: IndexRepositoryRequest) =>
    request<IndexRepositoryResponse>('/api/v1/repositories/index', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getRepository: (repositoryId: string) =>
    request<RepositoryStatusResponse>(
      `/api/v1/repositories/${encodeURIComponent(repositoryId)}`,
    ),

  deleteRepository: (repositoryId: string) =>
    request<DeleteRepositoryResponse>(
      `/api/v1/repositories/${encodeURIComponent(repositoryId)}`,
      { method: 'DELETE' },
    ),

  askQuestion: (body: ChatQueryRequest) =>
    request<ChatQueryResponse>('/api/v1/chat/query', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
