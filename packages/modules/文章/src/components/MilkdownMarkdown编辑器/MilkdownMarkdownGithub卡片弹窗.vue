<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  confirm: [repo: string]
}>()

const repoInputRef = ref<HTMLInputElement | null>(null)
const repoInput = ref('')
const repoError = ref('')

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) {
      return
    }

    repoInput.value = ''
    repoError.value = ''
    await nextTick()
    repoInputRef.value?.focus()
  },
)

function confirm() {
  const repo = repoInput.value.trim()
  if (!repo) {
    repoError.value = '请输入 GitHub 仓库，例如 owner/repo'
    return
  }

  if (!isValidGithubRepoName(repo)) {
    repoError.value = 'GitHub 仓库格式应为 owner/repo，只能包含字母、数字、点、短横线和下划线'
    return
  }

  emit('confirm', repo)
}

function isValidGithubRepoName(repo: string): boolean {
  return /^[A-Za-z0-9][A-Za-z0-9-]{0,38}\/[A-Za-z0-9._-]+$/.test(repo)
}
</script>

<template>
  <div
    v-if="visible"
    class="milkdown-markdown-github-card-dialog"
    role="dialog"
    aria-modal="true"
    aria-label="插入 GitHub 仓库卡片"
    @click.self="emit('close')"
  >
    <form class="milkdown-markdown-github-card-dialog__panel" @submit.prevent="confirm">
      <div class="milkdown-markdown-github-card-dialog__header">
        <strong>插入 GitHub 仓库卡片</strong>
        <button
          class="milkdown-markdown-github-card-dialog__close"
          type="button"
          title="关闭"
          @click="emit('close')"
        >
          关闭
        </button>
      </div>
      <div class="milkdown-markdown-github-card-dialog__body">
        <label class="milkdown-markdown-github-card-dialog__field">
          <span>仓库</span>
          <input
            ref="repoInputRef"
            v-model="repoInput"
            class="milkdown-markdown-github-card-dialog__input"
            type="text"
            placeholder="owner/repo"
            autocomplete="off"
            @input="repoError = ''"
          >
        </label>
        <p
          v-if="repoError"
          class="milkdown-markdown-github-card-dialog__error"
        >
          {{ repoError }}
        </p>
      </div>
      <div class="milkdown-markdown-github-card-dialog__footer">
        <button type="button" @click="emit('close')">取消</button>
        <button type="submit" class="is-primary">插入</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.milkdown-markdown-github-card-dialog {
  position: fixed;
  inset: 0;
  z-index: 4100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
  background: rgba(15, 23, 42, 0.48);
}

.milkdown-markdown-github-card-dialog__panel {
  display: flex;
  flex-direction: column;
  width: min(420px, 100%);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color-overlay);
  color: var(--el-text-color-primary);
  box-shadow: var(--el-box-shadow-dark);
}

.milkdown-markdown-github-card-dialog__header,
.milkdown-markdown-github-card-dialog__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
  border-bottom: 1px solid var(--el-border-color-light);
}

.milkdown-markdown-github-card-dialog__footer {
  justify-content: flex-end;
  border-top: 1px solid var(--el-border-color-light);
  border-bottom: none;
}

.milkdown-markdown-github-card-dialog__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 14px;
  box-sizing: border-box;
}

.milkdown-markdown-github-card-dialog__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.milkdown-markdown-github-card-dialog__input {
  min-height: 34px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  outline: none;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font: inherit;
}

.milkdown-markdown-github-card-dialog__input:focus {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary) 18%, transparent);
}

.milkdown-markdown-github-card-dialog__error {
  margin: 0;
  color: var(--el-color-danger);
  font-size: 12px;
  line-height: 1.5;
}

.milkdown-markdown-github-card-dialog__close,
.milkdown-markdown-github-card-dialog__footer button {
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  cursor: pointer;
}

.milkdown-markdown-github-card-dialog__footer button.is-primary {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary);
  color: #fff;
}
</style>
