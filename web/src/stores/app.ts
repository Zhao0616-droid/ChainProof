import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', () => {
  const analysisResult = ref<unknown>(null)

  async function loadMockResult() {
    const res = await fetch('/api/v1/mock/analysis_result')
    analysisResult.value = await res.json()
  }

  return { analysisResult, loadMockResult }
})
