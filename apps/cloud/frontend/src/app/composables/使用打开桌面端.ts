import { ElMessage } from 'element-plus'
import { onBeforeUnmount, ref } from 'vue'
import api from '../../shared/api'
import { 获取API错误消息 } from '../../shared/api'
import { 构建桌面端小工具协议地址 } from '../constants/desktop-protocol'

/** 后端 /auth/device/token 返回结构（仅使用 token，其余字段用于排错）。 */
interface 设备令牌响应 {
  token: string
  expires_at: string
  session: unknown
}

/** 唤起桌面端后的等待时间：超时仍在前台则提示未安装/未启动。 */
const 桌面端唤起等待毫秒 = 1200

/**
 * 打开桌面端小工具。
 *
 * 流程：请求一次性设备令牌 -> 跳转自定义协议唤起桌面端 -> 等待 1.2 秒。
 * 若页面仍在可见且未失焦状态（没有桌面端接管），提示用户安装或启动桌面端。
 */
export function 使用打开桌面端() {
  const 正在打开桌面端 = ref(false)
  let 等待计时器: number | null = null
  let 已失去焦点 = false

  function 处理窗口失焦() {
    已失去焦点 = true
  }

  function 处理页面可见性变化() {
    if (document.visibilityState === 'hidden') {
      已失去焦点 = true
    }
  }

  function 清理等待状态() {
    if (等待计时器 !== null) {
      window.clearTimeout(等待计时器)
      等待计时器 = null
    }
    window.removeEventListener('blur', 处理窗口失焦)
    document.removeEventListener('visibilitychange', 处理页面可见性变化)
  }

  /** 开始 1.2 秒的唤起等待，期间失焦/隐藏都视为桌面端已被打开。 */
  function 开始等待桌面端响应() {
    清理等待状态()
    已失去焦点 = false
    window.addEventListener('blur', 处理窗口失焦)
    document.addEventListener('visibilitychange', 处理页面可见性变化)
    等待计时器 = window.setTimeout(() => {
      清理等待状态()
      if (已失去焦点 || document.visibilityState === 'hidden') {
        return
      }
      ElMessage.warning('未检测到桌面端，请先安装或启动桌面端')
    }, 桌面端唤起等待毫秒)
  }

  async function 打开桌面端() {
    if (正在打开桌面端.value) {
      return
    }
    正在打开桌面端.value = true
    try {
      // 后端接口要求 JSON 请求体（各字段均有默认值），这里显式传空对象
      const { data } = await api.post<设备令牌响应>('/auth/device/token', {})
      if (!data?.token) {
        ElMessage.error('获取桌面端登录令牌失败')
        return
      }
      开始等待桌面端响应()
      const 协议地址 = 构建桌面端小工具协议地址(data.token)
      // 日志隐藏令牌本身，只保留协议地址格式，便于排查唤起失败问题
      console.info('正在唤起桌面端', {
        协议地址: 协议地址.replace(encodeURIComponent(data.token), '***'),
      })
      window.location.href = 协议地址
    } catch (错误) {
      ElMessage.error(获取API错误消息(错误, '获取桌面端登录令牌失败'))
    } finally {
      正在打开桌面端.value = false
    }
  }

  onBeforeUnmount(清理等待状态)

  return {
    正在打开桌面端,
    打开桌面端,
  }
}
