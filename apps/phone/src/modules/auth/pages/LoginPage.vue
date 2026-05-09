<script setup lang="ts">
import PhoneAuthEntryCard from '../components/PhoneAuthEntryCard.vue'
</script>

<template>
  <section class="page auth-page">
    <PhoneAuthEntryCard />
  </section>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding-top: 24px;
  padding-bottom: 24px;
}
</style>
