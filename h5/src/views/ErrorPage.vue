<template>
  <div class="page">
    <van-empty image="error" :description="t('common.error')">
      <van-button type="primary" @click="$router.replace('/home')">{{ t('common.retry') }}</van-button>
    </van-empty>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>
