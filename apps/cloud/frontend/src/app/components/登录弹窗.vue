<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Close, Hide, Lock, Right, User, View } from '@element-plus/icons-vue'
import { 使用认证入口 } from '@personal-system/module-auth/使用认证入口'
import { 开发者登录操作 } from '../../modules/认证/dev-login'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ 'update:show': [value: boolean] }>()

const passwordVisible = ref(false)
const {
  errorMessage,
  isDevMode,
  loading,
  loginForm,
  clearError,
  handleDeveloperLogin,
  handleLogin,
} = 使用认证入口({
  messages: {
    loginFailed: '登录失败，请检查用户名和密码',
    developerLoginFailed: '开发者登录失败',
  },
  redirectHandler: {
    getRedirectPath: () => '',
    navigate: async () => {
      console.info('[登录弹窗] 登录成功，关闭登录弹窗')
      emit('update:show', false)
    },
  },
})

function 关闭弹窗() {
  emit('update:show', false)
}

function 处理键盘事件(event: globalThis.KeyboardEvent) {
  if (props.show && event.key === 'Escape') {
    关闭弹窗()
  }
}

function 提交登录() {
  clearError()
  void handleLogin()
}

function 提交开发者登录() {
  clearError()
  void handleDeveloperLogin()
}

watch(() => props.show, (visible) => {
  if (visible) {
    clearError()
    passwordVisible.value = false
  }
})

onMounted(() => window.addEventListener('keydown', 处理键盘事件))
onBeforeUnmount(() => window.removeEventListener('keydown', 处理键盘事件))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="login-modal"
      @click.self="关闭弹窗"
    >
      <section
        class="login-modal__card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="login-modal-title"
        aria-describedby="login-modal-subtitle"
        @click.stop
      >
        <aside class="login-modal__rail" aria-hidden="true">
          <span class="login-modal__rail-brand">PS<span>.</span></span>
          <span class="login-modal__rail-copy">一个属于你的<br />私人空间。</span>
          <span class="login-modal__rail-foot">PERSONAL SYSTEM<br />EST. 2026</span>
        </aside>

        <div class="login-modal__body">
          <div class="login-modal__topline">
            <span class="login-modal__brand" aria-hidden="true">PS<span>.</span></span>
            <button class="login-modal__close" type="button" aria-label="关闭登录弹窗" @click="关闭弹窗">
              <Close aria-hidden="true" />
            </button>
          </div>

          <header class="login-modal__welcome">
            <span class="login-modal__eyebrow">PERSONAL SYSTEM</span>
            <h2 id="login-modal-title">回到这里</h2>
            <p id="login-modal-subtitle">继续你的日常记录。</p>
          </header>

          <form class="login-modal__form" @submit.prevent="提交登录">
            <label for="login-modal-username">用户名</label>
            <div class="login-modal__field">
              <User class="login-modal__field-icon" aria-hidden="true" />
              <input
                id="login-modal-username"
                v-model="loginForm.username"
                type="text"
                autocomplete="username"
                placeholder="请输入用户名"
                required
                :disabled="loading"
                @input="clearError"
              />
            </div>

            <label for="login-modal-password">密码</label>
            <div class="login-modal__field">
              <Lock class="login-modal__field-icon" aria-hidden="true" />
              <input
                id="login-modal-password"
                v-model="loginForm.password"
                :type="passwordVisible ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="请输入密码"
                required
                :disabled="loading"
                @input="clearError"
              />
              <button
                class="login-modal__visibility"
                type="button"
                :aria-label="passwordVisible ? '隐藏密码' : '显示密码'"
                :aria-pressed="passwordVisible"
                @click="passwordVisible = !passwordVisible"
              >
                <Hide v-if="passwordVisible" aria-hidden="true" />
                <View v-else aria-hidden="true" />
              </button>
            </div>

            <p v-if="errorMessage" class="login-modal__error" role="alert">{{ errorMessage }}</p>

            <button class="login-modal__submit" type="submit" :disabled="loading">
              <span>{{ loading ? '正在登录…' : '登录' }}</span>
              <span v-if="loading" class="login-modal__spinner" aria-hidden="true"></span>
              <Right v-else aria-hidden="true" />
            </button>
          </form>

          <footer v-if="isDevMode" class="login-modal__footer">
            <span>开发环境</span>
            <button type="button" :disabled="loading" @click="提交开发者登录">
              {{ 开发者登录操作[0]?.label ?? '开发者快捷登录' }}
              <Right aria-hidden="true" />
            </button>
          </footer>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.login-modal,
.login-modal * {
  box-sizing: border-box;
}

.login-modal {
  --login-accent-deep: var(--el-color-primary-dark-2);
  --login-button: var(--login-accent-deep);
  --login-accent-soft: color-mix(in srgb, #fffefa 72%, var(--el-color-primary-light-7) 28%);
  --login-accent-wash: color-mix(in srgb, #fffefa 65%, var(--el-color-primary-light-8) 35%);
  --login-accent-border: color-mix(in srgb, var(--el-color-primary) 24%, #fffefa);
  --login-surface: #fffefa;
  --login-ink: #27332e;
  --login-muted: #87928a;
  --login-label: #59665e;
  --login-icon: #89978e;
  --login-placeholder: #9aa79e;
  --login-divider: #e6eae6;
  --login-error: #b44235;
  --login-shadow: color-mix(in srgb, var(--el-color-primary-dark-8) 18%, transparent);
  position: fixed;
  z-index: 3000;
  inset: 0;
  display: grid;
  place-items: center;
  overflow: auto;
  padding: 24px;
  color: var(--login-ink);
  background: var(--theme-overlay);
  font-family: Inter, "Noto Sans SC", "Microsoft YaHei", sans-serif;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  backdrop-filter: blur(5px);
}

.login-modal__card {
  display: flex;
  width: min(100%, 520px);
  min-height: 385px;
  overflow: hidden;
  border: 1px solid var(--login-accent-border);
  border-radius: 14px;
  background: var(--login-surface);
  box-shadow: 0 18px 38px var(--login-shadow);
  animation: login-modal-enter 180ms ease-out both;
}

.login-modal__rail {
  display: flex;
  flex: 0 0 38%;
  flex-direction: column;
  justify-content: space-between;
  padding: 25px 20px;
  color: var(--login-accent-deep);
  background: var(--login-accent-soft);
}

.login-modal__rail-brand {
  font-size: 27px;
  font-weight: 850;
  line-height: 1;
}

.login-modal__rail-brand span {
  color: var(--el-color-primary);
}

.login-modal__rail-copy {
  font-size: 22px;
  font-weight: 750;
  line-height: 1.35;
}

.login-modal__rail-foot {
  color: color-mix(in srgb, var(--login-accent-deep) 72%, var(--login-accent-soft));
  font-size: 9px;
  line-height: 1.5;
}

.login-modal__body {
  flex: 1;
  min-width: 0;
  padding: 22px 22px 21px;
}

.login-modal__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 26px;
}

.login-modal__brand {
  visibility: hidden;
  font-size: 18px;
  font-weight: 850;
  line-height: 1;
}

.login-modal__brand span {
  color: var(--el-color-primary);
}

.login-modal__close,
.login-modal__visibility {
  display: grid;
  flex: none;
  place-items: center;
  padding: 0;
  border: 0;
  color: var(--login-icon);
  background: transparent;
  cursor: pointer;
}

.login-modal__close {
  width: 30px;
  height: 30px;
  margin: -2px -5px 0 0;
}

.login-modal__close svg {
  width: 17px;
  height: 17px;
}

.login-modal__welcome {
  margin: 15px 0 17px;
}

.login-modal__eyebrow {
  color: var(--login-accent-deep);
  font-size: 10px;
  font-weight: 800;
}

.login-modal__welcome h2 {
  margin: 7px 0 4px;
  color: var(--login-ink);
  font-size: 24px;
  font-weight: 750;
  line-height: 1.24;
}

.login-modal__welcome p {
  margin: 0;
  color: var(--login-muted);
  font-size: 12px;
  line-height: 1.5;
}

.login-modal__form {
  display: grid;
  gap: 7px;
  margin: 0;
}

.login-modal__form label {
  margin-top: 5px;
  color: var(--login-label);
  font-size: 12px;
  font-weight: 700;
}

.login-modal__field {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 39px;
  padding: 0 12px;
  border: 0;
  border-radius: 7px;
  background: var(--login-accent-wash);
  transition: box-shadow 160ms ease;
}

.login-modal__field:focus-within {
  box-shadow: 0 0 0 2px var(--el-color-primary);
}

.login-modal__field-icon {
  flex: none;
  width: 15px;
  height: 15px;
  color: var(--login-icon);
}

.login-modal__field input {
  min-width: 0;
  width: 100%;
  height: 100%;
  padding: 0;
  border: 0;
  outline: 0;
  color: var(--login-ink);
  background: transparent;
  font: inherit;
  font-size: 13px;
}

.login-modal__field input::placeholder {
  color: var(--login-placeholder);
}

.login-modal__field input:disabled {
  opacity: 0.7;
}

.login-modal__visibility {
  width: 28px;
  height: 30px;
}

.login-modal__visibility svg {
  width: 16px;
  height: 16px;
}

.login-modal__error {
  margin: 3px 0 0;
  color: var(--login-error);
  font-size: 12px;
  line-height: 1.45;
}

.login-modal__submit {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 41px;
  margin: 7px 0 0;
  padding: 0 16px;
  border: 0;
  border-radius: 7px;
  color: #fff;
  background: var(--login-button);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 750;
  transition: filter 160ms ease, transform 160ms ease;
}

.login-modal__submit:hover:not(:disabled) {
  filter: brightness(1.08);
  transform: translateY(-1px);
}

.login-modal__submit:disabled,
.login-modal__footer button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.login-modal__submit svg {
  width: 17px;
  height: 17px;
}

.login-modal__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgb(255 255 255 / 42%);
  border-top-color: #fffefa;
  border-radius: 50%;
  animation: login-modal-spin 700ms linear infinite;
}

.login-modal__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 15px;
  padding-top: 13px;
  border-top: 1px solid var(--login-divider);
  color: var(--login-muted);
  font-size: 11px;
}

.login-modal__footer button {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 0;
  border: 0;
  color: var(--login-accent-deep);
  background: transparent;
  cursor: pointer;
  font: inherit;
  font-weight: 700;
}

.login-modal__footer button:hover:not(:disabled) {
  text-decoration: underline;
}

.login-modal__footer svg {
  width: 12px;
  height: 12px;
}

.login-modal button:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 3px;
}

.dark .login-modal {
  --login-accent-deep: var(--el-color-primary-light-5);
  --login-button: var(--el-color-primary-dark-2);
  --login-accent-soft: color-mix(in srgb, #1d2824 72%, var(--el-color-primary-dark-8) 28%);
  --login-accent-wash: color-mix(in srgb, #151c19 82%, var(--el-color-primary-dark-8) 18%);
  --login-accent-border: color-mix(in srgb, #101613 76%, var(--el-color-primary-dark-8) 24%);
  --login-surface: color-mix(in srgb, #202825 88%, var(--el-color-primary-dark-8) 12%);
  --login-ink: var(--text-primary);
  --login-muted: var(--text-secondary);
  --login-label: var(--text-primary);
  --login-icon: var(--text-tertiary);
  --login-placeholder: var(--text-tertiary);
  --login-divider: color-mix(in srgb, var(--text-primary) 16%, transparent);
  --login-error: var(--theme-danger-strong);
  --login-shadow: rgb(0 0 0 / 42%);
}

@keyframes login-modal-enter {
  from { opacity: 0; transform: translateY(8px) scale(0.99); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes login-modal-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 560px) {
  .login-modal {
    padding: 16px;
  }

  .login-modal__rail {
    flex-basis: 31%;
    padding: 19px 11px;
  }

  .login-modal__rail-copy {
    font-size: 16px;
  }

  .login-modal__body {
    padding: 20px 14px;
  }

  .login-modal__welcome h2 {
    font-size: 20px;
  }

  .login-modal__welcome p {
    font-size: 11px;
  }
}

@media (max-width: 380px) {
  .login-modal__card {
    min-height: 0;
  }

  .login-modal__rail {
    display: none;
  }

  .login-modal__body {
    padding: 21px;
  }

  .login-modal__brand {
    visibility: visible;
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-modal__card,
  .login-modal__spinner {
    animation-duration: 0.01ms;
    animation-iteration-count: 1;
  }
}
</style>
