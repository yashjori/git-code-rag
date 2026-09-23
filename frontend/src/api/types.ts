// Mirrors app/models/schemas.py exactly. Keep in sync by hand - there is no
// shared schema generation between the FastAPI backend and this frontend.

export type Provider = 'github' | 'azure_devops'

export interface LoginRequest {
  username: string
  password: string
}

export interface CurrentUserResponse {
  username: string
}

export interface IndexRepositoryRequest {
  provider: Provider
  repository_url: string
  branch: string
  // Used once for this clone, then discarded server-side; never persisted,
  // never returned in any response. Omit for a public repository.
  access_token?: string
}

export interface IndexRepositoryResponse {
  repository_id: string
  status: string
  files_scanned: number
  files_indexed: number
  chunks_created: number
  branch: string
}

export interface RepositoryStatusResponse {
  repository_id: string
  provider: string
  repository_url: string
  branch: string
  indexed_at: string
  files_indexed: number
  chunks_created: number
  status: string
}

export interface RepositoryListResponse {
  repositories: RepositoryStatusResponse[]
}

export interface DeleteRepositoryResponse {
  repository_id: string
  status: 'deleted'
}

export interface ChatQueryRequest {
  repository_id: string
  branch: string
  question: string
}

export interface SourceReference {
  file_path: string
  start_line: number
  end_line: number
}

export interface ChatQueryResponse {
  answer: string
  sources: SourceReference[]
  repository_id: string
}

export interface ApiErrorBody {
  detail: string | { msg: string; loc: (string | number)[] }[]
}
