export type Severity = 'high' | 'medium' | 'low' | 'info'

export interface CounterexampleStep {
  step: number
  state: Record<string, string>
}

export interface FindingEvidence {
  kind: 'formal' | 'counterexample' | 'pattern'
  smt_status?: 'sat' | 'unsat' | 'unknown'
  counterexample?: CounterexampleStep[]
  proof_ref?: string
}

export interface FindingLocation {
  file: string
  line: number
  function?: string
}

export interface PatchInfo {
  diff: string
  verified: boolean
}

export interface Finding {
  id: string
  swc: string
  type: string
  severity: Severity
  location: FindingLocation
  evidence: FindingEvidence
  explanation: string
  patch: PatchInfo
}

export interface AnalysisResult {
  contract: {
    name: string
    hash: string
    compiler: string
  }
  analysis: {
    status: 'done' | 'partial' | 'timeout' | 'failed'
    coverage: { proved: number; total: number }
    duration_ms: number
    model_version: string
  }
  findings: Finding[]
  unverified: { reason: string; scope: string }[]
}

export interface AnalysisMeta {
  id: string
  name: string
  created_at: number
  status: string
  duration_ms: number
  findings_total: number
  counts: Record<Severity, number>
}

export interface AnalysisDetail extends AnalysisMeta {
  source: string
  result: AnalysisResult
}

export const SEVERITY_LABEL: Record<Severity, string> = {
  high: '高危',
  medium: '中危',
  low: '低危',
  info: '提示',
}

export const TYPE_LABEL: Record<string, string> = {
  reentrancy: '重入',
  'unchecked-low-level-call': '未检查的外部调用返回值',
  'tx-origin': 'tx.origin 鉴权',
  timestamp: '时间戳依赖',
  'unchecked-overflow': 'unchecked 溢出',
  'spec-violation': '规约违规',
  'spec-proved': '规约已证明',
}
