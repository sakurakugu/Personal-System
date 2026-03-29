import api from '../../utils/api'
import type {
  BillAccountPayload,
  BillAccountRecord,
  BillCategoryPayload,
  BillCategoryRecord,
  BillMonthSummary,
  BillRecordListResponse,
  BillRecordPayload,
  BillRecordQuery,
  BillRecordRecord,
  BillTemplateGenerateResult,
  BillTemplatePayload,
  BillTemplateRecord,
} from './types'

export async function fetchBillAccounts(): Promise<BillAccountRecord[]> {
  const { data } = await api.get<BillAccountRecord[]>('/bills/accounts')
  return data
}

export async function createBillAccount(payload: BillAccountPayload): Promise<BillAccountRecord> {
  const { data } = await api.post<BillAccountRecord>('/bills/accounts', payload)
  return data
}

export async function updateBillAccount(id: string, payload: Partial<BillAccountPayload>): Promise<BillAccountRecord> {
  const { data } = await api.patch<BillAccountRecord>(`/bills/accounts/${id}`, payload)
  return data
}

export async function deleteBillAccount(id: string): Promise<void> {
  await api.delete(`/bills/accounts/${id}`)
}

export async function fetchBillCategories(): Promise<BillCategoryRecord[]> {
  const { data } = await api.get<BillCategoryRecord[]>('/bills/categories')
  return data
}

export async function createBillCategory(payload: BillCategoryPayload): Promise<BillCategoryRecord> {
  const { data } = await api.post<BillCategoryRecord>('/bills/categories', payload)
  return data
}

export async function updateBillCategory(id: string, payload: Partial<BillCategoryPayload>): Promise<BillCategoryRecord> {
  const { data } = await api.patch<BillCategoryRecord>(`/bills/categories/${id}`, payload)
  return data
}

export async function deleteBillCategory(id: string): Promise<void> {
  await api.delete(`/bills/categories/${id}`)
}

export async function fetchBillRecords(query: BillRecordQuery = {}): Promise<BillRecordListResponse> {
  const { data } = await api.get<BillRecordListResponse>('/bills/records', { params: query })
  return data
}

export async function createBillRecord(payload: BillRecordPayload): Promise<BillRecordRecord> {
  const { data } = await api.post<BillRecordRecord>('/bills/records', payload)
  return data
}

export async function updateBillRecord(id: string, payload: Partial<BillRecordPayload>): Promise<BillRecordRecord> {
  const { data } = await api.patch<BillRecordRecord>(`/bills/records/${id}`, payload)
  return data
}

export async function deleteBillRecord(id: string): Promise<void> {
  await api.delete(`/bills/records/${id}`)
}

export async function fetchBillSummary(month?: string): Promise<BillMonthSummary> {
  const { data } = await api.get<BillMonthSummary>('/bills/summary', {
    params: month ? { month } : undefined,
  })
  return data
}

export async function fetchBillTemplates(): Promise<BillTemplateRecord[]> {
  const { data } = await api.get<BillTemplateRecord[]>('/bills/templates')
  return data
}

export async function createBillTemplate(payload: BillTemplatePayload): Promise<BillTemplateRecord> {
  const { data } = await api.post<BillTemplateRecord>('/bills/templates', payload)
  return data
}

export async function updateBillTemplate(id: string, payload: Partial<BillTemplatePayload>): Promise<BillTemplateRecord> {
  const { data } = await api.patch<BillTemplateRecord>(`/bills/templates/${id}`, payload)
  return data
}

export async function deleteBillTemplate(id: string): Promise<void> {
  await api.delete(`/bills/templates/${id}`)
}

export async function generateBillTemplates(month?: string): Promise<BillTemplateGenerateResult> {
  const { data } = await api.post<BillTemplateGenerateResult>('/bills/templates/generate', null, {
    params: month ? { month } : undefined,
  })
  return data
}
