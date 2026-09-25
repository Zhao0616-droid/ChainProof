<script setup lang="ts">
import { MODULES } from '@/modules/meta'
</script>

<template>
  <section class="home">
    <h1>模块导航</h1>
    <p class="hint">
      Day 1 骨架:假集成用 mock 数据见 server 的 /api/v1/mock/analysis_result
      与 examples/analysis_result.json
    </p>
    <div class="module-grid">
      <RouterLink v-for="m in MODULES" :key="m.code" :to="m.path" class="module-card">
        <div class="module-code">{{ m.code }}</div>
        <div class="module-name">{{ m.name }}</div>
        <div class="module-desc">{{ m.description }}</div>
        <div class="module-schedule">排期 {{ m.schedule }}</div>
      </RouterLink>
    </div>
  </section>
</template>
