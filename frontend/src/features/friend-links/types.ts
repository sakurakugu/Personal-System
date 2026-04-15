export type FriendLinkStatus = 'pending' | 'approved' | 'rejected'

export interface FriendLinkRecord {
  id: string
  name: string
  url: string
  description: string | null
  logo_url: string | null
  category: string | null
  status: FriendLinkStatus
  is_auto_exchange: boolean
  contact_name?: string | null
  contact_email?: string | null
  created_at?: string
  updated_at?: string
}

export interface FriendLinkListResponse {
  items: FriendLinkRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface FriendLinkAdminPayload {
  name: string
  url: string
  description: string
  logo_url: string
  category: string
  status: FriendLinkStatus
}
