<script setup lang="ts">
withDefaults(defineProps<{
  showFirefly?: boolean
}>(), {
  showFirefly: true,
})

const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer">
    <div class="footer-divider" />
    <div class="footer-card">
      <div class="footer-content">
        <div class="footer-custom" />
        <div class="footer-line">
          © {{ currentYear }} Sakurakugu. All Rights Reserved.
        </div>
        <div class="footer-line">
          <a class="footer-link" href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer">粤ICP备2026031237号</a>
          /
          <a
            class="footer-link"
            href="https://beian.mps.gov.cn/#/query/webSearch?code=44011202003729"
            target="_blank"
            rel="noopener noreferrer"
          >
            粤公网安备44011202003729号
          </a>
        </div>
        <div class="footer-line powered-by">
          Powered by
          <a class="footer-link" href="https://cn.vuejs.org/" target="_blank" rel="noopener noreferrer">Vue3</a>
          <template v-if="showFirefly">
            &
            <a class="footer-link" href="https://github.com/CuteLeaf/Firefly" target="_blank" rel="noopener noreferrer">Firefly</a>
          </template>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  padding: 0 0 calc(24px + var(--app-safe-area-bottom));
  text-align: center;
}

.footer-divider {
  border-top: 1px dashed color-mix(in srgb, var(--el-color-primary) 38%, rgba(0, 0, 0, 0.32));
  margin: 1.5rem 10% 0.5rem;
  transition: border-color 0.3s;
}

:global(.dark) .footer-divider {
  border-top-color: color-mix(in srgb, var(--el-color-primary-light-5) 52%, rgba(255, 255, 255, 0.2));
}

.footer-card {
  border: none;
  border-radius: 0;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem 1rem;
}

.footer-content {
  font-size: 0.875rem;
  line-height: 1.625;
  color: var(--text-primary);
  text-align: center;
}

.footer-line {
  margin: 0.125rem 0;
}

.footer-link {
  color: var(--el-color-primary);
  font-weight: 500;
  text-decoration: none;
  transition: color 0.15s;
}

.footer-link:hover {
  color: var(--el-color-primary-dark-2);
  text-decoration: underline;
}

:global(.dark) .footer-link {
  color: var(--el-color-primary-light-5);
}

:global(.dark) .footer-link:hover {
  color: var(--el-color-primary-light-3);
}

.powered-by {
  color: inherit;
}

@media (max-width: 992px) {
  .footer-divider {
    margin: 1.5rem 10% 0.5rem;
  }
}

@media (max-width: 576px) {
  .footer-divider {
    margin: 1rem 10% 0.5rem;
  }

  .footer-card {
    padding: 0.5rem 1rem 1rem;
  }
}
</style>
