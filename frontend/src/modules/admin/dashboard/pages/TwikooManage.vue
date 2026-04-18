<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import { ElAlert, ElButton, ElCard, ElIcon, ElInput, ElMessage, ElSpace, ElTag } from 'element-plus'
import TwikooPanel from '../../../blog/components/TwikooPanel.vue'
import { getApiErrorMessage } from '../../../../shared/api'
import { 更新Twikoo管理配置, 读取Twikoo管理配置, 读取Twikoo访问令牌 } from '../../../blog/api/twikooAdmin'

const 暗号读取中 = ref(false)
const 暗号保存中 = ref(false)
const 管理暗号 = ref('')
const 已登录Twikoo管理面板 = ref(false)

const 是否存在访问令牌 = computed(() => 读取Twikoo访问令牌().length > 0)

function 生成随机暗号() {
  const 字符集 = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
  const 缓冲区 = new Uint32Array(10)
  window.crypto.getRandomValues(缓冲区)
  管理暗号.value = Array.from(缓冲区, (value) => 字符集[value % 字符集.length]).join('')
}

async function 读取当前暗号配置() {
  暗号读取中.value = true
  try {
    const config = await 读取Twikoo管理配置()
    管理暗号.value = typeof config.HIDE_ADMIN_CRYPT === 'string' ? config.HIDE_ADMIN_CRYPT : ''
    已登录Twikoo管理面板.value = true
    ElMessage.success('Twikoo 配置已同步')
  } catch (error) {
    已登录Twikoo管理面板.value = false
    ElMessage.error(getApiErrorMessage(error, '请先在下方面板登录 Twikoo 管理员'))
  } finally {
    暗号读取中.value = false
  }
}

async function 保存当前暗号配置() {
  暗号保存中.value = true
  try {
    await 更新Twikoo管理配置({
      HIDE_ADMIN_CRYPT: 管理暗号.value.trim(),
    })
    已登录Twikoo管理面板.value = true
    ElMessage.success(管理暗号.value.trim() ? '隐藏暗号已保存' : '隐藏暗号已清空')
  } catch (error) {
    已登录Twikoo管理面板.value = false
    ElMessage.error(getApiErrorMessage(error, '保存 Twikoo 隐藏暗号失败'))
  } finally {
    暗号保存中.value = false
  }
}

async function 清空暗号配置() {
  管理暗号.value = ''
  await 保存当前暗号配置()
}
</script>

<template>
  <div class="page-container">
    <section class="page-header">
      <div class="page-header-main">
        <div class="page-header-icon">
          <ElIcon><ChatDotRound /></ElIcon>
        </div>
        <div class="page-header-copy">
          <h2>评论管理</h2>
          <p>这里保留评论管理入口，普通前台页面将隐藏管理小齿轮。</p>
        </div>
      </div>
      <ElTag type="warning" effect="dark">仅超级管理员可见</ElTag>
    </section>

    <ElAlert
      type="info"
      :closable="false"
      title="首次使用时，请点击评论卡片右上角的小齿轮设置管理员密码。后续登录仍使用 Twikoo 自己的密码，不复用本站后台账号。"
      class="page-alert"
    />

    <ElCard shadow="never" class="tips-card">
      <div class="tips-title">当前管理方式</div>
      <ul class="tips-list">
        <li>评论数据仍由 Twikoo 独立维护，不进入本站 PostgreSQL。</li>
        <li>这里主要是把管理入口放进后台，避免在前台直接暴露。</li>
        <li>如果想彻底隐藏前台入口，可在 Twikoo 配置里继续设置 `HIDE_ADMIN_CRYPT`。</li>
      </ul>
    </ElCard>

    <ElCard shadow="never" class="tips-card">
      <template #header>
        <div class="config-header">
          <span>前台管理入口暗号</span>
          <ElSpace>
            <ElTag :type="已登录Twikoo管理面板 ? 'success' : 'info'">
              {{ 已登录Twikoo管理面板 ? '已连接 Twikoo 管理配置' : '尚未连接管理配置' }}
            </ElTag>
            <ElTag :type="是否存在访问令牌 ? 'success' : 'warning'" effect="plain">
              {{ 是否存在访问令牌 ? '已检测到登录令牌' : '未检测到登录令牌' }}
            </ElTag>
          </ElSpace>
        </div>
      </template>

      <div class="config-body">
        <p class="config-tip">
          在下方 Twikoo 面板登录管理员密码后，点击“读取当前配置”，即可直接保存或清空 `HIDE_ADMIN_CRYPT`。
        </p>
        <ElInput
          v-model="管理暗号"
          placeholder="例如：admin-door"
          clearable
        />
        <div class="config-actions">
          <ElButton :loading="暗号读取中" @click="读取当前暗号配置">读取当前配置</ElButton>
          <ElButton @click="生成随机暗号">随机生成</ElButton>
          <ElButton type="primary" :loading="暗号保存中" @click="保存当前暗号配置">保存暗号</ElButton>
          <ElButton type="danger" plain :loading="暗号保存中" @click="清空暗号配置">清空暗号</ElButton>
        </div>
      </div>
    </ElCard>

    <TwikooPanel
      path="/dashboard/twikoo"
      title="Twikoo 评论面板"
      empty-description="后台评论面板尚未配置 Twikoo 服务地址"
    />
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 20px;
  border: 1px solid rgb(var(--el-color-primary-rgb) / 0.12);
  background:
    linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.12), rgb(var(--el-color-primary-rgb) / 0.03)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.99));
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.page-header-main {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
}

.page-header-icon {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgb(var(--el-color-primary-rgb) / 0.18), rgb(var(--el-color-primary-rgb) / 0.08));
  color: var(--el-color-primary-dark-2);
  font-size: 24px;
  flex: 0 0 auto;
}

.page-header-copy {
  min-width: 0;
}

.page-header-copy h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.3;
}

.page-header-copy p {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.7;
}

.page-alert {
  margin: 0;
}

.tips-card {
  border-radius: 18px;
  border-color: rgb(var(--el-color-primary-rgb) / 0.1);
  background: rgba(255, 255, 255, 0.92);
}

.tips-card :deep(.el-card__body) {
  padding: 18px 20px;
}

.tips-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 12px;
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.config-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-tip {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.7;
}

.config-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.tips-list {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.dark .page-header,
.dark .tips-card {
  border-color: color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--el-color-primary-light-5) 14%, transparent), color-mix(in srgb, var(--el-color-primary-light-5) 5%, transparent)),
    rgba(18, 25, 22, 0.9);
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.24);
}

.dark .page-header-icon {
  color: var(--el-color-primary-light-5);
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
  }

  .config-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
