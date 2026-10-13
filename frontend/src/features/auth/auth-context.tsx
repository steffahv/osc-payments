import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react"
import type { ReactNode } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { ApiError, apiGet, apiPost, sessionEvents } from "@/services/api"

export interface AuthUser {
  id: string
  email: string
  full_name: string
}

type AuthState =
  | { status: "loading" | "anonymous" | "error"; user: null }
  | { status: "authenticated"; user: AuthUser }

interface AuthContextValue {
  state: AuthState
  restore: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading", user: null })
  const generation = useRef(0)
  const queryClient = useQueryClient()

  const clearSession = useCallback(() => {
    generation.current++
    queryClient.clear()
    setState({ status: "anonymous", user: null })
  }, [queryClient])

  const restore = useCallback(async (background = false) => {
    const request = ++generation.current
    if (!background) setState({ status: "loading", user: null })
    try {
      const user = await apiGet<AuthUser>("/auth/me")
      if (request === generation.current) setState({ status: "authenticated", user })
    } catch (error) {
      if (request !== generation.current) return
      setState({ status: error instanceof ApiError && error.status === 401 ? "anonymous" : "error", user: null })
    }
  }, [])

  useEffect(() => {
    sessionEvents.addEventListener("expired", clearSession)
    void restore()
    return () => {
      generation.current++
      sessionEvents.removeEventListener("expired", clearSession)
    }
  }, [clearSession, restore])

  useEffect(() => {
    // Revalidate existing sessions on return, but never interrupt login form entry.
    if (state.status !== "authenticated") return
    const onFocus = () => { void restore(true) }
    window.addEventListener("focus", onFocus)
    return () => window.removeEventListener("focus", onFocus)
  }, [state.status, restore])

  async function login(email: string, password: string) {
    const request = ++generation.current
    const user = await apiPost<AuthUser>("/auth/login", { email, password })
    if (request === generation.current) {
      queryClient.clear()
      setState({ status: "authenticated", user })
    }
  }

  async function logout() {
    // Keep the session visible on failure so the user can retry server-side revocation.
    await apiPost<void>("/auth/logout")
    clearSession()
  }

  return <AuthContext.Provider value={{ state, restore, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth requires AuthProvider")
  return context
}
