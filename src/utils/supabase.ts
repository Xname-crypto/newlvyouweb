import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

const supabaseProjectRef = (() => {
  try {
    return new URL(supabaseUrl).hostname.split('.')[0]
  } catch {
    return ''
  }
})()

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Supabase URL or Anon Key is missing. Please check your .env file.')
}

const SUPABASE_STORAGE_KEYS = [
  supabaseProjectRef ? `sb-${supabaseProjectRef}-auth-token` : '',
  supabaseProjectRef ? `sb-${supabaseProjectRef}-auth-token-code-verifier` : '',
].filter(Boolean)

const SUPABASE_DEGRADED_KEY = supabaseProjectRef
  ? `sb-${supabaseProjectRef}-auth-degraded`
  : 'sb-auth-degraded'

const DEGRADE_RESPONSE_BODY = {
  error: 'Supabase auth degraded to guest mode.',
}

let hasLoggedDegradedMode = false

export const isSupabaseNetworkError = (error: unknown) => {
  const message = String((error as any)?.message || error || '').toLowerCase()
  const name = String((error as any)?.name || '').toLowerCase()

  return [
    'failed to fetch',
    'networkerror',
    'load failed',
    'err_name_not_resolved',
    'fetch failed',
    'signal is aborted',
    'aborterror',
    'the user aborted a request',
    'request was aborted',
    'lockmanager',
    'supabase auth degraded to guest mode',
  ].some((keyword) => message.includes(keyword)) || name === 'aborterror'
}

export const isSupabaseMissingSessionError = (error: unknown) => {
  const message = String((error as any)?.message || error || '').toLowerCase()
  const name = String((error as any)?.name || '').toLowerCase()
  return name === 'authsessionmissingerror' || message.includes('auth session missing')
}

const logSupabaseDegradedMode = () => {
  if (hasLoggedDegradedMode) {
    return
  }

  hasLoggedDegradedMode = true
  console.warn('Supabase auth is unavailable. The app is running in guest mode.')
}

const createDegradedResponse = () =>
  new Response(JSON.stringify(DEGRADE_RESPONSE_BODY), {
    status: 503,
    headers: {
      'Content-Type': 'application/json',
    },
  })

const markSupabaseAuthDegraded = () => {
  try {
    sessionStorage.setItem(SUPABASE_DEGRADED_KEY, '1')
  } catch {
    // Ignore storage access failures in degraded mode.
  }

  logSupabaseDegradedMode()
}

const clearSupabaseAuthDegraded = () => {
  try {
    sessionStorage.removeItem(SUPABASE_DEGRADED_KEY)
  } catch {
    // Ignore storage access failures in degraded mode.
  }
}

export const hasSupabaseAuthDegraded = () => {
  try {
    return sessionStorage.getItem(SUPABASE_DEGRADED_KEY) === '1'
  } catch {
    return false
  }
}

export const clearStoredSupabaseSession = () => {
  SUPABASE_STORAGE_KEYS.forEach((key) => {
    try {
      localStorage.removeItem(key)
      sessionStorage.removeItem(key)
    } catch {
      // Ignore storage access failures in degraded mode.
    }
  })
}

if (hasSupabaseAuthDegraded()) {
  clearStoredSupabaseSession()
}

const supabaseFetch: typeof fetch = async (input, init) => {
  if (hasSupabaseAuthDegraded()) {
    return createDegradedResponse()
  }

  try {
    return await fetch(input, init)
  } catch (error) {
    if (isSupabaseNetworkError(error)) {
      markSupabaseAuthDegraded()
      clearStoredSupabaseSession()
      void supabase.auth.stopAutoRefresh()
      return createDegradedResponse()
    }

    throw error
  }
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: !hasSupabaseAuthDegraded(),
    persistSession: !hasSupabaseAuthDegraded(),
    detectSessionInUrl: !hasSupabaseAuthDegraded(),
  },
  global: {
    fetch: supabaseFetch,
  },
})

if (hasSupabaseAuthDegraded()) {
  void supabase.auth.stopAutoRefresh()
}

export const safeGetSupabaseSession = async () => {
  if (hasSupabaseAuthDegraded()) {
    return null
  }

  try {
    const { data, error } = await supabase.auth.getSession()
    if (error) {
      if (isSupabaseMissingSessionError(error)) {
        clearStoredSupabaseSession()
        return null
      }

      if (isSupabaseNetworkError(error)) {
        markSupabaseAuthDegraded()
        clearStoredSupabaseSession()
        void supabase.auth.stopAutoRefresh()
        return null
      }

      throw error
    }

    clearSupabaseAuthDegraded()
    return data.session || null
  } catch (error) {
    if (isSupabaseMissingSessionError(error)) {
      clearStoredSupabaseSession()
      return null
    }

    if (isSupabaseNetworkError(error)) {
      markSupabaseAuthDegraded()
      clearStoredSupabaseSession()
      void supabase.auth.stopAutoRefresh()
      return null
    }

    throw error
  }
}

export const safeGetSupabaseUser = async () => {
  if (hasSupabaseAuthDegraded()) {
    return null
  }

  try {
    const { data, error } = await supabase.auth.getUser()
    if (error) {
      if (isSupabaseMissingSessionError(error)) {
        clearStoredSupabaseSession()
        return null
      }

      if (isSupabaseNetworkError(error)) {
        markSupabaseAuthDegraded()
        clearStoredSupabaseSession()
        void supabase.auth.stopAutoRefresh()
        return null
      }

      throw error
    }

    clearSupabaseAuthDegraded()
    return data.user || null
  } catch (error) {
    if (isSupabaseMissingSessionError(error)) {
      clearStoredSupabaseSession()
      return null
    }

    if (isSupabaseNetworkError(error)) {
      markSupabaseAuthDegraded()
      clearStoredSupabaseSession()
      void supabase.auth.stopAutoRefresh()
      return null
    }

    throw error
  }
}

export const safeSupabaseSignOut = async () => {
  try {
    if (!hasSupabaseAuthDegraded()) {
      await supabase.auth.signOut()
    }
  } catch (error) {
    if (!isSupabaseNetworkError(error)) {
      throw error
    }
  } finally {
    clearSupabaseAuthDegraded()
    clearStoredSupabaseSession()
    void supabase.auth.stopAutoRefresh()
  }
}
