<template>
  <div class="page">
    <div v-if="survey" class="card">
      <strong>{{ survey.title }}</strong>
      <div v-for="question in survey.questions" :key="question.id" class="question">
        <div>{{ question.title }}</div>
        <van-radio-group v-if="question.qtype === 'single'" v-model="answers[question.id]">
          <van-radio v-for="option in question.options" :key="option" :name="option">{{ option }}</van-radio>
        </van-radio-group>
        <van-field v-else v-model="answers[question.id]" placeholder="请填写" />
      </div>
      <van-button type="primary" block :disabled="survey.submitted" @click="submit">{{ survey.submitted ? '已提交' : '提交' }}</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { showToast } from 'vant'
import http from '@/api/http'

const survey = ref<any>(null)
const answers = reactive<Record<string, string>>({})

async function load() {
  const list = await http.get<never, { data: { items: Array<{ id: number }> } }>('/api/v1/plugins/surveys')
  const first = list.data.items[0]
  if (!first) return
  const detail = await http.get<never, { data: any }>(`/api/v1/plugins/surveys/${first.id}`)
  survey.value = detail.data
}

async function submit() {
  try {
    await http.post(`/api/v1/plugins/surveys/${survey.value.id}/submit`, { answers })
    survey.value.submitted = true
    showToast('提交成功')
  } catch (error) {
    showToast((error as Error).message)
  }
}

onMounted(load)
</script>

<style scoped>
.card { display: grid; gap: 4px; }
.card strong { font-size: 18px; }
.question { display: grid; gap: 10px; margin: 16px 0; }
.question :deep(.van-radio) { margin: 6px 0; }
.question :deep(.van-cell) {
  padding: 10px 12px;
  background: color-mix(in srgb, var(--app-text) 5%, var(--app-card));
  border-radius: 12px;
}
.card :deep(.van-button) { margin-top: 8px; }
</style>
