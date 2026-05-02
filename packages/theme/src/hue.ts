export interface OklchColorToken {
  lightness: number
  chroma: number
}

function gammaEncodeSrgbChannel(value: number) {
  const clampedValue = Math.min(Math.max(value, 0), 1)
  if (clampedValue <= 0.0031308) {
    return clampedValue * 12.92
  }
  return 1.055 * (clampedValue ** (1 / 2.4)) - 0.055
}

export function normalizeHue(value: number) {
  return ((Math.round(value) % 360) + 360) % 360
}

export function clampHue(value: number, fallback: number) {
  if (Number.isNaN(value)) {
    return fallback
  }
  return normalizeHue(value)
}

export function parseStoredHue(value: string | null, fallback: number) {
  const parsed = value ? Number.parseInt(value, 10) : Number.NaN
  return clampHue(parsed, fallback)
}

export function createRgbTripletFromOklch(token: OklchColorToken, hueValue: number) {
  const hue = normalizeHue(hueValue)
  const radians = (hue * Math.PI) / 180
  const a = token.chroma * Math.cos(radians)
  const b = token.chroma * Math.sin(radians)

  const lComponent = token.lightness + 0.3963377774 * a + 0.2158037573 * b
  const mComponent = token.lightness - 0.1055613458 * a - 0.0638541728 * b
  const sComponent = token.lightness - 0.0894841775 * a - 1.291485548 * b

  const l = lComponent ** 3
  const m = mComponent ** 3
  const s = sComponent ** 3

  const red = gammaEncodeSrgbChannel(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s)
  const green = gammaEncodeSrgbChannel(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s)
  const blue = gammaEncodeSrgbChannel(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s)

  return [
    Math.round(red * 255),
    Math.round(green * 255),
    Math.round(blue * 255),
  ].join(', ')
}

export function createRgbCssFromOklch(token: OklchColorToken, hueValue: number) {
  return `rgb(${createRgbTripletFromOklch(token, hueValue)})`
}

export function applyThemeHueToRoot(options: {
  hueValue: number
  primaryRgbToken: OklchColorToken
  root?: HTMLElement
}) {
  const root = options.root ?? document.documentElement
  const normalizedHue = normalizeHue(options.hueValue)
  root.style.setProperty('--hue', String(normalizedHue))
  root.style.setProperty('--selection-hue', String(normalizedHue))
  root.style.setProperty(
    '--el-color-primary-rgb',
    createRgbTripletFromOklch(options.primaryRgbToken, normalizedHue),
  )
  return normalizedHue
}
