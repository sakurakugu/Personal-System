<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import {
  ElButton,
  ElCard,
  ElCol,
  ElDatePicker,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElPagination,
  ElPopconfirm,
  ElProgress,
  ElRow,
  ElSelect,
  ElSkeleton,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import { ArrowLeft, ArrowRight, CreditCard, Plus } from '@element-plus/icons-vue'
import BaseDialog from '../../components/BaseDialog.vue'
import SegmentedSwitch from '../../components/SegmentedSwitch.vue'
import {
  createBillAccount,
  createBillCategory,
  createBillRecord,
  createBillTemplate,
  deleteBillAccount,
  deleteBillCategory,
  deleteBillRecord,
  deleteBillTemplate,
  fetchBillAccounts,
  fetchBillCategories,
  fetchBillRecords,
  fetchBillSummary,
  fetchBillTemplates,
  generateBillTemplates,
  updateBillAccount,
  updateBillCategory,
  updateBillRecord,
  updateBillTemplate,
} from '../../features/bills/api'
import type {
  BillAccountPayload,
  BillAccountRecord,
  BillAccountType,
  BillCategoryPayload,
  BillCategoryRecord,
  BillCategoryType,
  BillMonthSummary,
  BillRecordPayload,
  BillRecordRecord,
  BillRecordType,
  BillTemplatePayload,
  BillTemplateRecord,
} from '../../features/bills/types'
import { getApiErrorMessage } from '../../utils/api'

interface BillRecordFormState {
  type: BillRecordType
  account_id: string
  target_account_id: string
  category_id: string
  amount_yuan: number | null
  merchant: string
  note: string
  occurred_at: Date | null
}

interface BillAccountFormState {
  name: string
  type: BillAccountType
  initial_balance_yuan: number | null
  note: string
}

interface BillCategoryFormState {
  type: BillCategoryType
  name: string
  color: string
  icon: string
  sort_order: number
}

interface BillTemplateFormState {
  title: string
  type: BillRecordType
  account_id: string
  target_account_id: string
  category_id: string
  amount_yuan: number | null
  merchant: string
  note: string
  day_of_month: number
  is_active: boolean
}

const pageLoading = ref(true)
const tableLoading = ref(false)
const recordSaving = ref(false)
const accountSaving = ref(false)
const categorySaving = ref(false)
const templateSaving = ref(false)
const templateGenerating = ref(false)

const month = ref(getCurrentMonthValue())
const accounts = ref<BillAccountRecord[]>([])
const categories = ref<BillCategoryRecord[]>([])
const templates = ref<BillTemplateRecord[]>([])
const records = ref<BillRecordRecord[]>([])
const summary = ref<BillMonthSummary>(createEmptySummary(month.value))
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
  pages: 0,
})
const filters = ref({
  type: '' as BillRecordType | '',
  account_id: '',
  category_id: '',
  keyword: '',
})

const showRecordDialog = ref(false)
const showAccountDialog = ref(false)
const showCategoryDialog = ref(false)
const showTemplateDialog = ref(false)
const editingRecordId = ref('')
const editingAccountId = ref('')
const editingCategoryId = ref('')
const editingTemplateId = ref('')
const recordAmountInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)
const accountNameInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const categoryNameInputRef = ref<InstanceType<typeof ElInput> | null>(null)
const templateAmountInputRef = ref<InstanceType<typeof ElInputNumber> | null>(null)

const recordForm = ref<BillRecordFormState>(createEmptyRecordForm())
const accountForm = ref<BillAccountFormState>(createEmptyAccountForm())
const categoryForm = ref<BillCategoryFormState>(createEmptyCategoryForm())
const templateForm = ref<BillTemplateFormState>(createEmptyTemplateForm())

function focusRecordAmountInput() {
  void nextTick(() => {
    recordAmountInputRef.value?.focus()
  })
}

function focusAccountNameInput() {
  void nextTick(() => {
    accountNameInputRef.value?.focus()
    accountNameInputRef.value?.input?.focus()
  })
}

function focusCategoryNameInput() {
  void nextTick(() => {
    categoryNameInputRef.value?.focus()
    categoryNameInputRef.value?.input?.focus()
  })
}

function focusTemplateAmountInput() {
  void nextTick(() => {
    templateAmountInputRef.value?.focus()
  })
}

const accountTypeLabelMap: Record<BillAccountType, string> = {
  cash: '现金',
  debit_card: '借记卡',
  credit_card: '信用卡',
  wechat: '微信',
  alipay: '支付宝',
  other: '其他',
}

const recordTypeLabelMap: Record<BillRecordType, string> = {
  expense: '支出',
  income: '收入',
  transfer: '转账',
}

const recordTypeTagMap: Record<BillRecordType, 'danger' | 'success' | 'warning'> = {
  expense: 'danger',
  income: 'success',
  transfer: 'warning',
}

const accountTypeOptions: Array<{ label: string; value: BillAccountType }> = [
  { label: '现金', value: 'cash' },
  { label: '借记卡', value: 'debit_card' },
  { label: '信用卡', value: 'credit_card' },
  { label: '微信', value: 'wechat' },
  { label: '支付宝', value: 'alipay' },
  { label: '其他', value: 'other' },
]

const recordTypeOptions: Array<{ label: string; value: BillRecordType }> = [
  { label: '支出', value: 'expense' },
  { label: '收入', value: 'income' },
  { label: '转账', value: 'transfer' },
]

const categoryTypeOptions: Array<{ label: string; value: BillCategoryType }> = [
  { label: '支出', value: 'expense' },
  { label: '收入', value: 'income' },
]

const expenseCategories = computed(() => categories.value.filter((item) => item.type === 'expense'))
const incomeCategories = computed(() => categories.value.filter((item) => item.type === 'income'))

const availableRecordCategories = computed(() => {
  if (recordForm.value.type === 'income') {
    return incomeCategories.value
  }
  if (recordForm.value.type === 'expense') {
    return expenseCategories.value
  }
  return []
})

const availableTemplateCategories = computed(() => {
  if (templateForm.value.type === 'income') {
    return incomeCategories.value
  }
  if (templateForm.value.type === 'expense') {
    return expenseCategories.value
  }
  return []
})

const filteredCategoryOptions = computed(() => {
  if (filters.value.type === 'income') {
    return incomeCategories.value
  }
  if (filters.value.type === 'expense') {
    return expenseCategories.value
  }
  return categories.value
})

const incomeCategoryTotals = computed(() => summary.value.category_totals.filter((item) => item.type === 'income'))
const expenseCategoryTotals = computed(() => summary.value.category_totals.filter((item) => item.type === 'expense'))

const summaryCards = computed(() => [
  {
    key: 'income',
    title: '本月收入',
    value: formatCurrency(summary.value.income_cent),
    description: `${summary.value.month} 已入账收入`,
  },
  {
    key: 'expense',
    title: '本月支出',
    value: formatCurrency(summary.value.expense_cent),
    description: `${summary.value.month} 已记支出`,
  },
  {
    key: 'net',
    title: '本月结余',
    value: formatCurrency(summary.value.net_cent),
    description: '收入减去支出后的净额',
  },
  {
    key: 'records',
    title: '本月笔数',
    value: `${summary.value.record_count}`,
    description: '包含收入、支出和转账',
  },
])

watch(
  () => recordForm.value.type,
  (value) => {
    recordForm.value.amount_yuan = normalizeAmountByType(value, recordForm.value.amount_yuan)
    if (value === 'transfer') {
      recordForm.value.category_id = ''
      if (!recordForm.value.target_account_id && accounts.value.length > 1) {
        const nextAccount = accounts.value.find((item) => item.id !== recordForm.value.account_id)
        recordForm.value.target_account_id = nextAccount?.id ?? ''
      }
      return
    }

    recordForm.value.target_account_id = ''
    if (!availableRecordCategories.value.some((item) => item.id === recordForm.value.category_id)) {
      recordForm.value.category_id = availableRecordCategories.value[0]?.id ?? ''
    }
  },
)

watch(
  () => recordForm.value.amount_yuan,
  (value) => {
    syncFormTypeByAmount('record', value)
  },
)

watch(
  () => templateForm.value.type,
  (value) => {
    templateForm.value.amount_yuan = normalizeAmountByType(value, templateForm.value.amount_yuan)
    if (value === 'transfer') {
      templateForm.value.category_id = ''
      if (!templateForm.value.target_account_id && accounts.value.length > 1) {
        const nextAccount = accounts.value.find((item) => item.id !== templateForm.value.account_id)
        templateForm.value.target_account_id = nextAccount?.id ?? ''
      }
      return
    }

    templateForm.value.target_account_id = ''
    if (!availableTemplateCategories.value.some((item) => item.id === templateForm.value.category_id)) {
      templateForm.value.category_id = availableTemplateCategories.value[0]?.id ?? ''
    }
  },
)

watch(
  () => templateForm.value.amount_yuan,
  (value) => {
    syncFormTypeByAmount('template', value)
  },
)

function createEmptySummary(monthValue: string): BillMonthSummary {
  return {
    month: monthValue,
    income_cent: 0,
    expense_cent: 0,
    net_cent: 0,
    record_count: 0,
    daily_totals: [],
    category_totals: [],
  }
}

function getCurrentMonthValue(): string {
  const now = new Date()
  const year = now.getFullYear()
  const currentMonth = String(now.getMonth() + 1).padStart(2, '0')
  return `${year}-${currentMonth}`
}

function createEmptyRecordForm(): BillRecordFormState {
  return {
    type: 'expense',
    account_id: '',
    target_account_id: '',
    category_id: '',
    amount_yuan: null,
    merchant: '',
    note: '',
    occurred_at: new Date(),
  }
}

function createEmptyAccountForm(): BillAccountFormState {
  return {
    name: '',
    type: 'cash',
    initial_balance_yuan: 0,
    note: '',
  }
}

function createEmptyCategoryForm(): BillCategoryFormState {
  return {
    type: 'expense',
    name: '',
    color: '#94a3b8',
    icon: 'folder',
    sort_order: 0,
  }
}

function createEmptyTemplateForm(): BillTemplateFormState {
  return {
    title: '',
    type: 'expense',
    account_id: '',
    target_account_id: '',
    category_id: '',
    amount_yuan: null,
    merchant: '',
    note: '',
    day_of_month: new Date().getDate(),
    is_active: true,
  }
}

function centToYuan(value: number): number {
  return Number((value / 100).toFixed(2))
}

function amountCentToFormYuan(type: BillRecordType, value: number): number {
  return normalizeAmountByType(type, centToYuan(value)) ?? 0
}

function yuanToCent(value: number | null): number {
  return Math.round((value ?? 0) * 100)
}

function normalizeAmountByType(type: BillRecordType, value: number | null): number | null {
  if (value === null) {
    return null
  }
  const normalized = Number(Math.abs(value).toFixed(2))
  if (type === 'expense') {
    return -normalized
  }
  return normalized
}

function getPreviewColor(value: string): string {
  const normalized = value.trim()
  if (!normalized) {
    return '#94a3b8'
  }
  if (typeof document === 'undefined') {
    return normalized
  }
  const preview = document.createElement('span')
  preview.style.color = ''
  preview.style.color = normalized
  return preview.style.color ? normalized : '#94a3b8'
}

function getPreviewIcon(value: string): string {
  const normalized = value.trim()
  return normalized || 'folder'
}

function syncFormTypeByAmount(formKind: 'record' | 'template', value: number | null) {
  if (value === null || value === 0) {
    return
  }

  const targetForm = formKind === 'record' ? recordForm.value : templateForm.value
  if (targetForm.type === 'transfer') {
    if (value < 0) {
      targetForm.amount_yuan = Math.abs(value)
    }
    return
  }

  if (value < 0 && targetForm.type !== 'expense') {
    targetForm.type = 'expense'
    return
  }
  if (value > 0 && targetForm.type !== 'income') {
    targetForm.type = 'income'
  }
}

function trimToNull(value: string): string | null {
  const normalized = value.trim()
  return normalized || null
}

function formatCurrency(cents: number): string {
  const sign = cents < 0 ? '-' : ''
  return `${sign}¥${(Math.abs(cents) / 100).toFixed(2)}`
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN')
}

function formatAccountType(value: BillAccountType): string {
  return accountTypeLabelMap[value]
}

function formatRecordType(value: BillRecordType): string {
  return recordTypeLabelMap[value]
}

function formatTemplateSchedule(template: BillTemplateRecord): string {
  return `每月 ${template.day_of_month} 号 · ${template.is_active ? '启用中' : '已停用'}`
}

function formatTemplateAccountLine(template: BillTemplateRecord): string {
  if (template.type === 'transfer') {
    return `${template.account.name} → ${template.target_account?.name ?? '未设置转入账户'}`
  }
  return `${template.account.name} · ${template.category?.name ?? '未设置分类'}`
}

function shiftMonth(offset: number) {
  const [yearValue, monthValue] = month.value.split('-').map(Number)
  if (!yearValue || !monthValue) {
    return
  }
  const next = new Date(yearValue, monthValue - 1 + offset, 1)
  const nextYear = next.getFullYear()
  const nextMonth = String(next.getMonth() + 1).padStart(2, '0')
  month.value = `${nextYear}-${nextMonth}`
  void reloadSummaryAndRecords(1)
}

function getCategoryRatio(itemAmount: number, totalAmount: number): number {
  if (!totalAmount) {
    return 0
  }
  return Number(((itemAmount / totalAmount) * 100).toFixed(2))
}

function buildRecordQuery(page = 1) {
  return {
    page,
    page_size: pagination.value.pageSize,
    month: month.value,
    type: filters.value.type || undefined,
    account_id: filters.value.account_id || undefined,
    category_id: filters.value.category_id || undefined,
    keyword: filters.value.keyword.trim() || undefined,
  }
}

function resetRecordFormDefaults() {
  recordForm.value = createEmptyRecordForm()
  recordForm.value.account_id = accounts.value[0]?.id ?? ''
  recordForm.value.category_id = expenseCategories.value[0]?.id ?? ''
}

function resetTemplateFormDefaults() {
  templateForm.value = createEmptyTemplateForm()
  templateForm.value.account_id = accounts.value[0]?.id ?? ''
  templateForm.value.category_id = expenseCategories.value[0]?.id ?? ''
}

function handleMonthChange() {
  void reloadSummaryAndRecords(1)
}

function handleFilterChange() {
  if (!filteredCategoryOptions.value.some((item) => item.id === filters.value.category_id)) {
    filters.value.category_id = ''
  }
  void loadRecords(1)
}

async function loadCollections() {
  const [accountData, categoryData, templateData] = await Promise.all([
    fetchBillAccounts(),
    fetchBillCategories(),
    fetchBillTemplates(),
  ])
  accounts.value = accountData
  categories.value = categoryData
  templates.value = templateData
}

async function loadSummary() {
  summary.value = await fetchBillSummary(month.value)
}

async function loadRecords(page = 1) {
  tableLoading.value = true
  try {
    const data = await fetchBillRecords(buildRecordQuery(page))
    records.value = data.items
    pagination.value = {
      page: data.page,
      pageSize: data.page_size,
      total: data.total,
      pages: data.pages,
    }
  } finally {
    tableLoading.value = false
  }
}

async function reloadSummaryAndRecords(page = pagination.value.page) {
  await Promise.all([
    loadSummary(),
    loadRecords(page),
  ])
}

async function reloadAll(page = pagination.value.page) {
  await Promise.all([
    loadCollections(),
    loadSummary(),
    loadRecords(page),
  ])
}

function openCreateRecordDialog() {
  editingRecordId.value = ''
  resetRecordFormDefaults()
  showRecordDialog.value = true
}

function openEditRecordDialog(record: BillRecordRecord) {
  editingRecordId.value = record.id
  recordForm.value = {
    type: record.type,
    account_id: record.account.id,
    target_account_id: record.target_account?.id ?? '',
    category_id: record.category?.id ?? '',
    amount_yuan: amountCentToFormYuan(record.type, record.amount_cent),
    merchant: record.merchant ?? '',
    note: record.note ?? '',
    occurred_at: new Date(record.occurred_at),
  }
  showRecordDialog.value = true
}

function openCreateAccountDialog() {
  editingAccountId.value = ''
  accountForm.value = createEmptyAccountForm()
  showAccountDialog.value = true
}

function openEditAccountDialog(account: BillAccountRecord) {
  editingAccountId.value = account.id
  accountForm.value = {
    name: account.name,
    type: account.type,
    initial_balance_yuan: centToYuan(account.initial_balance_cent),
    note: account.note ?? '',
  }
  showAccountDialog.value = true
}

function openCreateCategoryDialog() {
  editingCategoryId.value = ''
  categoryForm.value = createEmptyCategoryForm()
  showCategoryDialog.value = true
}

function openEditCategoryDialog(category: BillCategoryRecord) {
  editingCategoryId.value = category.id
  categoryForm.value = {
    type: category.type,
    name: category.name,
    color: category.color,
    icon: category.icon,
    sort_order: category.sort_order,
  }
  showCategoryDialog.value = true
}

function openCreateTemplateDialog() {
  editingTemplateId.value = ''
  resetTemplateFormDefaults()
  showTemplateDialog.value = true
}

function openEditTemplateDialog(template: BillTemplateRecord) {
  editingTemplateId.value = template.id
  templateForm.value = {
    title: template.title,
    type: template.type,
    account_id: template.account.id,
    target_account_id: template.target_account?.id ?? '',
    category_id: template.category?.id ?? '',
    amount_yuan: amountCentToFormYuan(template.type, template.amount_cent),
    merchant: template.merchant ?? '',
    note: template.note ?? '',
    day_of_month: template.day_of_month,
    is_active: template.is_active,
  }
  showTemplateDialog.value = true
}

async function saveRecord() {
  if (!recordForm.value.account_id) {
    ElMessage.error('请选择账户')
    return
  }
  if (!recordForm.value.amount_yuan || Math.abs(recordForm.value.amount_yuan) <= 0) {
    ElMessage.error('请输入正确的金额')
    return
  }
  if (!recordForm.value.occurred_at) {
    ElMessage.error('请选择记账时间')
    return
  }
  if (recordForm.value.type === 'transfer') {
    if (!recordForm.value.target_account_id) {
      ElMessage.error('请选择转入账户')
      return
    }
  } else if (!recordForm.value.category_id) {
    ElMessage.error('请选择分类')
    return
  }

  const payload: BillRecordPayload = {
    type: recordForm.value.type,
    account_id: recordForm.value.account_id,
    target_account_id: recordForm.value.type === 'transfer' ? recordForm.value.target_account_id || null : null,
    category_id: recordForm.value.type === 'transfer' ? null : recordForm.value.category_id || null,
    amount_cent: yuanToCent(Math.abs(recordForm.value.amount_yuan)),
    merchant: trimToNull(recordForm.value.merchant),
    note: trimToNull(recordForm.value.note),
    occurred_at: recordForm.value.occurred_at.toISOString(),
  }

  recordSaving.value = true
  try {
    if (editingRecordId.value) {
      await updateBillRecord(editingRecordId.value, payload)
      ElMessage.success('账单已更新')
    } else {
      await createBillRecord(payload)
      ElMessage.success('账单已创建')
    }
    showRecordDialog.value = false
    await reloadAll(1)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存账单失败'))
  } finally {
    recordSaving.value = false
  }
}

async function saveAccount() {
  if (!accountForm.value.name.trim()) {
    ElMessage.error('请输入账户名称')
    return
  }

  const payload: BillAccountPayload = {
    name: accountForm.value.name.trim(),
    type: accountForm.value.type,
    initial_balance_cent: yuanToCent(accountForm.value.initial_balance_yuan),
    note: trimToNull(accountForm.value.note),
  }

  accountSaving.value = true
  try {
    if (editingAccountId.value) {
      await updateBillAccount(editingAccountId.value, payload)
      ElMessage.success('账户已更新')
    } else {
      await createBillAccount(payload)
      ElMessage.success('账户已创建')
    }
    showAccountDialog.value = false
    await reloadAll()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存账户失败'))
  } finally {
    accountSaving.value = false
  }
}

async function saveCategory() {
  if (!categoryForm.value.name.trim()) {
    ElMessage.error('请输入分类名称')
    return
  }

  const payload: BillCategoryPayload = {
    type: categoryForm.value.type,
    name: categoryForm.value.name.trim(),
    color: categoryForm.value.color.trim() || '#94a3b8',
    icon: categoryForm.value.icon.trim() || 'folder',
    sort_order: categoryForm.value.sort_order,
  }

  categorySaving.value = true
  try {
    if (editingCategoryId.value) {
      await updateBillCategory(editingCategoryId.value, payload)
      ElMessage.success('分类已更新')
    } else {
      await createBillCategory(payload)
      ElMessage.success('分类已创建')
    }
    showCategoryDialog.value = false
    await reloadAll()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存分类失败'))
  } finally {
    categorySaving.value = false
  }
}

async function saveTemplate() {
  if (!templateForm.value.title.trim()) {
    ElMessage.error('请输入模板标题')
    return
  }
  if (!templateForm.value.account_id) {
    ElMessage.error('请选择账户')
    return
  }
  if (!templateForm.value.amount_yuan || Math.abs(templateForm.value.amount_yuan) <= 0) {
    ElMessage.error('请输入正确的金额')
    return
  }
  if (templateForm.value.type === 'transfer') {
    if (!templateForm.value.target_account_id) {
      ElMessage.error('请选择转入账户')
      return
    }
  } else if (!templateForm.value.category_id) {
    ElMessage.error('请选择分类')
    return
  }

  const payload: BillTemplatePayload = {
    title: templateForm.value.title.trim(),
    type: templateForm.value.type,
    account_id: templateForm.value.account_id,
    target_account_id: templateForm.value.type === 'transfer' ? templateForm.value.target_account_id || null : null,
    category_id: templateForm.value.type === 'transfer' ? null : templateForm.value.category_id || null,
    amount_cent: yuanToCent(Math.abs(templateForm.value.amount_yuan)),
    merchant: trimToNull(templateForm.value.merchant),
    note: trimToNull(templateForm.value.note),
    day_of_month: templateForm.value.day_of_month,
    is_active: templateForm.value.is_active,
  }

  templateSaving.value = true
  try {
    if (editingTemplateId.value) {
      await updateBillTemplate(editingTemplateId.value, payload)
      ElMessage.success('固定账单模板已更新')
    } else {
      await createBillTemplate(payload)
      ElMessage.success('固定账单模板已创建')
    }
    showTemplateDialog.value = false
    await reloadAll()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存固定账单模板失败'))
  } finally {
    templateSaving.value = false
  }
}

async function handleDeleteRecord(id: string) {
  try {
    await deleteBillRecord(id)
    ElMessage.success('账单已删除')
    const nextPage = records.value.length === 1 && pagination.value.page > 1 ? pagination.value.page - 1 : pagination.value.page
    await reloadAll(nextPage)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除账单失败'))
  }
}

async function handleDeleteAccount(id: string) {
  try {
    await deleteBillAccount(id)
    ElMessage.success('账户已删除')
    await reloadAll()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除账户失败'))
  }
}

async function handleDeleteCategory(id: string) {
  try {
    await deleteBillCategory(id)
    ElMessage.success('分类已删除')
    await reloadAll()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除分类失败'))
  }
}

async function handleDeleteTemplate(id: string) {
  try {
    await deleteBillTemplate(id)
    ElMessage.success('固定账单模板已删除')
    await reloadAll()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '删除固定账单模板失败'))
  }
}

async function handleGenerateTemplates() {
  templateGenerating.value = true
  try {
    const result = await generateBillTemplates(month.value)
    ElMessage.success(`已补齐 ${result.month} 固定账单：新增 ${result.created_count} 条，跳过 ${result.skipped_count} 条`)
    await reloadAll()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '补齐固定账单失败'))
  } finally {
    templateGenerating.value = false
  }
}

onMounted(async () => {
  try {
    await reloadAll(1)
    resetRecordFormDefaults()
  } finally {
    pageLoading.value = false
  }
})
</script>

<template>
  <div class="bills-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">
          <ElIcon><CreditCard /></ElIcon>
          <span>账单管理</span>
        </h2>
        <p class="page-subtitle">账户、分类、流水、固定账单和月汇总都集中在这里维护。</p>
      </div>
      <div class="page-actions">
        <ElButton @click="openCreateAccountDialog">新建账户</ElButton>
        <ElButton @click="openCreateCategoryDialog">新建分类</ElButton>
        <ElButton @click="openCreateTemplateDialog">新建固定账单</ElButton>
        <ElButton type="primary" @click="openCreateRecordDialog">
          <ElIcon><Plus /></ElIcon>
          <span>记一笔</span>
        </ElButton>
      </div>
    </div>

    <ElSkeleton :loading="pageLoading" animated>
      <div class="month-toolbar">
        <ElButton text @click="shiftMonth(-1)">
          <ElIcon><ArrowLeft /></ElIcon>
        </ElButton>
        <ElDatePicker
          v-model="month"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择月份"
          @change="handleMonthChange"
        />
        <ElButton :loading="templateGenerating" @click="handleGenerateTemplates">补齐固定账单</ElButton>
        <ElButton text @click="shiftMonth(1)">
          <ElIcon><ArrowRight /></ElIcon>
        </ElButton>
      </div>

      <ElRow :gutter="16" class="summary-grid">
        <ElCol v-for="card in summaryCards" :key="card.key" :xs="24" :sm="12" :xl="6" class="summary-grid__item">
          <ElCard class="summary-card">
            <div class="summary-card__title">{{ card.title }}</div>
            <div class="summary-card__value">{{ card.value }}</div>
            <div class="summary-card__desc">{{ card.description }}</div>
          </ElCard>
        </ElCol>
      </ElRow>

      <ElRow :gutter="16" class="content-grid">
        <ElCol :xs="24" :xl="16">
          <ElCard class="panel-card" shadow="never">
            <template #header>
              <div class="panel-header">
                <span>账单流水</span>
              </div>
            </template>

            <div class="filters">
              <ElSelect v-model="filters.type" clearable placeholder="全部类型" class="filter-item" @change="handleFilterChange">
                <ElOption label="支出" value="expense" />
                <ElOption label="收入" value="income" />
                <ElOption label="转账" value="transfer" />
              </ElSelect>
              <ElSelect v-model="filters.account_id" clearable placeholder="全部账户" class="filter-item" @change="handleFilterChange">
                <ElOption v-for="account in accounts" :key="account.id" :label="account.name" :value="account.id" />
              </ElSelect>
              <ElSelect v-model="filters.category_id" clearable placeholder="全部分类" class="filter-item" @change="handleFilterChange">
                <ElOption v-for="category in filteredCategoryOptions" :key="category.id" :label="category.name" :value="category.id" />
              </ElSelect>
              <ElInput
                v-model="filters.keyword"
                class="filter-item filter-keyword"
                placeholder="搜索商户或备注"
                clearable
                @keyup.enter="handleFilterChange"
                @clear="handleFilterChange"
              />
              <ElButton @click="handleFilterChange">筛选</ElButton>
            </div>

            <ElTable v-loading="tableLoading" :data="records" border stripe class="records-table">
              <ElTableColumn label="时间" min-width="170">
                <template #default="{ row }: { row: BillRecordRecord }">
                  {{ formatDateTime(row.occurred_at) }}
                </template>
              </ElTableColumn>
              <ElTableColumn label="类型" width="88">
                <template #default="{ row }: { row: BillRecordRecord }">
                  <div class="record-type-cell">
                    <ElTag :type="recordTypeTagMap[row.type]" size="small">{{ formatRecordType(row.type) }}</ElTag>
                    <ElTag v-if="row.template_id" size="small" effect="plain">固定</ElTag>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="金额" width="128">
                <template #default="{ row }: { row: BillRecordRecord }">
                  <span :class="['amount-text', `is-${row.type}`]">{{ formatCurrency(row.amount_cent) }}</span>
                </template>
              </ElTableColumn>
              <ElTableColumn label="账户" min-width="140">
                <template #default="{ row }: { row: BillRecordRecord }">
                  <div>{{ row.account.name }}</div>
                  <div v-if="row.target_account" class="sub-text">转入 {{ row.target_account.name }}</div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="分类" min-width="120">
                <template #default="{ row }: { row: BillRecordRecord }">
                  <span v-if="row.category">{{ row.category.name }}</span>
                  <span v-else class="sub-text">转账</span>
                </template>
              </ElTableColumn>
              <ElTableColumn label="商户/备注" min-width="180">
                <template #default="{ row }: { row: BillRecordRecord }">
                  <div>{{ row.merchant || '未填写商户' }}</div>
                  <div v-if="row.template_title" class="sub-text">固定模板：{{ row.template_title }}</div>
                  <div v-if="row.note" class="sub-text">{{ row.note }}</div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="操作" width="120" fixed="right">
                <template #default="{ row }: { row: BillRecordRecord }">
                  <div class="table-actions">
                    <ElButton text @click="openEditRecordDialog(row)">编辑</ElButton>
                    <ElPopconfirm title="确定删除这条账单？" @confirm="handleDeleteRecord(row.id)">
                      <template #reference>
                        <ElButton text type="danger">删除</ElButton>
                      </template>
                    </ElPopconfirm>
                  </div>
                </template>
              </ElTableColumn>
            </ElTable>

            <div v-if="pagination.pages > 1" class="pagination-wrap">
              <ElPagination
                :current-page="pagination.page"
                :page-count="pagination.pages"
                layout="prev, pager, next"
                @update:current-page="loadRecords"
              />
            </div>
          </ElCard>
        </ElCol>

        <ElCol :xs="24" :xl="8">
          <ElCard class="panel-card" shadow="never">
            <template #header>
              <div class="panel-header">
                <span>账户余额</span>
              </div>
            </template>

            <div v-if="accounts.length" class="stack-list">
              <div v-for="account in accounts" :key="account.id" class="stack-item">
                <div class="stack-item__main">
                  <div class="stack-item__title">
                    <span>{{ account.name }}</span>
                    <ElTag size="small" effect="plain">{{ formatAccountType(account.type) }}</ElTag>
                  </div>
                  <div class="stack-item__value">{{ formatCurrency(account.current_balance_cent) }}</div>
                  <div v-if="account.note" class="sub-text">{{ account.note }}</div>
                </div>
                <div class="stack-item__actions">
                  <ElButton text @click="openEditAccountDialog(account)">编辑</ElButton>
                  <ElPopconfirm title="确定删除这个账户？" @confirm="handleDeleteAccount(account.id)">
                    <template #reference>
                      <ElButton text type="danger">删除</ElButton>
                    </template>
                  </ElPopconfirm>
                </div>
              </div>
            </div>
            <ElEmpty v-else description="暂无账户" />
          </ElCard>

          <ElCard class="panel-card" shadow="never">
            <template #header>
              <div class="panel-header">
                <span>分类排行</span>
              </div>
            </template>

            <div v-if="summary.category_totals.length" class="category-section">
              <div v-if="expenseCategoryTotals.length" class="category-block">
                <div class="category-block__title">支出分类</div>
                <div v-for="item in expenseCategoryTotals" :key="item.category_id" class="category-total-item">
                  <div class="category-total-item__head">
                    <div class="category-total-item__name">
                      <span class="category-color-dot" :style="{ backgroundColor: item.color }" />
                      <span>{{ item.name }}</span>
                    </div>
                    <span>{{ formatCurrency(item.amount_cent) }}</span>
                  </div>
                  <ElProgress :percentage="getCategoryRatio(item.amount_cent, summary.expense_cent)" :show-text="false" :stroke-width="8" />
                </div>
              </div>

              <div v-if="incomeCategoryTotals.length" class="category-block">
                <div class="category-block__title">收入分类</div>
                <div v-for="item in incomeCategoryTotals" :key="item.category_id" class="category-total-item">
                  <div class="category-total-item__head">
                    <div class="category-total-item__name">
                      <span class="category-color-dot" :style="{ backgroundColor: item.color }" />
                      <span>{{ item.name }}</span>
                    </div>
                    <span>{{ formatCurrency(item.amount_cent) }}</span>
                  </div>
                  <ElProgress :percentage="getCategoryRatio(item.amount_cent, summary.income_cent)" :show-text="false" :stroke-width="8" />
                </div>
              </div>
            </div>
            <ElEmpty v-else description="本月还没有分类汇总" />
          </ElCard>

          <ElCard class="panel-card" shadow="never">
            <template #header>
              <div class="panel-header">
                <span>固定账单</span>
                <ElButton text @click="openCreateTemplateDialog">新增</ElButton>
              </div>
            </template>

            <div v-if="templates.length" class="stack-list">
              <div v-for="template in templates" :key="template.id" class="stack-item">
                <div class="stack-item__main">
                  <div class="stack-item__title">
                    <span>{{ template.title }}</span>
                    <ElTag :type="recordTypeTagMap[template.type]" size="small">{{ formatRecordType(template.type) }}</ElTag>
                    <ElTag v-if="!template.is_active" size="small" effect="plain">已停用</ElTag>
                  </div>
                  <div class="stack-item__value">{{ formatCurrency(template.amount_cent) }}</div>
                  <div class="sub-text">{{ formatTemplateSchedule(template) }}</div>
                  <div class="sub-text">{{ formatTemplateAccountLine(template) }}</div>
                  <div v-if="template.merchant" class="sub-text">商户：{{ template.merchant }}</div>
                  <div v-if="template.note" class="sub-text">{{ template.note }}</div>
                </div>
                <div class="stack-item__actions">
                  <ElButton text @click="openEditTemplateDialog(template)">编辑</ElButton>
                  <ElPopconfirm title="确定删除这个固定账单模板？" @confirm="handleDeleteTemplate(template.id)">
                    <template #reference>
                      <ElButton text type="danger">删除</ElButton>
                    </template>
                  </ElPopconfirm>
                </div>
              </div>
            </div>
            <ElEmpty v-else description="暂无固定账单模板" />
          </ElCard>

          <ElCard class="panel-card" shadow="never">
            <template #header>
              <div class="panel-header">
                <span>分类管理</span>
              </div>
            </template>

            <div v-if="categories.length" class="stack-list">
              <div v-for="category in categories" :key="category.id" class="stack-item">
                <div class="stack-item__main">
                  <div class="stack-item__title">
                    <div class="category-title">
                      <span class="category-color-dot" :style="{ backgroundColor: category.color }" />
                      <span>{{ category.name }}</span>
                    </div>
                    <ElTag size="small" :type="category.type === 'expense' ? 'danger' : 'success'" effect="plain">
                      {{ category.type === 'expense' ? '支出' : '收入' }}
                    </ElTag>
                  </div>
                  <div class="sub-text">排序 {{ category.sort_order }} · 图标 {{ category.icon }}</div>
                </div>
                <div class="stack-item__actions">
                  <ElButton text @click="openEditCategoryDialog(category)">编辑</ElButton>
                  <ElPopconfirm title="确定删除这个分类？" @confirm="handleDeleteCategory(category.id)">
                    <template #reference>
                      <ElButton text type="danger">删除</ElButton>
                    </template>
                  </ElPopconfirm>
                </div>
              </div>
            </div>
            <ElEmpty v-else description="暂无分类" />
          </ElCard>
        </ElCol>
      </ElRow>
    </ElSkeleton>

    <BaseDialog
      v-model="showRecordDialog"
      :title="editingRecordId ? '编辑账单' : '新增账单'"
      width="560px"
      @opened="focusRecordAmountInput"
    >
      <ElForm label-position="top" @submit.prevent="saveRecord">
        <ElFormItem label="类型">
          <SegmentedSwitch
            v-model="recordForm.type"
            aria-label="账单类型"
            :options="recordTypeOptions"
            full-width
          />
        </ElFormItem>
        <ElFormItem label="金额">
          <ElInputNumber
            ref="recordAmountInputRef"
            v-model="recordForm.amount_yuan"
            :step="0.01"
            :precision="2"
            style="width: 100%"
          />
        </ElFormItem>
        <ElFormItem label="账户">
          <ElSelect v-model="recordForm.account_id" style="width: 100%">
            <ElOption v-for="account in accounts" :key="account.id" :label="account.name" :value="account.id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem v-if="recordForm.type === 'transfer'" label="转入账户">
          <ElSelect v-model="recordForm.target_account_id" style="width: 100%">
            <ElOption v-for="account in accounts" :key="account.id" :label="account.name" :value="account.id" :disabled="account.id === recordForm.account_id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem v-else label="分类">
          <ElSelect v-model="recordForm.category_id" style="width: 100%">
            <ElOption v-for="category in availableRecordCategories" :key="category.id" :label="category.name" :value="category.id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="商户">
          <ElInput v-model="recordForm.merchant" placeholder="可选，如超市、咖啡店" maxlength="120" />
        </ElFormItem>
        <ElFormItem label="备注">
          <ElInput v-model="recordForm.note" type="textarea" :rows="3" placeholder="可选备注" />
        </ElFormItem>
        <ElFormItem label="记账时间">
          <ElDatePicker v-model="recordForm.occurred_at" type="datetime" style="width: 100%" placeholder="选择时间" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="showRecordDialog = false">取消</ElButton>
        <ElButton type="primary" :loading="recordSaving" @click="saveRecord">
          {{ editingRecordId ? '保存' : '创建' }}
        </ElButton>
      </template>
    </BaseDialog>

    <BaseDialog
      v-model="showAccountDialog"
      :title="editingAccountId ? '编辑账户' : '新增账户'"
      width="460px"
      @opened="focusAccountNameInput"
    >
      <ElForm label-position="top" @submit.prevent="saveAccount">
        <ElFormItem label="账户名称">
          <ElInput ref="accountNameInputRef" v-model="accountForm.name" maxlength="60" />
        </ElFormItem>
        <ElFormItem label="账户类型">
          <ElSelect v-model="accountForm.type" style="width: 100%">
            <ElOption v-for="option in accountTypeOptions" :key="option.value" :label="option.label" :value="option.value" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="期初余额">
          <ElInputNumber v-model="accountForm.initial_balance_yuan" :step="0.01" :precision="2" style="width: 100%" />
        </ElFormItem>
        <ElFormItem label="备注">
          <ElInput v-model="accountForm.note" type="textarea" :rows="3" maxlength="300" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="showAccountDialog = false">取消</ElButton>
        <ElButton type="primary" :loading="accountSaving" @click="saveAccount">
          {{ editingAccountId ? '保存' : '创建' }}
        </ElButton>
      </template>
    </BaseDialog>

    <BaseDialog
      v-model="showCategoryDialog"
      :title="editingCategoryId ? '编辑分类' : '新增分类'"
      width="460px"
      @opened="focusCategoryNameInput"
    >
      <ElForm label-position="top" @submit.prevent="saveCategory">
        <ElFormItem label="分类类型">
          <SegmentedSwitch
            v-model="categoryForm.type"
            aria-label="分类类型"
            :options="categoryTypeOptions"
            full-width
          />
        </ElFormItem>
        <ElFormItem label="分类名称">
          <ElInput ref="categoryNameInputRef" v-model="categoryForm.name" maxlength="40" />
        </ElFormItem>
        <ElFormItem label="颜色">
          <ElInput v-model="categoryForm.color" maxlength="32" placeholder="#94a3b8 / rgb(148, 163, 184) / hsl(215, 20%, 65%)">
            <template #append>
              <span class="category-preview-inline">
                <span class="category-color-dot category-color-dot--preview" :style="{ backgroundColor: getPreviewColor(categoryForm.color) }" />
                <span>{{ getPreviewColor(categoryForm.color) }}</span>
              </span>
            </template>
          </ElInput>
        </ElFormItem>
        <ElFormItem label="图标标识">
          <ElInput v-model="categoryForm.icon" maxlength="40" placeholder="folder">
            <template #append>
              <span class="category-preview-inline">{{ getPreviewIcon(categoryForm.icon) }}</span>
            </template>
          </ElInput>
        </ElFormItem>
        <ElFormItem label="排序">
          <ElInputNumber v-model="categoryForm.sort_order" :min="-999" :max="999" style="width: 100%" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="showCategoryDialog = false">取消</ElButton>
        <ElButton type="primary" :loading="categorySaving" @click="saveCategory">
          {{ editingCategoryId ? '保存' : '创建' }}
        </ElButton>
      </template>
    </BaseDialog>

    <BaseDialog
      v-model="showTemplateDialog"
      :title="editingTemplateId ? '编辑固定账单' : '新增固定账单'"
      width="560px"
      @opened="focusTemplateAmountInput"
    >
      <ElForm label-position="top" @submit.prevent="saveTemplate">
        <ElFormItem label="模板标题">
          <ElInput v-model="templateForm.title" maxlength="80" placeholder="例如：房租、工资、信用卡还款" />
        </ElFormItem>
        <ElFormItem label="类型">
          <SegmentedSwitch
            v-model="templateForm.type"
            aria-label="固定账单类型"
            :options="recordTypeOptions"
            full-width
          />
        </ElFormItem>
        <ElFormItem label="金额">
          <ElInputNumber
            ref="templateAmountInputRef"
            v-model="templateForm.amount_yuan"
            :step="0.01"
            :precision="2"
            style="width: 100%"
          />
        </ElFormItem>
        <ElFormItem label="账户">
          <ElSelect v-model="templateForm.account_id" style="width: 100%">
            <ElOption v-for="account in accounts" :key="account.id" :label="account.name" :value="account.id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem v-if="templateForm.type === 'transfer'" label="转入账户">
          <ElSelect v-model="templateForm.target_account_id" style="width: 100%">
            <ElOption
              v-for="account in accounts"
              :key="account.id"
              :label="account.name"
              :value="account.id"
              :disabled="account.id === templateForm.account_id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem v-else label="分类">
          <ElSelect v-model="templateForm.category_id" style="width: 100%">
            <ElOption v-for="category in availableTemplateCategories" :key="category.id" :label="category.name" :value="category.id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="每月出账日">
          <ElInputNumber v-model="templateForm.day_of_month" :min="1" :max="31" style="width: 100%" />
        </ElFormItem>
        <ElFormItem label="商户">
          <ElInput v-model="templateForm.merchant" maxlength="120" placeholder="可选，如房东、公司、平台名" />
        </ElFormItem>
        <ElFormItem label="备注">
          <ElInput v-model="templateForm.note" type="textarea" :rows="3" placeholder="可选备注" />
        </ElFormItem>
        <ElFormItem label="启用状态">
          <ElSwitch v-model="templateForm.is_active" active-text="启用" inactive-text="停用" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="showTemplateDialog = false">取消</ElButton>
        <ElButton type="primary" :loading="templateSaving" @click="saveTemplate">
          {{ editingTemplateId ? '保存' : '创建' }}
        </ElButton>
      </template>
    </BaseDialog>
  </div>
</template>

<style scoped>
.bills-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.page-subtitle {
  margin: 10px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.7;
}

.page-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.month-toolbar {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.summary-grid {
  row-gap: 16px;
  margin-bottom: 16px;
}

.summary-card {
  height: 100%;
}

.summary-card__title {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.summary-card__value {
  margin-top: 12px;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
}

.summary-card__desc {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.content-grid {
  margin-bottom: 16px;
}

.panel-card {
  margin-bottom: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.filter-item {
  width: 160px;
}

.filter-keyword {
  width: 220px;
}

.records-table {
  width: 100%;
}

.table-actions {
  display: flex;
  gap: 4px;
}

.record-type-cell {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.amount-text {
  font-weight: 600;
}

.amount-text.is-expense {
  color: #ef4444;
}

.amount-text.is-income {
  color: #16a34a;
}

.amount-text.is-transfer {
  color: #d97706;
}

.sub-text {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.stack-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stack-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--el-fill-color-lighter);
}

.stack-item__main {
  flex: 1;
  min-width: 0;
}

.stack-item__title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
  font-weight: 600;
}

.stack-item__value {
  font-size: 18px;
  font-weight: 700;
}

.stack-item__actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.category-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.category-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-block__title {
  font-weight: 600;
}

.category-total-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-total-item__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.category-total-item__name,
.category-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.category-color-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex-shrink: 0;
}

.category-color-dot--preview {
  width: 12px;
  height: 12px;
  border: 1px solid var(--el-border-color);
}

.category-preview-inline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--el-text-color-regular);
}

@media (max-width: 768px) {
  .summary-grid {
    row-gap: 12px;
  }

  .page-header {
    flex-direction: column;
  }

  .page-actions {
    justify-content: flex-start;
  }

  .month-toolbar {
    width: 100%;
  }

  .month-toolbar :deep(.el-date-editor) {
    flex: 1;
  }

  .filter-item,
  .filter-keyword {
    width: 100%;
  }

  .stack-item {
    flex-direction: column;
  }

  .stack-item__actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
