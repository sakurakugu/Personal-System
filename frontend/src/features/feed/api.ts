import api from '../../shared/api'
import type { FeedListResponse, FeedQuery } from './types'

const DEFAULT_PAGE_SIZE = 10

export async function fetchFeedList(page = 1, query: FeedQuery = {}): Promise<FeedListResponse> {
  const { data } = await api.get<FeedListResponse>('/feed', {
    params: {
      page,
      page_size: DEFAULT_PAGE_SIZE,
      ...query,
    },
  })
  return data
}

