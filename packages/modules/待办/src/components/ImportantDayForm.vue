<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import {
  ElButton,
  ElDatePicker,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElSelect,
} from 'element-plus'
import type { Todo } from '../store'
import { recurrenceOptions } from '../helpers/todo-item'
import { BaseDialog, SegmentedSwitch } from '@personal-system/ui'

interface Props {
  modelValue: boolean
  editingTodo?: Todo | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submit: [data: {
    title: string
    description?: string
    dateType: 'start' | 'end'
    date: Date | null
    recurrenceType: string
    recurrenceInterval: number
  }]
}>()

type InputInstance = InstanceType<typeof ElInput>

// 表单数据
const form = ref({
  title: '',
  description: '',
  dateType: 'start' as 'start' | 'end', // start: 正计时, end: 倒计时
  date: null as Date | null,
  recurrenceType: 'yearly',
  recurrenceInterval: 1, // 自定义间隔天数
})
const titleInputRef = ref<InputInstance | null>(null)

const 日期类型选项 = [
  { label: '正计时（纪念过去）', value: 'start' },
  { label: '倒计时（期待未来）', value: 'end' },
] as const

// 是否编辑模式
const isEdit = computed(() => !!props.editingTodo)

// 对话框标题
const dialogTitle = computed(() => isEdit.value ? '编辑重要日' : '新建重要日')

// 重置表单
function resetForm() {
  form.value = {
    title: '',
    description: '',
    dateType: 'start',
    date: null,
    recurrenceType: 'yearly',
    recurrenceInterval: 1,
  }
}

function focusTitleInput() {
  void nextTick(() => {
    titleInputRef.value?.focus()
    titleInputRef.value?.input?.focus()
  })
}

// 监听编辑对象变化
watch(() => props.editingTodo, (todo) => {
  if (todo) {
    // 编辑模式：根据 start_date 和 end_date 判断类型
    if (todo.end_date && !todo.start_date) {
      // 只有截止日期 -> 倒计时
      form.value.dateType = 'end'
      form.value.date = new Date(todo.end_date)
    } else if (todo.start_date) {
      // 有开始日期 -> 正计时（优先）
      form.value.dateType = 'start'
      form.value.date = new Date(todo.start_date)
    } else {
      form.value.dateType = 'start'
      form.value.date = null
    }
    
    form.value.title = todo.title
    form.value.description = todo.description || ''
    form.value.recurrenceType = todo.recurrence_type === 'none' ? 'yearly' : todo.recurrence_type
    form.value.recurrenceInterval = todo.recurrence_interval || 1
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听对话框显示状态
watch(() => props.modelValue, (visible) => {
  if (visible && !props.editingTodo) {
    resetForm()
  }
  if (visible) {
    focusTitleInput()
  }
})

// 提交表单
function handleSubmit() {
  if (!form.value.title.trim()) return
  if (!form.value.date) {
    ElMessage.warning('请选择日期')
    return
  }
  
  emit('submit', {
    title: form.value.title.trim(),
    description: form.value.description || undefined,
    dateType: form.value.dateType,
    date: form.value.date,
    recurrenceType: form.value.recurrenceType,
    recurrenceInterval: form.value.recurrenceInterval,
  })
  
  emit('update:modelValue', false)
}

// 关闭对话框
function handleClose() {
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="dialogTitle"
    width="480px"
    style="max-width: 90vw"
    :close-on-click-modal="false"
    @update:model-value="emit('update:modelValue', $event)"
    @opened="focusTitleInput"
    @closed="resetForm"
  >
    <ElForm label-position="left" label-width="80px" @submit.prevent="handleSubmit">
      <!-- 标题 -->
      <ElFormItem>
        <template #label>
          <span>标题<span style="color: var(--el-color-danger); margin-left: 2px">*</span></span>
        </template>
        <ElInput
          ref="titleInputRef"
          v-model="form.title"
          placeholder="例如：结婚纪念日、家人生日"
        />
      </ElFormItem>
      
      <!-- 类型选择 -->
      <ElFormItem label="类型">
        <SegmentedSwitch
          v-model="form.dateType"
          aria-label="重要日类型"
          :options="日期类型选项"
          full-width
        />
      </ElFormItem>

      <!-- 日期 -->
      <ElFormItem>
        <template #label>
          <span>{{ form.dateType === 'start' ? '开始日期' : '目标日期' }}<span style="color: var(--el-color-danger); margin-left: 2px">*</span></span>
        </template>
        <ElDatePicker
          v-model="form.date"
          type="date"
          :placeholder="form.dateType === 'start' ? '选择开始日期' : '选择目标日期'"
          style="width: 100%"
        />
      </ElFormItem>

      <!-- 循环 -->
      <ElFormItem label="循环">
        <div style="display: flex; gap: 12px; align-items: center; width: 100%">
          <ElSelect
            v-model="form.recurrenceType"
            :style="{ flex: form.recurrenceType === 'custom' ? '0 0 140px' : '1' }"
          >
            <ElOption
              v-for="item in recurrenceOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </ElSelect>
          <div
            v-if="form.recurrenceType === 'custom'"
            style="display: flex; align-items: center; gap: 8px; flex-shrink: 0"
          >
            <span class="recurrence-text">每</span>
            <ElInputNumber
              v-model="form.recurrenceInterval"
              :min="1"
              :max="365"
              style="width: 130px"
            />
            <span class="recurrence-text">天</span>
          </div>
        </div>
      </ElFormItem>

      <!-- 备注 -->
      <ElFormItem label="备注">
        <ElInput
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="可选，添加一些备注信息"
        />
      </ElFormItem>

      <!-- 提交按钮 -->
      <div style="display: flex; gap: 12px; margin-top: 24px">
        <ElButton type="primary" style="flex: 1" native-type="submit">
          {{ isEdit ? '保存' : '创建' }}
        </ElButton>
        <ElButton style="flex: 1" @click="handleClose">取消</ElButton>
      </div>
    </ElForm>
  </BaseDialog>
</template>

<style scoped>
/* 循环文字样式 */
.recurrence-text {
  font-size: 14px;
}

.dark .recurrence-text {
  color: #fff;
}
</style>
