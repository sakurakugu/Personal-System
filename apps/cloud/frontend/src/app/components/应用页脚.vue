<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElIcon, ElTooltip } from 'element-plus'
import { Switch } from '@element-plus/icons-vue'

withDefaults(defineProps<{
  showFirefly?: boolean
}>(), {
  showFirefly: true,
})

const currentYear = new Date().getFullYear()

// .top 与 .com 是同一主体下的两个独立网站，ICP 备案号与公网安备号都不同。
// 默认展示当前访问域名对应的备案信息，页脚右侧图标可按列表顺序切换到另一个域名。
const 备案列表 = [
  {
    domain: 'sakurakugu.com',
    icp: '粤ICP备2026031237号-2',
    公安备案号: '', // TODO: .com 公网安备申请通过后填入
    公安查询码: '',
  },
  {
    domain: 'sakurakugu.top',
    icp: '粤ICP备2026031237号-1',
    公安备案号: '粤公网安备44011202003729号',
    公安查询码: '44011202003729',
  },
]

const 访问域名 = window.location.hostname.toLowerCase()
const 初始索引 = 备案列表.findIndex((item) => 访问域名.endsWith(item.domain))
const 当前索引 = ref(初始索引 >= 0 ? 初始索引 : 0)
const 备案信息 = computed(() => 备案列表[当前索引.value])

function 切换备案域名() {
  当前索引.value = (当前索引.value + 1) % 备案列表.length
}
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
          <a class="footer-link" href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer">{{ 备案信息.icp }}</a>
          <template v-if="备案信息.公安备案号">
            /
            <a
              class="footer-link"
              :href="`https://beian.mps.gov.cn/#/query/webSearch?code=${备案信息.公安查询码}`"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ 备案信息.公安备案号 }}
            </a>
          </template>
          <ElTooltip :content="`当前显示 ${备案信息.domain} 的备案号，点击切换`" placement="top">
            <button
              type="button"
              class="footer-beian-switch"
              :aria-label="`切换备案域名，当前为 ${备案信息.domain}`"
              @click="切换备案域名"
            >
              <ElIcon><Switch /></ElIcon>
            </button>
          </ElTooltip>
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

.footer-beian-switch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  margin-left: 0.375rem;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--el-color-primary);
  cursor: pointer;
  vertical-align: -0.1rem;
  transition: color 0.15s, background-color 0.15s;
}

.footer-beian-switch:hover {
  color: var(--el-color-primary-dark-2);
  background: color-mix(in srgb, var(--el-color-primary) 14%, transparent);
}

.footer-beian-switch:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 2px;
}

:global(.dark) .footer-beian-switch {
  color: var(--el-color-primary-light-5);
}

:global(.dark) .footer-beian-switch:hover {
  color: var(--el-color-primary-light-3);
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
