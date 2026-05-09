<script setup lang="ts">
import DesktopAuthEntryCard from '../components/DesktopAuthEntryCard.vue'
</script>

<template>
  <section class="page auth-page">
    <DesktopAuthEntryCard />
  </section>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding: 24px;
}
</style>
