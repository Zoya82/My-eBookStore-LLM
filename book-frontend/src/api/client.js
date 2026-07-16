const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'
const DEFAULT_TIMEOUT = 30000

function buildUrl(path, params = {}) {
  const url = new URL(`${API_BASE.replace(/\/$/, '')}/${String(path).replace(/^\//, '')}`)
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })
  return url.toString()
}

function getErrorMessage(payload, fallback) {
  if (!payload) return fallback
  if (typeof payload === 'string') return payload
  const primary = payload.msg ?? payload.message ?? payload.detail
  if (primary !== undefined && primary !== null) {
    return typeof primary === 'object' ? getErrorMessage(primary, fallback) : String(primary)
  }
  if (payload.data && typeof payload.data === 'object') return getErrorMessage(payload.data, fallback)
  if (typeof payload === 'object') {
    const errors = Object.entries(payload).map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(', ') : value}`).join('; ')
    if (errors) return errors
  }
  return fallback
}

function isBusinessError(data) {
  return data?.success === false || (typeof data?.code === 'number' && data.code >= 400)
}

export async function request(path, options = {}) {
  const { method = 'GET', params, body, timeout = DEFAULT_TIMEOUT, headers: customHeaders = {}, ...fetchOptions } = options
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)
  const headers = { Accept: 'application/json', ...customHeaders }
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('bookweb_token') : null
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  try {
    const response = await fetch(buildUrl(path, params), {
      ...fetchOptions,
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    })
    const text = response.status === 204 ? '' : await response.text()
    let data = null
    if (text) {
      try { data = JSON.parse(text) } catch { data = text }
    }
    if (response.status === 401 && token && !String(path).includes('/login/')) {
      localStorage.removeItem('bookweb_token')
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('bookweb:auth-expired'))
    }
    if (!response.ok || isBusinessError(data)) {
      const error = new Error(getErrorMessage(data, `请求失败（HTTP ${response.status}）`))
      error.status = response.status
      error.response = response
      error.data = data
      throw error
    }
    return data
  } catch (cause) {
    if (cause.status !== undefined) throw cause
    const error = new Error(cause.name === 'AbortError' ? '请求超时' : (cause.message || '网络请求失败'), { cause })
    error.status = null
    error.response = null
    error.data = null
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

export { API_BASE }
