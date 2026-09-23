import { type FormEvent, useState } from 'react'
import type { Provider } from '../api/types'
import { useSessionToken } from '../hooks/useSessionToken'

interface Props {
  isIndexing: boolean
  indexError: string | null
  onSubmit: (input: {
    provider: Provider
    repositoryUrl: string
    branch: string
    accessToken: string
  }) => Promise<unknown>
}

// Set VITE_ENABLE_PRIVATE_TOKENS=false at build time for deployments served
// over plain HTTP - a token typed here would otherwise travel unencrypted
// with every index request. Defaults to enabled for local dev (HTTPS not
// applicable on localhost).
const PRIVATE_TOKENS_ENABLED = import.meta.env.VITE_ENABLE_PRIVATE_TOKENS !== 'false'

export function AddRepositoryForm({ isIndexing, indexError, onSubmit }: Props) {
  const [provider, setProvider] = useState<Provider>('github')
  const [repositoryUrl, setRepositoryUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [lastResult, setLastResult] = useState<string | null>(null)
  const [accessToken, setAccessToken] = useSessionToken(provider)

  const placeholder =
    provider === 'github'
      ? 'https://github.com/org/repository'
      : 'https://dev.azure.com/org/project/_git/repository'
  const tokenLabel = provider === 'github' ? 'GitHub personal access token' : 'Azure DevOps personal access token'

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!repositoryUrl.trim() || !branch.trim()) return

    setLastResult(null)
    try {
      const result = await onSubmit({
        provider,
        repositoryUrl: repositoryUrl.trim(),
        branch: branch.trim(),
        accessToken: accessToken.trim(),
      })
      const stats = result as { files_indexed: number; chunks_created: number }
      setLastResult(`indexed ${stats.files_indexed} files, ${stats.chunks_created} chunks`)
      setRepositoryUrl('')
    } catch {
      // indexError already reflects this; nothing else to do here.
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 border-b border-line p-4">
      <fieldset className="flex flex-col gap-1.5 border-0 p-0 m-0">
        <legend className="font-mono text-xs uppercase tracking-wide text-muted">Provider</legend>
        <div role="radiogroup" aria-label="Provider" className="flex gap-1 rounded border border-line bg-panel-2 p-0.5">
          {(['github', 'azure_devops'] as const).map((value) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={provider === value}
              onClick={() => setProvider(value)}
              className={`flex-1 rounded px-2 py-1 text-xs font-medium transition-colors ${
                provider === value ? 'bg-amber text-ink' : 'text-muted hover:text-fg'
              }`}
            >
              {value === 'github' ? 'GitHub' : 'Azure DevOps'}
            </button>
          ))}
        </div>
      </fieldset>

      <label className="flex flex-col gap-1.5">
        <span className="font-mono text-xs uppercase tracking-wide text-muted">Repository URL</span>
        <input
          type="text"
          name="repositoryUrl"
          autoComplete="off"
          required
          value={repositoryUrl}
          onChange={(event) => setRepositoryUrl(event.target.value)}
          placeholder={placeholder}
          className="rounded border border-line bg-panel-2 px-2.5 py-1.5 font-mono text-sm text-fg placeholder:text-muted/60 focus-visible:border-amber"
        />
      </label>

      <label className="flex flex-col gap-1.5">
        <span className="font-mono text-xs uppercase tracking-wide text-muted">Branch</span>
        <input
          type="text"
          name="branch"
          autoComplete="off"
          required
          value={branch}
          onChange={(event) => setBranch(event.target.value)}
          className="rounded border border-line bg-panel-2 px-2.5 py-1.5 font-mono text-sm text-fg focus-visible:border-amber"
        />
      </label>

      {PRIVATE_TOKENS_ENABLED ? (
        <label className="flex flex-col gap-1.5">
          <span className="font-mono text-xs uppercase tracking-wide text-muted">
            {tokenLabel} <span className="normal-case text-muted/70">(private repos only)</span>
          </span>
          <input
            type="password"
            name="accessToken"
            autoComplete="off"
            value={accessToken}
            onChange={(event) => setAccessToken(event.target.value)}
            placeholder="Leave blank for a public repository"
            className="rounded border border-line bg-panel-2 px-2.5 py-1.5 font-mono text-sm text-fg placeholder:text-muted/60 focus-visible:border-amber"
          />
          <p className="text-[11px] leading-snug text-muted">
            Used once to clone this repository, then discarded. Never stored on the
            server. Kept only in this browser tab until you close it.
          </p>
        </label>
      ) : (
        <p className="text-[11px] leading-snug text-muted">
          Private repositories aren&apos;t supported on this deployment (no
          HTTPS, so a token would travel unencrypted). Public repositories
          only.
        </p>
      )}

      <button
        type="submit"
        disabled={isIndexing}
        className="mt-1 rounded bg-amber px-3 py-1.5 text-sm font-medium text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isIndexing ? 'Indexing…' : 'Index repository'}
      </button>

      {indexError && (
        <p role="alert" className="font-mono text-xs text-red">
          {indexError}
        </p>
      )}
      {lastResult && !indexError && (
        <p className="font-mono text-xs text-green">{lastResult}</p>
      )}
    </form>
  )
}
