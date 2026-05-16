<script setup lang="ts">
import { DesktopWidgetTokenCard, DeviceSessionsPage } from '@personal-system/module-auth'
import { 获取已配置的活跃基地址 } from '@personal-system/api'
import { 同步小工具令牌到桌面 } from '@/shared/widget-sync'

function syncWidgetToken(payload: { token: string; widgetName: string }) {
  return 同步小工具令牌到桌面({
    token: payload.token,
    apiBaseUrl: 获取已配置的活跃基地址(),
    widgetName: payload.widgetName,
  })
}
</script>

<template>
  <DeviceSessionsPage info-title="桌面端当前使用设备令牌登录，这里列出的就是原生设备会话。">
    <template #before-list>
      <DesktopWidgetTokenCard :sync-token="syncWidgetToken" />
    </template>
  </DeviceSessionsPage>
</template>
