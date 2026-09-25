<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAppStore } from '@/stores/app'
import type { AnalysisMeta } from '@/types'
import { SEVERITY_LABEL } from '@/types'

const router = useRouter()
const store = useAppStore()

const filename = ref('VulnerableToken.sol')
const source = ref('')
const submitting = ref(false)
const error = ref('')
const recent = ref<AnalysisMeta[]>([])

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) readFile(file)
}

function readFile(file: File) {
  filename.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    source.value = String(reader.result ?? '')
  }
  reader.readAsText(file)
}

async function loadSample() {
  error.value = ''
  try {
    const res = await fetch('/api/v1/sample')
    if (!res.ok) throw new Error(`加载示例失败(${res.status})`)
    const data = await res.json()
    filename.value = data.filename
    source.value = data.source
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function submit() {
  if (!source.value.trim()) {
    error.value = '请先选择文件、粘贴代码或加载示例合约'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    const res = await fetch('/api/v1/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: filename.value, source: source.value }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail ?? `分析失败(${res.status})`)
    const detail = await fetch(`/api/v1/analyses/${data.id}`).then((r) => r.json())
    store.setCurrent(detail)
    router.push(`/result/${data.id}`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/analyses')
    if (res.ok) recent.value = (await res.json()).items
  } catch {
    recent.value = []
  }
})
</script>

<template>
  <section class="home">
    <h1>合约安全分析</h1>
    <p class="hint">上传或粘贴 Solidity 源码,引擎 + 形式化验证生成审计结果(演示版)</p>

    <div class="upload-card">
      <div class="upload-row">
        <label class="file-picker">
          <input type="file" accept=".sol" @change="onFileChange" />
          选择 .sol 文件
        </label>
        <button class="btn ghost" @click="loadSample">使用示例合约</button>
        <span v-if="filename" class="filename">{{ filename }}</span>
      </div>
      <textarea
        v-model="source"
        class="source-input"
        placeholder="// 或直接粘贴 Solidity 源码..."
        spellcheck="false"
      ></textarea>
      <div class="upload-actions">
        <button class="btn primary" :disabled="submitting" @click="submit">
          {{ submitting ? '分析中…' : '开始分析' }}
        </button>
        <span v-if="error" class="error">{{ error }}</span>
      </div>
    </div>

    <div v-if="recent.length" class="recent">
      <h2>最近分析</h2>
      <table class="recent-table">
        <thead>
          <tr>
            <th>合约</th>
            <th>状态</th>
            <th>漏洞数</th>
            <th>耗时</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in recent"
            :key="item.id"
            class="recent-row"
            @click="router.push(`/result/${item.id}`)"
          >
            <td>{{ item.name }}</td>
            <td>{{ item.status }}</td>
            <td>
              <span
                v-for="(sev) in ['high', 'medium', 'low', 'info']"
                :key="sev"
                class="count-chip"
                :class="sev"
              >
                {{ SEVERITY_LABEL[sev as keyof typeof SEVERITY_LABEL] }} {{ item.counts[sev as keyof typeof item.counts] }}
              </span>
            </td>
            <td>{{ item.duration_ms }} ms</td>
            <td>{{ new Date(item.created_at * 1000).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
