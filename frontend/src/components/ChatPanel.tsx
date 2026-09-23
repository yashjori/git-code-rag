import { type FormEvent, useState } from 'react'
import type { RepositoryStatusResponse } from '../api/types'
import { useChat } from '../hooks/useChat'
import { renderInlineMarkdown } from '../lib/markdownLite'
import { SourceCitations } from './SourceCitation'

const EXAMPLE_QUESTIONS = [
  'Where is authentication implemented?',
  'Explain the login flow.',
  'Where is the database connection configured?',
]

interface Props {
  repository: RepositoryStatusResponse
  onBack: () => void
}

export function ChatPanel({ repository, onBack }: Props) {
  const { exchanges, ask } = useChat(repository.repository_id, repository.branch)
  const [question, setQuestion] = useState('')

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed) return
    setQuestion('')
    await ask(trimmed)
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-line px-5 py-3">
        <button
          type="button"
          onClick={onBack}
          aria-label="Back to repositories"
          className="text-muted hover:text-amber md:hidden"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <p className="font-mono text-sm text-amber">
          &gt; {repository.repository_id}{' '}
          <span className="text-muted">({repository.branch})</span>
        </p>
      </header>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {exchanges.length === 0 ? (
          <div className="mx-auto max-w-lg pt-8 text-center">
            <p className="text-sm text-muted">
              Ask anything about this repository&apos;s code. Answers are grounded in the
              indexed source, never guessed.
            </p>
            <ul className="mt-4 flex flex-col gap-2">
              {EXAMPLE_QUESTIONS.map((example) => (
                <li key={example}>
                  <button
                    type="button"
                    onClick={() => void ask(example)}
                    className="w-full rounded border border-line px-3 py-2 text-left font-mono text-xs text-muted transition-colors hover:border-amber hover:text-fg"
                  >
                    {example}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            {exchanges.map((exchange) => (
              <div key={exchange.id}>
                <p className="font-mono text-sm text-fg">
                  <span className="text-amber">$</span> {exchange.question}
                </p>

                {exchange.isPending && (
                  <p className="mt-2 font-mono text-xs text-muted" aria-live="polite">
                    thinking…
                  </p>
                )}

                {exchange.error && (
                  <p role="alert" className="mt-2 font-mono text-xs text-red">
                    {exchange.error}
                  </p>
                )}

                {exchange.answer && (
                  <div className="mt-2 max-w-3xl">
                    <p className="text-sm leading-relaxed text-fg">
                      {renderInlineMarkdown(exchange.answer)}
                    </p>
                    {exchange.sources && <SourceCitations sources={exchange.sources} />}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-line px-5 py-3">
        <span className="font-mono text-sm text-amber">$</span>
        <input
          type="text"
          name="question"
          autoComplete="off"
          aria-label="Ask a question about this repository"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about this repository"
          className="flex-1 bg-transparent font-mono text-sm text-fg placeholder:text-muted/60 focus:outline-none"
        />
        <button
          type="submit"
          disabled={!question.trim()}
          className="rounded bg-amber px-3 py-1 text-xs font-medium text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </div>
  )
}
