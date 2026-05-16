<script setup lang="ts">
import { ElButton, ElInput } from 'element-plus'

defineProps<{
  creatingTodo: boolean
  draft: string
  visible: boolean
}>()

defineEmits<{
  clear: []
  submit: []
  'update:draft': [value: string]
}>()
</script>

<template>
  <section v-show="visible" class="widget-panel widget-no-drag">
    <div class="panel-header panel-header--static">
      <div class="panel-header__left">
        <h3 class="panel-header__title">添加新待办</h3>
      </div>
    </div>

    <div class="panel-body">
      <div class="composer">
        <p class="composer__label">请输入待办内容</p>
        <ElInput
          :model-value="draft"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 5 }"
          resize="none"
          placeholder="例如：整理本周账单、补充一篇文章草稿"
          @update:model-value="(value) => $emit('update:draft', value)"
        />
        <div class="composer__actions">
          <ElButton plain @click="$emit('clear')">清空</ElButton>
          <ElButton type="primary" :loading="creatingTodo" @click="$emit('submit')">确认添加</ElButton>
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
</style>
