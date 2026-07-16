import { request } from './client'

export const TOKEN_KEY = 'bookweb_token'

export function getStoredToken() { return typeof localStorage === 'undefined' ? null : localStorage.getItem(TOKEN_KEY) }
export function setStoredToken(token) { localStorage.setItem(TOKEN_KEY, token) }
export function clearStoredToken() { localStorage.removeItem(TOKEN_KEY) }

export async function registerUser(payload) {
  const response = await request('/users/register/', { method: 'POST', body: payload })
  return response.data
}

export async function loginUser(payload) {
  const response = await request('/users/login/', { method: 'POST', body: payload })
  if (!response?.data?.token || !response?.data?.user) throw new Error('登录响应缺少认证信息')
  return response.data
}

export async function getProfile() {
  const response = await request('/users/profile/')
  return response.data
}

export async function updateProfile(payload) {
  const allowed = ['username', 'avatar', 'gender', 'email']
  const body = Object.fromEntries(allowed.filter(key => Object.prototype.hasOwnProperty.call(payload, key)).map(key => [key, payload[key]]))
  const response = await request('/users/profile/', { method: 'PUT', body })
  return response.data
}
export async function changePassword(payload) { const response = await request('/users/change-password/', { method: 'POST', body: payload }); return response.data }
