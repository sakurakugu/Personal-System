<script setup lang="ts">
/* global HTMLImageElement, CanvasRenderingContext2D, HTMLCanvasElement, Image, requestAnimationFrame, cancelAnimationFrame */
import { onMounted, onUnmounted, watch } from 'vue'
import { useBlogAppearanceStore } from '../../modules/blog/store'

interface SakuraConfig {
  enable: boolean
  sakuraNum: number
  limitTimes: number
  size: { min: number; max: number }
  opacity: { min: number; max: number }
  speed: {
    horizontal: { min: number; max: number }
    vertical: { min: number; max: number }
    rotation: number
    fadeSpeed: number
  }
  zIndex: number
}

const props = withDefaults(defineProps<{
  enable?: boolean
  sakuraNum?: number
  limitTimes?: number
  sizeMin?: number
  sizeMax?: number
  opacityMin?: number
  opacityMax?: number
  speedHorizontalMin?: number
  speedHorizontalMax?: number
  speedVerticalMin?: number
  speedVerticalMax?: number
  rotationSpeed?: number
  fadeSpeed?: number
  zIndex?: number
}>(), {
  enable: true,
  sakuraNum: 21,
  limitTimes: -1,
  sizeMin: 0.5,
  sizeMax: 1.1,
  opacityMin: 0.3,
  opacityMax: 0.9,
  speedHorizontalMin: -1.7,
  speedHorizontalMax: -1.2,
  speedVerticalMin: 1.5,
  speedVerticalMax: 2.2,
  rotationSpeed: 0.03,
  fadeSpeed: 0.03,
  zIndex: 100,
})

const blogAppearance = useBlogAppearanceStore()

const config: SakuraConfig = {
  enable: props.enable,
  sakuraNum: props.sakuraNum,
  limitTimes: props.limitTimes,
  size: { min: props.sizeMin, max: props.sizeMax },
  opacity: { min: props.opacityMin, max: props.opacityMax },
  speed: {
    horizontal: { min: props.speedHorizontalMin, max: props.speedHorizontalMax },
    vertical: { min: props.speedVerticalMin, max: props.speedVerticalMax },
    rotation: props.rotationSpeed,
    fadeSpeed: props.fadeSpeed,
  },
  zIndex: props.zIndex,
}

let manager: SakuraManager | null = null

function isDesktop(): boolean {
  return !window.matchMedia('(pointer: coarse)').matches
}

function maybeInit() {
  if (!manager && blogAppearance.sakuraEnabled && isDesktop()) {
    manager = new SakuraManager(config)
    manager.init().catch((err) => {
      console.error('SakuraEffect init failed:', err)
    })
  }
}

function maybeStop() {
  if (manager) {
    manager.stop()
    manager = null
  }
}

class Sakura {
  x: number
  y: number
  s: number
  r: number
  a: number
  fn: {
    x: (x: number, y: number) => number
    y: (_x: number, y: number) => number
    r: (r: number) => number
    a: (a: number) => number
  }
  idx: number
  img: HTMLImageElement
  limitArray: number[]
  config: SakuraConfig

  constructor(
    x: number,
    y: number,
    s: number,
    r: number,
    a: number,
    fn: Sakura['fn'],
    idx: number,
    img: HTMLImageElement,
    limitArray: number[],
    config: SakuraConfig,
  ) {
    this.x = x
    this.y = y
    this.s = s
    this.r = r
    this.a = a
    this.fn = fn
    this.idx = idx
    this.img = img
    this.limitArray = limitArray
    this.config = config
  }

  draw(cxt: CanvasRenderingContext2D) {
    cxt.save()
    cxt.translate(this.x, this.y)
    cxt.rotate(this.r)
    cxt.globalAlpha = this.a
    cxt.drawImage(this.img, 0, 0, 40 * this.s, 40 * this.s)
    cxt.restore()
  }

  update() {
    this.x = this.fn.x(this.x, this.y)
    this.y = this.fn.y(this.x, this.y)
    this.r = this.fn.r(this.r)
    this.a = this.fn.a(this.a)

    if (
      this.x > window.innerWidth
      || this.x < 0
      || this.y > window.innerHeight
      || this.y < 0
      || this.a <= 0
    ) {
      if (this.limitArray[this.idx] === -1) {
        this.resetPosition()
      } else if (this.limitArray[this.idx] > 0) {
        this.resetPosition()
        this.limitArray[this.idx]--
      }
    }
  }

  private resetPosition() {
    this.fn.r = getRandom('fnr', this.config)
    if (Math.random() > 0.4) {
      this.x = getRandom('x', this.config)
      this.y = 0
      this.s = getRandom('s', this.config)
      this.r = getRandom('r', this.config)
      this.a = getRandom('a', this.config)
    } else {
      this.x = window.innerWidth
      this.y = getRandom('y', this.config)
      this.s = getRandom('s', this.config)
      this.r = getRandom('r', this.config)
      this.a = getRandom('a', this.config)
    }
  }
}

class SakuraList {
  list: Sakura[] = []

  push(sakura: Sakura) {
    this.list.push(sakura)
  }

  update() {
    for (let i = 0, len = this.list.length; i < len; i++) {
      this.list[i].update()
    }
  }

  draw(cxt: CanvasRenderingContext2D) {
    for (let i = 0, len = this.list.length; i < len; i++) {
      this.list[i].draw(cxt)
    }
  }

  get(i: number) {
    return this.list[i]
  }

  size() {
    return this.list.length
  }
}

/* eslint-disable no-redeclare */
function getRandom(
  option: 'x' | 'y' | 's' | 'r' | 'a',
  config: SakuraConfig,
): number
function getRandom(
  option: 'fnx' | 'fny' | 'fnr' | 'fna',
  config: SakuraConfig,
): (...args: number[]) => number
function getRandom(
  option: string,
  config: SakuraConfig,
): number | ((...args: number[]) => number) {
/* eslint-enable no-redeclare */
  let ret: number | ((...args: number[]) => number) = 0
  let random: number

  switch (option) {
    case 'x':
      ret = Math.random() * window.innerWidth
      break
    case 'y':
      ret = Math.random() * window.innerHeight
      break
    case 's':
      ret = config.size.min + Math.random() * (config.size.max - config.size.min)
      break
    case 'r':
      ret = Math.random() * 6
      break
    case 'a':
      ret = config.opacity.min + Math.random() * (config.opacity.max - config.opacity.min)
      break
    case 'fnx':
      random = config.speed.horizontal.min + Math.random() * (config.speed.horizontal.max - config.speed.horizontal.min)
      ret = (x: number, _y: number) => x + random
      break
    case 'fny':
      random = config.speed.vertical.min + Math.random() * (config.speed.vertical.max - config.speed.vertical.min)
      ret = (_x: number, y: number) => y + random
      break
    case 'fnr':
      ret = (r: number) => r + config.speed.rotation
      break
    case 'fna':
      ret = (alpha: number) => alpha - config.speed.fadeSpeed * 0.01
      break
  }
  return ret
}

class SakuraManager {
  private config: SakuraConfig
  private canvas: HTMLCanvasElement | null = null
  private ctx: CanvasRenderingContext2D | null = null
  private sakuraList: SakuraList | null = null
  private animationId: number | null = null
  private img: HTMLImageElement | null = null
  private isRunning = false
  private boundHandleResize: () => void

  constructor(config: SakuraConfig) {
    this.config = config
    this.boundHandleResize = this.handleResize.bind(this)
  }

  async init() {
    if (!this.config.enable || this.isRunning) return

    this.img = new Image()
    this.img.src = '/sakura.png'

    await new Promise<void>((resolve, reject) => {
      if (!this.img) return
      this.img.onload = () => resolve()
      this.img.onerror = () => reject(new Error('Failed to load sakura image'))
    })

    this.createCanvas()
    this.createSakuraList()
    this.startAnimation()
    this.isRunning = true
  }

  private createCanvas() {
    this.canvas = document.createElement('canvas')
    this.canvas.height = window.innerHeight
    this.canvas.width = window.innerWidth
    this.canvas.setAttribute(
      'style',
      `position: fixed; left: 0; top: 0; pointer-events: none; z-index: ${this.config.zIndex}; transform: translateZ(0);`,
    )
    this.canvas.setAttribute('id', 'canvas_sakura')
    document.body.appendChild(this.canvas)
    this.ctx = this.canvas.getContext('2d')
    window.addEventListener('resize', this.boundHandleResize)
  }

  private createSakuraList() {
    if (!this.img || !this.ctx) return

    this.sakuraList = new SakuraList()
    const limitArray = new Array(this.config.sakuraNum).fill(this.config.limitTimes)

    for (let i = 0; i < this.config.sakuraNum; i++) {
      const sakura = new Sakura(
        getRandom('x', this.config),
        getRandom('y', this.config),
        getRandom('s', this.config),
        getRandom('r', this.config),
        getRandom('a', this.config),
        {
          x: getRandom('fnx', this.config),
          y: getRandom('fny', this.config),
          r: getRandom('fnr', this.config),
          a: getRandom('fna', this.config),
        },
        i,
        this.img,
        limitArray,
        this.config,
      )
      sakura.draw(this.ctx)
      this.sakuraList.push(sakura)
    }
  }

  private startAnimation() {
    if (!this.ctx || !this.canvas || !this.sakuraList) return

    const animate = () => {
      if (!this.ctx || !this.canvas || !this.sakuraList) return
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
      this.sakuraList.update()
      this.sakuraList.draw(this.ctx)
      this.animationId = requestAnimationFrame(animate)
    }

    this.animationId = requestAnimationFrame(animate)
  }

  private handleResize() {
    if (this.canvas) {
      this.canvas.width = window.innerWidth
      this.canvas.height = window.innerHeight
    }
  }

  stop() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
      this.animationId = null
    }
    if (this.canvas) {
      document.body.removeChild(this.canvas)
      this.canvas = null
    }
    window.removeEventListener('resize', this.boundHandleResize)
    this.isRunning = false
  }

  toggle() {
    if (this.isRunning) {
      this.stop()
    } else {
      this.init()
    }
  }
}

onMounted(() => {
  if (!props.enable) return
  maybeInit()
})

watch(() => blogAppearance.sakuraEnabled, () => {
  if (blogAppearance.sakuraEnabled && isDesktop()) {
    maybeInit()
  } else {
    maybeStop()
  }
})

onUnmounted(() => {
  maybeStop()
})
</script>

<template>
  <!-- 樱花特效通过 canvas 挂载到 body，组件本身不渲染 DOM -->
  <div v-if="false" aria-hidden="true" />
</template>
