<template>
  <div class="page dicts">
    <aside class="types">
      <div class="toolbar">
        <strong>字典类型</strong>
        <el-button type="primary" link @click="openType()">新建</el-button>
      </div>
      <el-scrollbar>
        <button v-for="item in dicts" :key="item.id" class="type" :class="{ on: item.id === currentId }" @click="currentId = item.id">
          <span>{{ item.name }}</span>
          <small>{{ item.code }}</small>
        </button>
        <el-empty v-if="!dicts.length" description="还没有字典" />
      </el-scrollbar>
    </aside>
    <section class="items">
      <div class="toolbar">
        <strong>{{ current?.name || '字典项' }}</strong>
        <el-button type="primary" :disabled="!current" @click="openItem()">新建字典项</el-button>
        <el-button :disabled="!current" @click="openType(current)">编辑类型</el-button>
        <el-button type="danger" plain :disabled="!current" @click="removeType">删除类型</el-button>
      </div>
      <el-table :data="current?.items || []" border class="grid">
        <el-table-column prop="label" label="名称" />
        <el-table-column prop="value" label="值" />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column label="启用" width="80"><template #default="{ row }">{{ row.enabled ? '是' : '否' }}</template></el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button link @click="openItem(row)">编辑</el-button>
            <el-button link type="danger" @click="removeItem(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
    <el-dialog v-model="typeVisible" title="字典类型" width="420px">
      <el-form label-width="72px">
        <el-form-item label="名称"><el-input v-model="typeForm.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="typeForm.code" :disabled="Boolean(typeForm.id)" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="saveType">保存</el-button></template>
    </el-dialog>
    <el-dialog v-model="itemVisible" title="字典项" width="420px">
      <el-form label-width="72px">
        <el-form-item label="名称"><el-input v-model="itemForm.label" /></el-form-item>
        <el-form-item label="值"><el-input v-model="itemForm.value" /></el-form-item>
        <el-form-item label="排序"><el-input v-model.number="itemForm.sort" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="saveItem">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'

const dicts = ref<any[]>([])
const currentId = ref<number | null>(null)
const current = computed(() => dicts.value.find((item) => item.id === currentId.value))
const typeVisible = ref(false)
const itemVisible = ref(false)
const typeForm = reactive<any>({ name: '', code: '' })
const itemForm = reactive<any>({ label: '', value: '', sort: 0, enabled: true })

async function load() {
  dicts.value = (await http.get<never, { data: { items: any[] } }>('/api/v1/admin/dicts')).data.items
  if (!dicts.value.some((item) => item.id === currentId.value)) currentId.value = dicts.value[0]?.id ?? null
}

function openType(row?: any) {
  Object.assign(typeForm, row ? { id: row.id, name: row.name, code: row.code } : { id: undefined, name: '', code: '' })
  typeVisible.value = true
}

async function saveType() {
  await http.post('/api/v1/admin/dicts/save', { id: typeForm.id, name: typeForm.name, code: typeForm.code })
  typeVisible.value = false
  ElMessage.success('已保存')
  load()
}

async function removeType() {
  if (!current.value) return
  await ElMessageBox.confirm(`删除字典 ${current.value.name}？`, '确认')
  await http.post('/api/v1/admin/dicts/delete', { id: current.value.id })
  load()
}

function openItem(row?: any) {
  Object.assign(itemForm, row || { id: undefined, label: '', value: '', sort: 0, enabled: true })
  itemVisible.value = true
}

async function saveItem() {
  await http.post('/api/v1/admin/dicts/save', {
    id: itemForm.id,
    dict_type_id: currentId.value,
    label: itemForm.label,
    value: itemForm.value,
    sort: itemForm.sort || 0,
    enabled: true,
  })
  itemVisible.value = false
  ElMessage.success('已保存')
  load()
}

async function removeItem(row: any) {
  await http.post('/api/v1/admin/dicts/delete', { item_id: row.id })
  load()
}

onMounted(load)
</script>

<style scoped>
.dicts { flex-direction: row; gap: 16px; padding: 16px; }
.types { width: 240px; flex: none; display: flex; flex-direction: column; min-height: 0; border-right: 1px solid #e8edf5; padding-right: 12px; }
.items { flex: 1; min-width: 0; display: flex; flex-direction: column; min-height: 0; }
.type { display: flex; flex-direction: column; align-items: flex-start; width: 100%; border: 0; background: transparent; text-align: left; padding: 10px 12px; border-radius: 8px; cursor: pointer; }
.type.on { background: #eff6ff; color: #1d4ed8; }
.type small { color: #94a3b8; }
.grid { flex: 1; min-height: 0; }
</style>
