export const 最大评分等级 = 15
export const 最大展示星数 = 6
export const 零星起始等级 = 3

export type 评分星位状态 = 'full' | 'half' | 'empty'
export type 评分展示类型 = 'danger' | 'trash' | 'stars'

export interface 评分展示模型 {
  type: 评分展示类型
  icon: string
  label: string
  levelText: string
  summaryText: string
  starValue: number
  starStates: 评分星位状态[]
}

function 限制评分等级(rating: number) {
  return Math.max(1, Math.min(最大评分等级, Math.round(rating)))
}

function 格式化星数(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function 构建星位状态(starValue: number): 评分星位状态[] {
  return Array.from({ length: 最大展示星数 }, (_, index) => {
    const current = index + 1
    if (starValue >= current) {
      return 'full'
    }
    if (starValue >= current - 0.5) {
      return 'half'
    }
    return 'empty'
  })
}

export function 获取评分展示(rating: number): 评分展示模型 {
  const 等级 = 限制评分等级(rating)
  const levelText = `${等级} 级`

  if (等级 === 1) {
    return {
      type: 'danger',
      icon: '💣',
      label: '雷区',
      levelText,
      summaryText: `${levelText} · 💣 雷区`,
      starValue: 0,
      starStates: 构建星位状态(0),
    }
  }

  if (等级 === 2) {
    return {
      type: 'trash',
      icon: '💩',
      label: '粪作',
      levelText,
      summaryText: `${levelText} · 💩 粪作`,
      starValue: 0,
      starStates: 构建星位状态(0),
    }
  }

  const starValue = (等级 - 零星起始等级) / 2
  const label = `${格式化星数(starValue)} 星`

  return {
    type: 'stars',
    icon: starValue > 0 ? '★' : '☆',
    label,
    levelText,
    summaryText: `${levelText} · ${label}`,
    starValue,
    starStates: 构建星位状态(starValue),
  }
}

export function 获取评分选项标签(rating: number) {
  const 展示 = 获取评分展示(rating)
  return `${展示.levelText} · ${展示.icon} ${展示.label}`
}
