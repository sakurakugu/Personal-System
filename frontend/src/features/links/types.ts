export type LinkStatus = 'pending' | 'approved' | 'rejected'

export interface LinkRecord {
  id: string
  name: string
  url: string
  description: string | null
  logo_url: string | null
  status: LinkStatus
  is_auto_exchange: boolean
  contact_name?: string | null
  contact_email?: string | null
  created_at?: string
  updated_at?: string
}

export interface LinkExchangePayload {
  name: string
  url: string
  description: string
  logo_url: string
  contact_email: string
  contact_name: string
  my_site_url: string
}

export interface LinkExchangeResponse {
  message: string
}

export interface LinkListResponse {
  items: LinkRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface LinkAdminPayload {
  name: string
  url: string
  description: string
  logo_url: string
  status: LinkStatus
}
