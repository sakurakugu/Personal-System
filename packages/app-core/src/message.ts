import { messageConfig } from 'element-plus'
import type { MessageConfigContext } from 'element-plus'

const 默认消息配置: MessageConfigContext = {
  grouping: true,
  showClose: true,
}

export function 配置全局消息(配置: MessageConfigContext = {}): void {
  Object.assign(messageConfig, 默认消息配置, 配置)
}
