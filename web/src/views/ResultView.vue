<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { useAppStore } from '@/stores/app'
import type { AnalysisDetail, Finding } from '@/types'
import { SEVERITY_LABEL, TYPE_LABEL } from '@/types'

const route = useRoute()
const store = useAppStore()

const detail = ref<AnalysisDetail | null>(store.current)
const error = ref('')
const expanded = ref<Record<string, boolean>>({})
const sourceLines = ref<HTMLElement | null>(null)

const findingLines = computed(() => {
  const set = new Set<number>()
  for (const f of detail.value?.result.findings ?? []) set.add(f.location.line)
  return set
})

onMounted(async () => {
  if (detail.value && detail.value.id === route.params.id) return
  try {
    const res = await fetch(`/api/v1/analyses/${route.params.id}`)
    if (!res.ok) throw new Error(`记录不存在(${res.status})`)
    detail.value = await res.json()
    store.setCurrent(detail.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
})

function toggle(id: string) {
  expanded.value[id] = !expanded.value[id]
}

function jumpToLine(line: number) {
  const el = sourceLines.value?.querySelector(`.src-line[data-line="${line}"]`)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  el.classList.add('flash')
  nextTick(() => setTimeout(() => el.classList.remove('flash'), 1500))
}

function shortHash(hash: string) {
  return `${hash.slice(0, 10)}…${hash.slice(-6)}`
}

function severityOrder(f: Finding) {
  return { high: 0, medium: 1, low: 2, info: 3 }[f.severity]
}
</script>

<template>
  <section v-if="detail" class="result">
    <div class="result-header">
      <div>
        <h1>{{ detail.result.contract.name }}</h1>
        <p class="hint">
          {{ detail.result.contract.compiler }} · hash {{ shortHash(detail.result.contract.hash) }}
        </p>
      </div>
      <RouterLink to="/" class="btn ghost">返回</RouterLink>
    </div>

    <div class="summary">
      <div class="summary-item">
        <div class="summary-label">状态</div>
        <div class="summary-value" :class="detail.result.analysis.status">
          {{ detail.result.analysis.status }}
        </div>
      </div>
      <div class="summary-item">
        <div class="summary-label">证明覆盖</div>
        <div class="summary-value">
          {{ detail.result.analysis.coverage.proved }}/{{ detail.result.analysis.coverage.total }}
        </div>
      </div>
      <div class="summary-item">
        <div class="summary-label">发现</div>
        <div class="summary-value">
          <span
            v-for="sev in (['high', 'medium', 'low', 'info'] as const)"
            :key="sev"
            class="count-chip"
            :class="sev"
          >
            {{ SEVERITY_LABEL[sev] }} {{ detail.counts[sev] }}
          </span>
        </div>
      </div>
      <div class="summary-item">
        <div class="summary-label">耗时</div>
        <div class="summary-value">{{ detail.result.analysis.duration_ms }} ms</div>
      </div>
      <div class="summary-item">
        <div class="summary-label">模型</div>
        <div class="summary-value">{{ detail.result.analysis.model_version }}</div>
      </div>
    </div>

    <div v-if="detail.result.unverified.length" class="unverified-box">
      <strong>诚实声明:</strong>
      <span v-for="(u, i) in detail.result.unverified" :key="i">{{ u.reason }}</span>
    </div>

    <h2>漏洞发现({{ detail.result.findings.length }})</h2>
    <div v-if="!detail.result.findings.length" class="no-findings">
      未发现漏洞模式。
    </div>

    <article
      v-for="f in [...detail.result.findings].sort(severityOrder)"
      :key="f.id"
      class="finding-card"
      :class="f.severity"
    >
      <header class="finding-header">
        <span class="severity-badge" :class="f.severity">{{ SEVERITY_LABEL[f.severity] }}</span>
        <span class="finding-title">{{ TYPE_LABEL[f.type] ?? f.type }}</span>
        <span class="swc-chip">{{ f.swc }}</span>
        <button
          class="btn ghost small locate"
          @click="jumpToLine(f.location.line)"
        >
          定位 {{ f.location.line }} 行
        </button>
        <button class="toggle" @click="toggle(f.id)">
          {{ expanded[f.id] ? '收起' : '展开' }}证据
        </button>
      </header>

      <p class="explanation">{{ f.explanation }}</p>

      <div v-if="expanded[f.id]" class="evidence">
        <div class="evidence-head">
          <span>证据类型:{{ f.evidence.kind }}</span>
          <span v-if="f.evidence.smt_status">SMT: {{ f.evidence.smt_status }}</span>
          <span v-if="f.evidence.proof_ref">{{ f.evidence.proof_ref }}</span>
        </div>

        <table v-if="f.evidence.counterexample?.length" class="evidence-table">
          <thead>
            <tr>
              <th>步骤</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="step in f.evidence.counterexample" :key="step.step">
              <td class="step-no">{{ step.step }}</td>
              <td class="step-state">
                <div v-for="(v, k) in step.state" :key="k">
                  <code>{{ k }}</code> = {{ v }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else-if="f.evidence.kind === 'pattern'" class="evidence-note">
          模式匹配证据:检测器命中可疑代码模式,未经求解器证明,需人工复核。
        </p>

        <div class="patch">
          <div class="patch-head">
            <span>建议补丁</span>
            <span class="patch-verified" :class="{ ok: f.patch.verified }">
              {{ f.patch.verified ? '已验证' : '未验证' }}
            </span>
          </div>
          <pre class="diff">{{ f.patch.diff }}</pre>
        </div>
      </div>
    </article>

    <h2>源码</h2>
    <div ref="sourceLines" class="source-viewer">
      <div
        v-for="(line, i) in detail.source.split('\n')"
        :key="i"
        class="src-line"
        :class="{ hit: findingLines.has(i + 1) }"
        :data-line="i + 1"
      >
        <span class="line-no">{{ i + 1 }}</span>
        <span class="line-code">{{ line }}</span>
      </div>
    </div>
  </section>

  <section v-else class="result">
    <p v-if="error" class="error">{{ error }}</p>
    <p v-else>加载中…</p>
  </section>
</template>
