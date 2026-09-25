export interface ModuleMeta {
  path: string
  code: string
  name: string
  description: string
  schedule: string
}

export const MODULES: ModuleMeta[] = [
  {
    path: '/m1',
    code: 'M1',
    name: '项目空间与审计历史',
    description: '多合约项目、多次审计、审计 diff(修好哪些/新引入哪些)',
    schedule: 'W2',
  },
  {
    path: '/m2',
    code: 'M2',
    name: '审计结果与证明视图(核心)',
    description: '源码高亮 + 证明展开 + 反例轨迹 + 补丁 diff + 一键重跑',
    schedule: 'W1 D6',
  },
  {
    path: '/m3',
    code: 'M3',
    name: '规约库',
    description: '每条规约可查看/编辑/停用,标 SWC 分类与出处',
    schedule: 'W2',
  },
  {
    path: '/m4',
    code: 'M4',
    name: '报告导出与分享',
    description: '行业格式报告,每个结论带证明链接',
    schedule: 'W3',
  },
  {
    path: '/m5',
    code: 'M5',
    name: '批量审计 + CLI/CI',
    description: '批量任务、GitHub Action、PR 评论',
    schedule: 'W3',
  },
  {
    path: '/m6',
    code: 'M6',
    name: '漏洞知识库',
    description: '按 SWC 分类:原理 + 真实案例 + 复现 + 修复',
    schedule: 'W2',
  },
]
