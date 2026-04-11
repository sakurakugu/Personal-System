export type FriendLinkStatus = 'pending' | 'approved' | 'rejected'

export interface FriendLinkRecord {
  id: string
  name: string
  url: string
  description: string | null
  logo_url: string | null
  status: FriendLinkStatus
  is_auto_exchange: boolean
  contact_name?: string | null
  contact_email?: string | null
  created_at?: string
  updated_at?: string
}

export interface FriendLinkExchangePayload {
  name: string
  url: string
  description: string
  logo_url: string
  contact_email: string
  contact_name: string
  my_site_url: string
}

export interface FriendLinkExchangeResponse {
  message: string
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
  status: FriendLinkStatus
}
