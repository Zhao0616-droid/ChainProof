export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  const data: unknown = await res.json().catch(() => null)
  if (!res.ok) {
    const detail =
      data && typeof data === 'object' && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : `请求失败(${res.status})`
    throw new Error(detail)
  }
  return data as T
}
