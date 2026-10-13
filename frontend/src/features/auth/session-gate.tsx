import type { ReactNode } from "react"
import { Navigate, Outlet } from "react-router"
import { Button } from "@/components/ui/button"
import { useAuth } from "./auth-context"

export function SessionGate({ children }: { children: ReactNode }) {
  const { state, restore } = useAuth()
  if (state.status === "loading") return <main className="p-10" role="status">Checking your session…</main>
  if (state.status === "error") return (
    <main className="mx-auto max-w-md space-y-4 p-10">
      <p role="alert">Unable to check your session. Please try again.</p>
      <Button onClick={() => void restore()}>Retry</Button>
    </main>
  )
  return children
}

export function ProtectedRoute() {
  const { state } = useAuth()
  return <SessionGate>{state.status === "authenticated" ? <Outlet /> : <Navigate to="/login" replace />}</SessionGate>
}
