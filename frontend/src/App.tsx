import { useState } from 'react'
import { AddRepositoryForm } from './components/AddRepositoryForm'
import { ChatPanel } from './components/ChatPanel'
import { LoginPage } from './components/LoginPage'
import { RepositoryList } from './components/RepositoryList'
import { ThemeToggle } from './components/ThemeToggle'
import { useAuth } from './hooks/useAuth'
import { useRepositories } from './hooks/useRepositories'

function MainApp({ username, onLogout }: { username: string; onLogout: () => void }) {
  const {
    repositories,
    isLoading,
    loadError,
    isIndexing,
    indexError,
    addRepository,
    removeRepository,
  } = useRepositories()

  const [selectedId, setSelectedId] = useState<string | null>(null)

  // If the selected repo was deleted, .find() simply returns undefined and
  // the UI falls back to the empty state below - no effect needed to keep
  // selectedId "in sync" with the list.
  const selectedRepository = repositories.find((repo) => repo.repository_id === selectedId) ?? null

  async function handleDelete(repositoryId: string) {
    await removeRepository(repositoryId)
  }

  return (
    <div className="flex h-screen flex-col bg-ink text-fg">
      <header className="flex items-center justify-between border-b border-line px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-amber" aria-hidden />
          <h1 className="font-mono text-sm font-medium">git-code-assistant</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-muted">{username}</span>
          <button
            type="button"
            onClick={onLogout}
            className="font-mono text-xs text-muted transition-colors hover:text-amber"
          >
            Sign out
          </button>
          <ThemeToggle />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* On mobile, the repo list and the chat panel are separate full-screen
            views (master-detail); md: and up shows both side by side. */}
        <aside
          className={`${selectedRepository ? 'hidden' : 'flex'} w-full shrink-0 flex-col overflow-y-auto border-line md:flex md:w-80 md:border-r`}
        >
          <div className="border-b border-line px-4 py-3">
            <h2 className="font-mono text-xs uppercase tracking-wide text-muted">
              Add repository
            </h2>
          </div>
          <AddRepositoryForm
            isIndexing={isIndexing}
            indexError={indexError}
            onSubmit={({ provider, repositoryUrl, branch, accessToken }) =>
              addRepository({
                provider,
                repository_url: repositoryUrl,
                branch,
                access_token: accessToken || undefined,
              })
            }
          />
          <div className="border-b border-line px-4 py-3">
            <h2 className="font-mono text-xs uppercase tracking-wide text-muted">
              Repositories
            </h2>
          </div>
          <RepositoryList
            repositories={repositories}
            isLoading={isLoading}
            loadError={loadError}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onDelete={handleDelete}
          />
        </aside>

        <main className={`${selectedRepository ? 'flex' : 'hidden'} flex-1 overflow-hidden md:flex`}>
          {selectedRepository ? (
            <ChatPanel
              key={selectedRepository.repository_id}
              repository={selectedRepository}
              onBack={() => setSelectedId(null)}
            />
          ) : (
            <div className="flex h-full items-center justify-center px-6 text-center">
              <p className="max-w-sm text-sm text-muted">
                {repositories.length === 0
                  ? 'Paste a repository link on the left to index it, then ask questions about its code.'
                  : 'Select a repository on the left to ask questions about its code.'}
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

function App() {
  const { status, username, isLoggingIn, loginError, login, logout } = useAuth()

  if (status === 'checking') {
    return <div className="flex h-screen items-center justify-center bg-ink" aria-busy />
  }

  if (status === 'anonymous' || !username) {
    return <LoginPage isLoggingIn={isLoggingIn} loginError={loginError} onLogin={login} />
  }

  return <MainApp username={username} onLogout={logout} />
}

export default App
