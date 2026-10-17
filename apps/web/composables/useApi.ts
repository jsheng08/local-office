// Shared API layer: X-Demo-User header, 120 s timeout, verbatim errors, last-call meta.
export interface CallMeta {
  use_case?: string; model?: string; endpoint?: string; latency_ms?: number
  completion_tokens?: number; prompt_tokens?: number; tok_per_s?: number; attempts?: number
}
export interface ApiError { status?: number; body: string }

export const useCurrentUser = () => useState<string>('user', () => {
  try { return localStorage.getItem('lo_user') || 'aisyah' } catch { return 'aisyah' }
})
export const useLastCall = () => useState<CallMeta | null>('lastCall', () => null)

export function toApiError(e: any): ApiError {
  const status: number | undefined = e?.response?.status ?? e?.statusCode
  const data = e?.data ?? e?.response?._data
  let body = ''
  if (data && typeof data === 'object') {
    const keys = Object.keys(data)
    body = keys.length === 1 && keys[0] === 'detail'
      ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail, null, 2))
      : JSON.stringify(data, null, 2)
  } else if (typeof data === 'string' && data) {
    body = data
  } else if (e?.name === 'AbortError' || /aborted|timeout/i.test(String(e?.message))) {
    body = 'Request aborted after 120 s timeout'
  } else {
    body = String(e?.message || e)
  }
  return { status, body }
}

export function useApi() {
  const user = useCurrentUser()
  const lastCall = useLastCall()
  return async function api<T = any>(path: string, opts: { method?: string; body?: any; timeout?: number } = {}): Promise<T> {
    const ctrl = new AbortController()
    const timer = setTimeout(() => ctrl.abort(), opts.timeout ?? 120000)
    try {
      const res: any = await $fetch(path, {
        method: (opts.method || 'GET') as any,
        body: opts.body,
        headers: user.value ? { 'X-Demo-User': user.value } : {},
        signal: ctrl.signal,
      })
      const calls = res?.meta?.calls
      if (Array.isArray(calls) && calls.length) lastCall.value = calls[calls.length - 1]
      return res as T
    } catch (e: any) {
      throw toApiError(e)
    } finally {
      clearTimeout(timer)
    }
  }
}

// Busy state with live elapsed seconds for AI actions.
export function useBusy() {
  const busy = ref(false)
  const elapsed = ref(0)
  let iv: any = null
  async function run<T>(fn: () => Promise<T>): Promise<T> {
    busy.value = true; elapsed.value = 0
    const t0 = Date.now()
    iv = setInterval(() => { elapsed.value = (Date.now() - t0) / 1000 }, 100)
    try { return await fn() } finally {
      clearInterval(iv); elapsed.value = (Date.now() - t0) / 1000; busy.value = false
    }
  }
  return { busy, elapsed, run }
}

export const fmtNum = (n: any, d = 1) =>
  n == null || isNaN(Number(n)) ? '—' : Number(n).toLocaleString('en-MY', { maximumFractionDigits: d })
export const fmtRM = (n: any) => {
  if (n == null || isNaN(Number(n))) return '—'
  const v = Number(n)
  return (v < 0 ? '-' : '') + 'RM ' + Math.abs(v).toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
