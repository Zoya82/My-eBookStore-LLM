/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { changePassword, clearStoredToken, getProfile, getStoredToken, loginUser, registerUser, setStoredToken, updateProfile } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(Boolean(getStoredToken()))
  const [authError, setAuthError] = useState('')

  useEffect(() => {
    if (!getStoredToken()) return
    getProfile().then(setUser).catch(error => {
      clearStoredToken(); setUser(null); setAuthError(error.message)
    }).finally(() => setAuthLoading(false))
  }, [])

  useEffect(() => {
    const expired = () => { clearStoredToken(); setUser(null); setAuthError('登录已过期，请重新登录') }
    window.addEventListener('bookweb:auth-expired', expired)
    return () => window.removeEventListener('bookweb:auth-expired', expired)
  }, [])

  const value = useMemo(() => ({
    user, authLoading, authError, isAuthenticated: Boolean(user),
    register: async form => { setAuthError(''); return registerUser(form) },
    login: async form => { setAuthError(''); const result = await loginUser(form); setStoredToken(result.token); setUser(result.user); return result.user },
    logout: () => { clearStoredToken(); setUser(null) },
    refreshProfile: async () => { const next = await getProfile(); setUser(next); return next },
    updateProfile: async form => { const next = await updateProfile(form); setUser(next); return next },
    changePassword: async form => changePassword(form),
    clearAuthError: () => setAuthError(''),
  }), [user, authLoading, authError])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() { return useContext(AuthContext) }
