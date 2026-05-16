<script setup lang="ts">
import { DesktopWidgetTokenCard, DeviceSessionsPage } from '@personal-system/module-auth'
import { getConfiguredActiveBaseUrl } from '@personal-system/api'
import { syncWidgetTokenToDesktopWidget } from '@/shared/widget-sync'

function syncWidgetToken(payload: { token: string; widgetName: string }) {
  return syncWidgetTokenToDesktopWidget({
    token: payload.token,
    apiBaseUrl: getConfiguredActiveBaseUrl(),
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
