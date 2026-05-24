<script setup lang="ts">
import { 获取手机角色配置 } from '@/modules/认证/lib/role'
import ProfileSubpageHeader from '@/modules/个人/components/个人子页面标题.vue'
import { 使用认证存储 } from '@personal-system/domain/auth'
import { computed } from 'vue'

const auth = 使用认证存储()
const roleProfile = computed(() => 获取手机角色配置(auth.user?.role))
</script>

<template>
  <section class="page">
    <ProfileSubpageHeader
      title="角色能力"
      to="/me/account"
    />

    <section class="panel-card stack">
      <div class="capability-list">
        <article v-for="item in roleProfile.capabilities" :key="item.title" class="capability-card">
          <strong>{{ item.title }}</strong>
        </article>
      </div>
    </section>
  </section>
</template>
