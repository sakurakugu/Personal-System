<script setup lang="ts">
import { ElInput } from 'element-plus'
import { nextTick, ref, watch } from 'vue'
import WidgetButton from './小工具按钮.vue'

const props = defineProps<{
  creatingTodo: boolean
  draft: string
  visible: boolean
}>()

defineEmits<{
  clear: []
  submit: []
  'update:draft': [value: string]
}>()

const draftInputRef = ref<InstanceType<typeof ElInput> | null>(null)

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) {
      return
    }
    await nextTick()
    draftInputRef.value?.resizeTextarea()
  },
)
</script>

<template>
  <section class="widget-panel widget-no-drag">
    <div class="panel-header panel-header--static">
      <div class="panel-header__left">
        <h3 class="panel-header__title">添加新待办</h3>
      </div>
    </div>

    <div class="panel-body">
      <div class="composer">
        <p class="composer__label">请输入待办内容</p>
        <ElInput
          ref="draftInputRef"
          class="composer__input"
          :model-value="draft"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 5 }"
          resize="none"
          placeholder="例如：整理本周账单、补充一篇文章草稿"
          @update:model-value="(value) => $emit('update:draft', value)"
        />
        <div class="composer__actions">
          <WidgetButton variant="secondary" @click="$emit('clear')">清空</WidgetButton>
          <WidgetButton variant="primary" :loading="creatingTodo" @click="$emit('submit')">确认添加</WidgetButton>
        </div>
      </div>
    </div>
  </section>
</template>

<style>
.composer {
  display: grid;
  gap: 12px;
}

.composer__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.composer__input :deep(.el-textarea__inner) {
  min-height: 88px !important;
  line-height: 1.6;
}
</style>
