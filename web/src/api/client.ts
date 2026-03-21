const MONKEY_URL = import.meta.env.VITE_MONKEY_URL ?? 'http://localhost:4000'
export const MONKEY_WS_URL = import.meta.env.VITE_MONKEY_WS_URL ?? MONKEY_URL.replace(/^http/, 'ws')

export function getToken(): string {
  return localStorage.getItem('jwt_token') ?? ''
}
export function setToken(token: string) {
  localStorage.setItem('jwt_token', token)
}
export function clearToken() {
  localStorage.removeItem('jwt_token')
}
export function getRefreshToken(): string {
  return localStorage.getItem('refresh_token') ?? ''
}
export function setRefreshToken(token: string) {
  localStorage.setItem('refresh_token', token)
}
export function clearRefreshToken() {
  localStorage.removeItem('refresh_token')
}
export function clearTokens() {
  clearToken()
  clearRefreshToken()
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return false
  try {
    const res = await fetch(`${MONKEY_URL}/api/poc/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) {
      clearTokens()
      return false
    }
    const data = await res.json()
    setToken(data.access_token)
    setRefreshToken(data.refresh_token)
    return true
  } catch {
    clearTokens()
    return false
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  requireAuth = true
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (requireAuth) {
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
  }
  let res = await fetch(`${MONKEY_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 401 && requireAuth) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      headers['Authorization'] = `Bearer ${getToken()}`
      res = await fetch(`${MONKEY_URL}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      })
    }
  }
  if (res.status === 401) {
    clearTokens()
    window.location.href = '/login'
    throw new Error('認証が必要です')
  }
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail ?? 'APIエラーが発生しました')
  }
  return res.json() as Promise<T>
}

export const api = {
  // Auth
  login: (username: string, password: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>(
      'POST', '/api/poc/auth/login', { username, password }, false
    ),
  refresh: (refresh_token: string) =>
    request<{ access_token: string; refresh_token: string }>(
      'POST', '/api/poc/auth/refresh', { refresh_token }, false
    ),
  logout: (refresh_token: string) =>
    request<{ message: string }>(
      'POST', '/api/poc/auth/logout', { refresh_token }, false
    ),
}

export const pocsApi = {
  getPocs: () =>
    request<import('../types').Poc[]>('GET', '/api/learn/pocs'),
}

export const jobsApi = {
  getJobs: (poc_id: number) =>
    request<import('../types').TrainingJob[]>('GET', `/api/learn/jobs/poc/${poc_id}`),
  getJob: (id: number) =>
    request<import('../types').TrainingJob>('GET', `/api/learn/jobs/${id}`),
  createJob: (data: {
    poc_id: number
    name: string
    training_data: { log_id: number; role: number }[]
    training_mode: number
    iters: number
    max_seq_length: number
    loss_threshold: number
  }) =>
    request<import('../types').TrainingJob>('POST', '/api/learn/jobs', data),
  executeJob: (id: number) =>
    request<import('../types').TrainingJob>('POST', `/api/learn/jobs/${id}/execute`),
  deleteJob: (id: number) =>
    request<void>('DELETE', `/api/learn/jobs/${id}`),
}

export const logsApi = {
  getLogs: (params: {
    poc_id: number
    dataset_id?: number
    user_id?: number
    trained?: string
  }) => {
    const query = new URLSearchParams()
    query.set('poc_id', String(params.poc_id))
    if (params.dataset_id) query.set('dataset_id', String(params.dataset_id))
    if (params.user_id) query.set('user_id', String(params.user_id))
    if (params.trained) query.set('trained', params.trained)
    return request<import('../types').Log[]>('GET', `/api/learn/logs?${query.toString()}`)
  },
  getDatasets: (poc_id: number) =>
    request<import('../types').Dataset[]>('GET', `/api/learn/logs/datasets?poc_id=${poc_id}`),
}

export const modelsApi = {
  getModels: (poc_id: number) =>
    request<import('../types').Model[]>('GET', `/api/learn/models/poc/${poc_id}`),
}
