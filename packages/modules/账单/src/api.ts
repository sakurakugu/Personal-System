import api from '@personal-system/api'
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

export async function 获取账单账户(): Promise<BillAccountRecord[]> {
  const { data } = await api.get<BillAccountRecord[]>('/bills/accounts')
  return data
}

export async function 创建账单账户(payload: BillAccountPayload): Promise<BillAccountRecord> {
  const { data } = await api.post<BillAccountRecord>('/bills/accounts', payload)
  return data
}

export async function 更新账单账户(id: string, payload: Partial<BillAccountPayload>): Promise<BillAccountRecord> {
  const { data } = await api.patch<BillAccountRecord>(`/bills/accounts/${id}`, payload)
  return data
}

export async function 删除账单账户(id: string): Promise<void> {
  await api.delete(`/bills/accounts/${id}`)
}

export async function 获取账单分类(): Promise<BillCategoryRecord[]> {
  const { data } = await api.get<BillCategoryRecord[]>('/bills/categories')
  return data
}

export async function 创建账单分类(payload: BillCategoryPayload): Promise<BillCategoryRecord> {
  const { data } = await api.post<BillCategoryRecord>('/bills/categories', payload)
  return data
}

export async function 更新账单分类(id: string, payload: Partial<BillCategoryPayload>): Promise<BillCategoryRecord> {
  const { data } = await api.patch<BillCategoryRecord>(`/bills/categories/${id}`, payload)
  return data
}

export async function 删除账单分类(id: string): Promise<void> {
  await api.delete(`/bills/categories/${id}`)
}

export async function 获取账单记录(query: BillRecordQuery = {}): Promise<BillRecordListResponse> {
  const { data } = await api.get<BillRecordListResponse>('/bills/records', { params: query })
  return data
}

export async function 创建账单记录(payload: BillRecordPayload): Promise<BillRecordRecord> {
  const { data } = await api.post<BillRecordRecord>('/bills/records', payload)
  return data
}

export async function 更新账单记录(id: string, payload: Partial<BillRecordPayload>): Promise<BillRecordRecord> {
  const { data } = await api.patch<BillRecordRecord>(`/bills/records/${id}`, payload)
  return data
}

export async function 删除账单记录(id: string): Promise<void> {
  await api.delete(`/bills/records/${id}`)
}

export async function 获取账单汇总(month?: string): Promise<BillMonthSummary> {
  const { data } = await api.get<BillMonthSummary>('/bills/summary', {
    params: month ? { month } : undefined,
  })
  return data
}

export async function 获取账单模板(): Promise<BillTemplateRecord[]> {
  const { data } = await api.get<BillTemplateRecord[]>('/bills/templates')
  return data
}

export async function 创建账单模板(payload: BillTemplatePayload): Promise<BillTemplateRecord> {
  const { data } = await api.post<BillTemplateRecord>('/bills/templates', payload)
  return data
}

export async function 更新账单模板(id: string, payload: Partial<BillTemplatePayload>): Promise<BillTemplateRecord> {
  const { data } = await api.patch<BillTemplateRecord>(`/bills/templates/${id}`, payload)
  return data
}

export async function 删除账单模板(id: string): Promise<void> {
  await api.delete(`/bills/templates/${id}`)
}

export async function 生成账单模板(month?: string): Promise<BillTemplateGenerateResult> {
  const { data } = await api.post<BillTemplateGenerateResult>('/bills/templates/generate', null, {
    params: month ? { month } : undefined,
  })
  return data
}

