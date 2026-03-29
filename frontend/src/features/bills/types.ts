export type BillAccountType = 'cash' | 'debit_card' | 'credit_card' | 'wechat' | 'alipay' | 'other'

export type BillCategoryType = 'expense' | 'income'

export type BillRecordType = 'expense' | 'income' | 'transfer'

export interface BillAccountSimpleRecord {
  id: string
  name: string
  type: BillAccountType
}

export interface BillAccountRecord extends BillAccountSimpleRecord {
  initial_balance_cent: number
  current_balance_cent: number
  note: string | null
  created_at: string
  updated_at: string
}

export interface BillCategorySimpleRecord {
  id: string
  type: BillCategoryType
  name: string
  color: string
  icon: string
}

export interface BillCategoryRecord extends BillCategorySimpleRecord {
  sort_order: number
  created_at: string
  updated_at: string
}

export interface BillRecordRecord {
  id: string
  template_id: string | null
  template_title: string | null
  type: BillRecordType
  amount_cent: number
  merchant: string | null
  note: string | null
  occurred_at: string
  account: BillAccountSimpleRecord
  target_account: BillAccountSimpleRecord | null
  category: BillCategorySimpleRecord | null
  created_at: string
  updated_at: string
}

export interface BillSummaryDailyTotal {
  date: string
  income_cent: number
  expense_cent: number
}

export interface BillSummaryCategory {
  category_id: string
  type: BillCategoryType
  name: string
  color: string
  amount_cent: number
  record_count: number
}

export interface BillMonthSummary {
  month: string
  income_cent: number
  expense_cent: number
  net_cent: number
  record_count: number
  daily_totals: BillSummaryDailyTotal[]
  category_totals: BillSummaryCategory[]
}

export interface BillTemplateRecord {
  id: string
  title: string
  type: BillRecordType
  amount_cent: number
  merchant: string | null
  note: string | null
  day_of_month: number
  is_active: boolean
  account: BillAccountSimpleRecord
  target_account: BillAccountSimpleRecord | null
  category: BillCategorySimpleRecord | null
  created_at: string
  updated_at: string
}

export interface BillTemplateGenerateResult {
  month: string
  created_count: number
  skipped_count: number
}

export interface BillRecordListResponse {
  items: BillRecordRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface BillAccountPayload {
  name: string
  type: BillAccountType
  initial_balance_cent: number
  note?: string | null
}

export interface BillCategoryPayload {
  type: BillCategoryType
  name: string
  color: string
  icon: string
  sort_order: number
}

export interface BillRecordPayload {
  type: BillRecordType
  account_id: string
  target_account_id?: string | null
  category_id?: string | null
  amount_cent: number
  merchant?: string | null
  note?: string | null
  occurred_at: string
}

export interface BillTemplatePayload {
  title: string
  type: BillRecordType
  account_id: string
  target_account_id?: string | null
  category_id?: string | null
  amount_cent: number
  merchant?: string | null
  note?: string | null
  day_of_month: number
  is_active: boolean
}

export interface BillRecordQuery {
  page?: number
  page_size?: number
  month?: string
  type?: BillRecordType | ''
  account_id?: string
  category_id?: string
  keyword?: string
}
