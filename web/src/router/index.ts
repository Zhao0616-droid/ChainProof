import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

import { MODULES } from '@/modules/meta'
import HomeView from '@/views/HomeView.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/result/:id', name: 'result', component: () => import('@/views/ResultView.vue') },
  { path: '/m1', name: 'M1', component: () => import('@/modules/m1/ProjectSpaceView.vue') },
  { path: '/m2', name: 'M2', component: () => import('@/modules/m2/AuditResultView.vue') },
  { path: '/m3', name: 'M3', component: () => import('@/modules/m3/SpecLibraryView.vue') },
  { path: '/m4', name: 'M4', component: () => import('@/modules/m4/ReportExportView.vue') },
  { path: '/m5', name: 'M5', component: () => import('@/modules/m5/BatchAuditView.vue') },
  { path: '/m6', name: 'M6', component: () => import('@/modules/m6/KnowledgeBaseView.vue') },
]

// 模块元信息供占位页显示(真实实现后删除)
for (const route of routes.slice(1)) {
  if (!route.path.startsWith('/result')) {
    route.meta = { module: MODULES.find((m) => m.path === route.path) }
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
