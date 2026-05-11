const runtimeEnv = (globalThis as any).__APP_ENV__ || {}
const rawApiBaseUrl = String(runtimeEnv.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || '').trim()

export const API_BASE_URL = rawApiBaseUrl.replace(/\/+$/, '')

const normalizePath = (path: string) => {
  const value = String(path || '')
  return value.startsWith('/') ? value : `/${value}`
}

export const apiUrl = (path: string) => {
  const value = String(path || '')
  if (/^https?:\/\//i.test(value)) {
    return value
  }

  return API_BASE_URL ? `${API_BASE_URL}${normalizePath(value)}` : normalizePath(value)
}
