import type { MediaStatus, MediaType } from './types'

export interface 文娱状态选项<T extends MediaStatus | '' = MediaStatus> {
  label: string
  value: T
}

const 通用状态标签映射: Record<Extract<MediaStatus, 'paused' | 'dropped'>, string> = {
  paused: '搁置',
  dropped: '弃坑',
}

const 聚合状态标签映射: Record<Exclude<MediaStatus, 'paused' | 'dropped'>, string> = {
  planned: '想看 / 想读 / 想听 / 想玩',
  doing: '在看 / 在读 / 在听 / 在玩',
  done: '看过 / 读过 / 听过 / 玩过',
}

const 分类状态标签映射: Record<MediaType, Record<Exclude<MediaStatus, 'paused' | 'dropped'>, string>> = {
  anime: {
    planned: '想看',
    doing: '在看',
    done: '看过',
  },
  comic: {
    planned: '想看',
    doing: '在看',
    done: '看过',
  },
  movie: {
    planned: '想看',
    doing: '在看',
    done: '看过',
  },
  tv: {
    planned: '想看',
    doing: '在看',
    done: '看过',
  },
  novel: {
    planned: '想读',
    doing: '在读',
    done: '读过',
  },
  book: {
    planned: '想读',
    doing: '在读',
    done: '读过',
  },
  music: {
    planned: '想听',
    doing: '在听',
    done: '听过',
  },
  game: {
    planned: '想玩',
    doing: '在玩',
    done: '玩过',
  },
  other: {
    planned: '计划中',
    doing: '进行中',
    done: '已完成',
  },
}

const 状态顺序: MediaStatus[] = ['planned', 'doing', 'done', 'paused', 'dropped']

export function 获取文娱状态标签(mediaType: MediaType | '' | null | undefined, status: MediaStatus): string {
  if (status === 'paused' || status === 'dropped') {
    return 通用状态标签映射[status]
  }
  if (!mediaType) {
    return 聚合状态标签映射[status]
  }
  return 分类状态标签映射[mediaType][status]
}

export function 获取文娱状态选项(mediaType: MediaType | '' | null | undefined): 文娱状态选项[] {
  return 状态顺序.map((status) => ({
    label: 获取文娱状态标签(mediaType, status),
    value: status,
  }))
}

export function 获取文娱状态筛选选项(mediaType: MediaType | '' | null | undefined): 文娱状态选项<MediaStatus | ''>[] {
  return [
    { label: '全部', value: '' },
    ...获取文娱状态选项(mediaType),
  ]
}
