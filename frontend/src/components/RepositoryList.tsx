import { useState } from 'react'
import type { RepositoryStatusResponse } from '../api/types'
import { StatusBadge } from './StatusBadge'

interface Props {
  repositories: RepositoryStatusResponse[]
  isLoading: boolean
  loadError: string | null
  selectedId: string | null
  onSelect: (repositoryId: string) => void
  onDelete: (repositoryId: string) => Promise<void>
}

export function RepositoryList({
  repositories,
  isLoading,
  loadError,
  selectedId,
  onSelect,
  onDelete,
}: Props) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  async function handleDelete(repositoryId: string) {
    setDeletingId(repositoryId)
    try {
      await onDelete(repositoryId)
    } finally {
      setDeletingId(null)
    }
  }

  if (isLoading) {
    return <p className="p-4 font-mono text-xs text-muted">loading repositories…</p>
  }

  if (loadError) {
    return (
      <p role="alert" className="p-4 font-mono text-xs text-red">
        {loadError}
      </p>
    )
  }

  if (repositories.length === 0) {
    return (
      <p className="p-4 text-sm leading-relaxed text-muted">
        No repositories indexed yet. Add one above to start asking questions about its code.
      </p>
    )
  }

  return (
    <ul className="flex flex-1 flex-col overflow-y-auto">
      {repositories.map((repo) => {
        const isSelected = repo.repository_id === selectedId
        return (
          <li key={repo.repository_id} className="border-b border-line">
            <div
              className={`group flex items-start gap-2 border-l-2 px-4 py-3 transition-colors ${
                isSelected ? 'border-l-amber bg-panel-2' : 'border-l-transparent hover:bg-panel-2/60'
              }`}
            >
              <button
                type="button"
                onClick={() => onSelect(repo.repository_id)}
                className="flex-1 text-left"
              >
                <p className="truncate font-mono text-sm text-fg">{repo.repository_id}</p>
                <p className="mt-0.5 truncate font-mono text-xs text-muted">
                  {repo.branch} · {repo.files_indexed} files · {repo.chunks_created} chunks
                </p>
                <div className="mt-1">
                  <StatusBadge status={repo.status} />
                </div>
              </button>
              <button
                type="button"
                onClick={() => void handleDelete(repo.repository_id)}
                disabled={deletingId === repo.repository_id}
                aria-label={`Delete ${repo.repository_id}`}
                title="Delete this repository's index"
                className="mt-0.5 shrink-0 text-muted opacity-0 transition-opacity hover:text-red focus-visible:opacity-100 disabled:opacity-50 group-hover:opacity-100"
              >
                {deletingId === repo.repository_id ? (
                  <span className="font-mono text-xs">…</span>
                ) : (
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.8">
                    <path strokeLinecap="round" d="M5 7h14M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-9 0 1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13" />
                  </svg>
                )}
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
