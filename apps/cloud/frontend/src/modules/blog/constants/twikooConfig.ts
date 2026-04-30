export const TWIKOO_SCRIPT_VERSION = '1.7.7'
export const TWIKOO_SCRIPT_URL = `https://cdn.jsdelivr.net/npm/twikoo@${TWIKOO_SCRIPT_VERSION}/dist/twikoo.nocss.js`
export const TWIKOO_STYLE_URL = `https://cdn.jsdelivr.net/npm/twikoo@${TWIKOO_SCRIPT_VERSION}/dist/twikoo.css`

export interface TwikooInitOptions {
  envId: string
  el: HTMLElement | string
  path?: string
  lang?: string
  region?: string
}

export interface TwikooInstance {
  init(options: TwikooInitOptions): Promise<void>
}

export function readTwikooEnvId(): string {
  return import.meta.env.VITE_TWIKOO_ENV_ID?.trim() || ''
}

export function readTwikooRegion(): string | undefined {
  const region = import.meta.env.VITE_TWIKOO_REGION?.trim()
  return region || undefined
}
