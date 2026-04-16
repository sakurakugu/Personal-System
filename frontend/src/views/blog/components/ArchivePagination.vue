<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { computed } from 'vue'

const props = defineProps<{
  currentPage: number
  totalPages: number
}>()

const emit = defineEmits<{
  (e: 'update:currentPage', page: number): void
}>()

function generatePageNumbers(current: number, total: number): (number | string)[] {
  const delta = 2
  const rangeWithDots: (number | string)[] = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      rangeWithDots.push(i)
    }
    return rangeWithDots
  }

  const left = Math.max(2, current - delta)
  const right = Math.min(total - 1, current + delta)

  rangeWithDots.push(1)
  if (left > 2) {
    rangeWithDots.push('...')
  }
  for (let i = left; i <= right; i++) {
    rangeWithDots.push(i)
  }
  if (right < total - 1) {
    rangeWithDots.push('...')
  }
  if (total > 1) {
    rangeWithDots.push(total)
  }

  return rangeWithDots
}

const pageNumbers = computed(() => generatePageNumbers(props.currentPage, props.totalPages))
const activeIndex = computed(() => pageNumbers.value.findIndex(p => p === props.currentPage))

function goPrev() {
  if (props.currentPage > 1) {
    emit('update:currentPage', props.currentPage - 1)
  }
}

function goNext() {
  if (props.currentPage < props.totalPages) {
    emit('update:currentPage', props.currentPage + 1)
  }
}

function goPage(page: number) {
  emit('update:currentPage', page)
}
</script>

<template>
  <div class="pagination-root">
    <div class="pagination-inner" role="navigation" aria-label="文章列表">
      <button
        type="button"
        class="nav-btn"
        :class="{ disabled: currentPage === 1 }"
        aria-label="上一页"
        :aria-disabled="currentPage === 1 ? 'true' : 'false'"
        :tabindex="currentPage === 1 ? -1 : 0"
        @click="goPrev"
      >
        <Icon icon="material-symbols:chevron-left-rounded" class="nav-icon" aria-hidden="true" />
      </button>

      <div class="page-numbers">
        <div
          class="active-slider"
          :style="{ transform: `translateX(${activeIndex * 2.75}rem)` }"
        />
        <template v-for="(p, idx) in pageNumbers" :key="`${p}-${idx}`">
          <span v-if="p === '...'" class="ellipsis" aria-hidden="true">
            <Icon icon="material-symbols:more-horiz" />
          </span>
          <div
            v-else-if="p === currentPage"
            class="page-item page-current"
            aria-current="page"
          >
            {{ p }}
          </div>
          <button
            v-else
            type="button"
            class="page-item page-btn"
            :aria-label="`第 ${p} 页`"
            @click="goPage(p as number)"
          >
            {{ p }}
          </button>
        </template>
      </div>

      <button
        type="button"
        class="nav-btn"
        :class="{ disabled: currentPage === totalPages }"
        aria-label="下一页"
        :aria-disabled="currentPage === totalPages ? 'true' : 'false'"
        :tabindex="currentPage === totalPages ? -1 : 0"
        @click="goNext"
      >
        <Icon icon="material-symbols:chevron-right-rounded" class="nav-icon" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.pagination-root {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.pagination-inner {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.5rem;
  overflow: hidden;
  color: var(--primary);
  background: var(--card-bg);
  border: none;
  cursor: pointer;
  transition: background-color 150ms ease;
}

.nav-btn:hover:not(.disabled) {
  background: var(--btn-card-bg-hover);
}

.nav-btn:active:not(.disabled) {
  background: var(--btn-card-bg-active);
}

.nav-btn.disabled {
  pointer-events: none;
  color: rgba(0, 0, 0, 0.1);
}

.dark .nav-btn.disabled {
  color: rgba(255, 255, 255, 0.1);
}

.nav-icon {
  font-size: 1.75rem;
}

.page-numbers {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  background: var(--card-bg);
  overflow: hidden;
  color: var(--text-primary);
  font-weight: 700;
}

.dark .page-numbers {
  color: #cbd5e1;
}

.active-slider {
  position: absolute;
  left: 0;
  top: 0;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 0.5rem;
  background: var(--primary);
  transition: transform 200ms ease;
  z-index: 0;
}

.page-item {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  font-weight: 700;
  font-size: 1rem;
}

.page-current {
  color: #ffffff;
}

.dark .page-current {
  color: rgba(0, 0, 0, 0.7);
}

.page-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  transition: color 150ms ease;
}

.page-btn:hover {
  color: var(--primary);
}

.page-btn:active {
  transform: scale(0.9);
}

.ellipsis {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  font-size: 1.25rem;
  color: var(--text-secondary);
}
</style>
