<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  texts: string[]
  speed?: number
  deleteSpeed?: number
  pauseTime?: number
}>(), {
  speed: 100,
  deleteSpeed: 50,
  pauseTime: 2000,
})

const display = ref('')
let instance: TypewriterEffect | null = null

class TypewriterEffect {
  private texts: string[]
  private currentTextIndex = 0
  private currentIndex = 0
  private isDeleting = false
  private timeoutId: number | null = null
  private speed: number
  private deleteSpeed: number
  private pauseTime: number
  private displayRef: { value: string }

  constructor(texts: string[], displayRef: { value: string }, speed: number, deleteSpeed: number, pauseTime: number) {
    this.texts = texts
    this.displayRef = displayRef
    this.speed = speed
    this.deleteSpeed = deleteSpeed
    this.pauseTime = pauseTime
    this.start()
  }

  private start() {
    if (this.texts.length === 0) return
    this.type()
  }

  private getCurrentText(): string {
    return this.texts[this.currentTextIndex] || ''
  }

  private type() {
    const currentText = this.getCurrentText()
    const segments = this.segmentText(currentText)

    if (this.isDeleting) {
      if (this.currentIndex > 0) {
        this.currentIndex--
        this.displayRef.value = segments.slice(0, this.currentIndex).join('')
        this.timeoutId = window.setTimeout(() => this.type(), this.deleteSpeed)
      } else {
        this.isDeleting = false
        this.currentTextIndex = (this.currentTextIndex + 1) % this.texts.length
        this.timeoutId = window.setTimeout(() => this.type(), this.speed)
      }
    } else {
      if (this.currentIndex < segments.length) {
        this.currentIndex++
        this.displayRef.value = segments.slice(0, this.currentIndex).join('')
        this.timeoutId = window.setTimeout(() => this.type(), this.speed)
      } else {
        if (this.texts.length > 1) {
          this.isDeleting = true
          this.timeoutId = window.setTimeout(() => this.type(), this.pauseTime)
        }
      }
    }
  }

  destroy() {
    if (this.timeoutId !== null) {
      window.clearTimeout(this.timeoutId)
      this.timeoutId = null
    }
  }

  private segmentText(text: string): string[] {
    const segmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' })
    return Array.from(segmenter.segment(text), s => s.segment)
  }
}

function restart() {
  if (instance) {
    instance.destroy()
    instance = null
  }
  display.value = ''
  instance = new TypewriterEffect(props.texts, display, props.speed, props.deleteSpeed, props.pauseTime)
}

onMounted(() => {
  restart()
})

watch(() => props.texts, () => {
  restart()
}, { flush: 'post' })

onUnmounted(() => {
  if (instance) {
    instance.destroy()
    instance = null
  }
})
</script>

<template>
  <span class="typewriter">{{ display }}</span>
  <span class="typewriter-cursor">|</span>
</template>

<style scoped>
.typewriter {
  display: inline;
}

.typewriter-cursor {
  display: inline;
  animation: blink 1s infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}
</style>
