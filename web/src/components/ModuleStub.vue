<script setup lang="ts">
import { useRoute } from 'vue-router'

import type { ModuleMeta } from '@/modules/meta'

const route = useRoute()
const moduleMeta = route.meta.module as ModuleMeta
</script>

<template>
  <section class="module-page">
    <h1>{{ moduleMeta.code }} {{ moduleMeta.name }}</h1>
    <p class="description">{{ moduleMeta.description }}</p>
    <p class="placeholder">占位页 — 实现排期 {{ moduleMeta.schedule }}</p>
  </section>
</template>
