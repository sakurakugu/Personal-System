declare module 'culori' {
  export type OklchColor = {
    mode: 'oklch'
    l: number
    c: number
    h: number
  }

  export type RgbColor = {
    mode: 'rgb'
    r: number
    g: number
    b: number
  }

  export function converter(mode: 'rgb'): (color: OklchColor) => RgbColor | undefined
  export function formatCss(color: OklchColor): string
}
