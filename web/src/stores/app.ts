import { ref } from 'vue'
import { defineStore } from 'pinia'

import type { AnalysisDetail } from '@/types'

export const useAppStore = defineStore('app', () => {
  const current = ref<AnalysisDetail | null>(null)

  function setCurrent(detail: AnalysisDetail | null) {
    current.value = detail
  }

  return { current, setCurrent }
})
