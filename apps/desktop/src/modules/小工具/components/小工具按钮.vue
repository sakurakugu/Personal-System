<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'
import { ElIcon } from 'element-plus'
import { computed, useAttrs, useSlots } from 'vue'

defineOptions({
  inheritAttrs: false,
})

const props = withDefaults(defineProps<{
  active?: boolean
  disabled?: boolean
  loading?: boolean
  size?: 'md' | 'compact' | 'sm'
  variant?: 'icon' | 'text' | 'secondary' | 'primary'
}>(), {
  active: false,
  disabled: false,
  loading: false,
  size: 'md',
  variant: 'icon',
})

const attrs = useAttrs()
const slots = useSlots()

const hasIcon = computed(() => props.loading || Boolean(slots.icon))
const hasLabel = computed(() => Boolean(slots.default))
const buttonDisabled = computed(() => props.disabled || props.loading)
const buttonType = computed<'button' | 'submit' | 'reset'>(() => {
  const rawType = attrs.type
  if (rawType === 'submit' || rawType === 'reset') {
    return rawType
  }
  return 'button'
})
</script>

<template>
  <button
    v-bind="attrs"
    :type="buttonType"
    class="widget-button"
    :class="[
      `widget-button--${variant}`,
      `widget-button--${size}`,
      {
        'widget-button--active': active,
        'widget-button--icon-only': !hasLabel,
        'widget-button--with-icon': hasIcon,
        'is-disabled': buttonDisabled,
      },
    ]"
    :disabled="buttonDisabled"
  >
    <span v-if="hasIcon" class="widget-button__icon-shell">
      <ElIcon v-if="loading" class="widget-button__icon widget-button__icon--spin">
        <Loading />
      </ElIcon>
      <slot v-else name="icon" />
    </span>
    <span v-if="hasLabel" class="widget-button__label">
      <slot />
    </span>
  </button>
</template>

<style>
.widget-button {
  --widget-button-size: 34px;
  --widget-button-radius: 8px;
  --widget-button-padding-inline: 12px;
  --widget-button-gap: 8px;
  --widget-button-color: var(--desktop-accent);
  --widget-button-background: transparent;
  --widget-button-hover-background: transparent;
  --widget-button-active-background: color-mix(in srgb, var(--desktop-accent) 10%, transparent);
  --widget-button-pressed-background: var(--desktop-accent);
  --widget-button-pressed-color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--widget-button-size);
  min-height: var(--widget-button-size);
  padding: 0 var(--widget-button-padding-inline);
  border: none;
  border-radius: var(--widget-button-radius);
  background: var(--widget-button-background);
  color: var(--widget-button-color);
  cursor: pointer;
  box-sizing: border-box;
  flex-shrink: 0;
  transition:
    background-color 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease,
    opacity 0.18s ease;
  appearance: none;
}

.widget-button:hover {
  background: var(--widget-button-hover-background);
  color: var(--widget-button-color);
}

.widget-button:active {
  background: var(--widget-button-pressed-background);
  color: var(--widget-button-pressed-color);
  transform: scale(0.94);
}

.widget-button:disabled,
.widget-button.is-disabled {
  opacity: 0.56;
  cursor: not-allowed;
}

.widget-button:disabled:active,
.widget-button.is-disabled:active {
  transform: none;
}

.widget-button--active {
  background: var(--widget-button-active-background);
}

.widget-button--active:hover {
  background: var(--widget-button-active-background);
  color: var(--widget-button-color);
}

.widget-button--md {
  --widget-button-size: 34px;
}

.widget-button--compact {
  --widget-button-size: 32px;
}

.widget-button--sm {
  --widget-button-size: 28px;
  --widget-button-radius: 6px;
  --widget-button-padding-inline: 8px;
}

.widget-button--icon {
  width: var(--widget-button-size);
  height: var(--widget-button-size);
  padding: 0;
}

.widget-button--text {
  --widget-button-padding-inline: 10px;
  --widget-button-color: var(--desktop-text);
  --widget-button-hover-background: color-mix(in srgb, var(--desktop-accent) 8%, transparent);
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.widget-button--secondary {
  --widget-button-color: var(--desktop-accent);
  --widget-button-background: color-mix(in srgb, var(--desktop-accent) 10%, transparent);
  --widget-button-hover-background: color-mix(in srgb, var(--desktop-accent) 16%, transparent);
  --widget-button-active-background: color-mix(in srgb, var(--desktop-accent) 16%, transparent);
  --widget-button-pressed-background: var(--desktop-accent);
  min-width: 72px;
  font-size: 14px;
  font-weight: 700;
}

.widget-button--primary {
  --widget-button-color: white;
  --widget-button-background: var(--desktop-accent);
  --widget-button-hover-background: color-mix(in srgb, var(--desktop-accent) 88%, black);
  --widget-button-active-background: color-mix(in srgb, var(--desktop-accent) 88%, black);
  --widget-button-pressed-background: color-mix(in srgb, var(--desktop-accent) 76%, black);
  min-width: 88px;
  font-size: 14px;
  font-weight: 700;
}

.widget-button--with-icon {
  gap: var(--widget-button-gap);
}

.widget-button__icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.widget-button__label {
  display: inline-flex;
  align-items: center;
  line-height: 1;
  white-space: nowrap;
}

.widget-button :is(.iconify, .el-icon, svg) {
  color: currentColor;
}

.widget-button .iconify,
.widget-button .el-icon {
  font-size: 18px;
}

.widget-button--sm .iconify,
.widget-button--sm .el-icon {
  font-size: 14px;
}

.widget-button--sm .widget-button__icon-shell {
  width: 14px;
  height: 14px;
}

.widget-button__icon--spin {
  animation: widget-button-spin 0.9s linear infinite;
}

@keyframes widget-button-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>
