<template>
  <van-config-provider :theme="app.theme" :theme-vars="themeVars">
    <router-view />
  </van-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const themeVars = computed(() => ({ primaryColor: app.config.settings.h5_primary || '#1989fa' }))
</script>
