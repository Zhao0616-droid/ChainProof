<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '@/api'

interface BatchFileItem {
  filename: string
  status: 'queued' | 'done' | 'failed'
  id?: string
  name?: string
  error?: string
}

interface BatchTask {
  id: string
  status: 'queued' | 'running' | 'done'
  total: number
  done: number
  files: BatchFileItem[]
}

const router = useRouter()
const selected = ref<{ filename: string; source: string }[]>([])
const error = ref('')
const task = ref<BatchTask | null>(null)
const submitting = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

function onFilesChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  error.value = ''
  for (const file of files) {
    const reader = new FileReader()
    reader.onload = () => {
      selected.value.push({ filename: file.name, source: String(reader.result ?? '') })
    }
    reader.readAsText(file)
  }
  input.value = ''
}

function removeAt(idx: number) {
  selected.value.splice(idx, 1)
}

async function startBatch() {
  if (!selected.value.length) {
    error.value = '请先选择要分析的 .sol 文件(可多选)'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    const res = await api<{ task_id: string }>('/api/v1/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files: selected.value }),
    })
    task.value = { id: res.task_id, status: 'queued', total: selected.value.length, done: 0, files: [] }
    timer = setInterval(poll, 1200)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    submitting.value = false
  }
}

async function poll() {
  if (!task.value) return
  try {
    task.value = await api<BatchTask>(`/api/v1/tasks/${task.value.id}`)
  } catch {
    stopPolling()
  }
  if (task.value.status === 'done') stopPolling()
}

function stopPolling() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function startOver() {
  stopPolling()
  task.value = null
  selected.value = []
}

onBeforeUnmount(stopPolling)
</script>

<template>
  <section class="batch">
    <div class="result-header">
      <div>
        <h1>批量审计</h1>
        <p class="hint">选择多个 .sol 文件,后台队列逐个分析(演示版内存队列)</p>
      </div>
      <RouterLink to="/" class="btn ghost">返回</RouterLink>
    </div>

    <div v-if="!task" class="upload-card">
      <div class="upload-row">
        <label class="file-picker">
          <input type="file" accept=".sol" multiple @change="onFilesChange" />
          选择多个 .sol 文件
        </label>
        <span class="filename">已选 {{ selected.length }} 个</span>
      </div>
      <ul v-if="selected.length" class="file-list">
        <li v-for="(f, i) in selected" :key="i">
          <span>{{ f.filename }}</span>
          <button class="btn danger small" @click="removeAt(i)">移除</button>
        </li>
      </ul>
      <div class="upload-actions">
        <button class="btn primary" :disabled="submitting || !selected.length" @click="startBatch">
          {{ submitting ? '提交中…' : '开始批量分析' }}
        </button>
        <span v-if="error" class="error">{{ error }}</span>
      </div>
    </div>

    <div v-else class="upload-card">
      <div class="batch-head">
        <span>
          任务 {{ task.id }} · {{ task.status === 'done' ? '完成' : '进行中' }}
          ({{ task.done }}/{{ task.total }})
        </span>
        <button class="btn ghost small" @click="startOver">再来一批</button>
      </div>
      <div class="progress">
        <div
          class="progress-bar"
          :style="{ width: `${task.total ? (task.done / task.total) * 100 : 0}%` }"
        ></div>
      </div>
      <table class="recent-table">
        <thead>
          <tr>
            <th>文件</th>
            <th>状态</th>
            <th>结果</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(f, i) in task.files" :key="i">
            <td>{{ f.filename }}</td>
            <td>
              <span class="count-chip" :class="f.status">
                {{ f.status === 'done' ? '完成' : f.status === 'failed' ? '失败' : '排队中' }}
              </span>
            </td>
            <td>
              <span v-if="f.status === 'failed'" class="error">{{ f.error }}</span>
              <button
                v-else-if="f.status === 'done'"
                class="btn ghost small"
                @click="router.push(`/result/${f.id}`)"
              >
                查看 {{ f.name }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
