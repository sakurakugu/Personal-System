<script setup lang="ts">
import {
  ElButton,
  ElCheckbox,
  ElInput,
  ElInputNumber,
  ElText,
} from 'element-plus'
import BaseDialog from '../../../../shared/components/BaseDialog.vue'

defineProps<{
  visible: boolean
  标题: string
  名称前缀: string
  起始序号: number
  补零位数: number
  保留扩展名: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:prefix': [value: string]
  'update:start-index': [value: number]
  'update:digits': [value: number]
  'update:keep-extension': [value: boolean]
  confirm: []
}>()
</script>

<template>
  <BaseDialog
    :model-value="visible"
    :title="标题"
    width="460px"
    @update:model-value="emit('update:visible', $event)"
  >
    <div class="batch-rename-form">
      <div class="batch-rename-form__row">
        <span class="batch-rename-form__label">名称前缀</span>
        <ElInput
          :model-value="名称前缀"
          placeholder="例如：素材-"
          @update:model-value="emit('update:prefix', $event)"
        />
      </div>
      <div class="batch-rename-form__grid">
        <div class="batch-rename-form__row">
          <span class="batch-rename-form__label">起始序号</span>
          <ElInputNumber
            :model-value="起始序号"
            :min="1"
            :step="1"
            @update:model-value="emit('update:start-index', Number($event ?? 1))"
          />
        </div>
        <div class="batch-rename-form__row">
          <span class="batch-rename-form__label">补零位数</span>
          <ElInputNumber
            :model-value="补零位数"
            :min="1"
            :max="8"
            :step="1"
            @update:model-value="emit('update:digits', Number($event ?? 1))"
          />
        </div>
      </div>
      <ElCheckbox
        :model-value="保留扩展名"
        @update:model-value="emit('update:keep-extension', Boolean($event))"
      >
        文件保留原扩展名
      </ElCheckbox>
      <ElText type="info">
        会按当前排序顺序执行，文件夹排在文件前面。
      </ElText>
    </div>

    <template #footer>
      <ElButton @click="emit('update:visible', false)">取消</ElButton>
      <ElButton type="primary" @click="emit('confirm')">确认重命名</ElButton>
    </template>
  </BaseDialog>
</template>

<style scoped>
.batch-rename-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.batch-rename-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.batch-rename-form__row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.batch-rename-form__label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
