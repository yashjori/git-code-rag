import { useCallback, useRef, useState } from 'react'
import { ApiError, api } from '../api/client'
import type { SourceReference } from '../api/types'

export interface ChatExchange {
  id: string
  question: string
  answer?: string
  sources?: SourceReference[]
  error?: string
  isPending: boolean
}

export function useChat(repositoryId: string, branch: string) {
  const [exchanges, setExchanges] = useState<ChatExchange[]>([])
  const nextId = useRef(0)

  const ask = useCallback(
    async (question: string) => {
      const id = String(nextId.current++)
      setExchanges((current) => [...current, { id, question, isPending: true }])

      try {
        const result = await api.askQuestion({ repository_id: repositoryId, branch, question })
        setExchanges((current) =>
          current.map((exchange) =>
            exchange.id === id
              ? { ...exchange, isPending: false, answer: result.answer, sources: result.sources }
              : exchange,
          ),
        )
      } catch (error) {
        const message = error instanceof ApiError ? error.message : 'Could not get an answer.'
        setExchanges((current) =>
          current.map((exchange) =>
            exchange.id === id ? { ...exchange, isPending: false, error: message } : exchange,
          ),
        )
      }
    },
    [repositoryId, branch],
  )

  return { exchanges, ask }
}
