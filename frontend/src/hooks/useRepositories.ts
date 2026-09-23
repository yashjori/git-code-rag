import { useCallback, useEffect, useState } from 'react'
import { ApiError, api } from '../api/client'
import type { IndexRepositoryRequest, RepositoryStatusResponse } from '../api/types'

export function useRepositories() {
  const [repositories, setRepositories] = useState<RepositoryStatusResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isIndexing, setIsIndexing] = useState(false)
  const [indexError, setIndexError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setLoadError(null)
    try {
      const response = await api.listRepositories()
      setRepositories(response.repositories)
    } catch (error) {
      setLoadError(error instanceof ApiError ? error.message : 'Could not load repositories.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const addRepository = useCallback(
    async (request: IndexRepositoryRequest) => {
      setIsIndexing(true)
      setIndexError(null)
      try {
        const result = await api.indexRepository(request)
        await refresh()
        return result
      } catch (error) {
        const message = error instanceof ApiError ? error.message : 'Could not index the repository.'
        setIndexError(message)
        throw error
      } finally {
        setIsIndexing(false)
      }
    },
    [refresh],
  )

  const removeRepository = useCallback(
    async (repositoryId: string) => {
      await api.deleteRepository(repositoryId)
      await refresh()
    },
    [refresh],
  )

  return {
    repositories,
    isLoading,
    loadError,
    isIndexing,
    indexError,
    refresh,
    addRepository,
    removeRepository,
  }
}
