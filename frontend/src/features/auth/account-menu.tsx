import { useState } from "react"
import { Button } from "@/components/ui/button"
import { useAuth } from "./auth-context"

export function AccountMenu() {
  const { state, logout } = useAuth()
  const [pending, setPending] = useState(false)
  const [error, setError] = useState("")
  async function signOut() {
    setPending(true)
    setError("")
    try {
      await logout()
    } catch {
      setError("Unable to sign out. Please try again.")
    } finally {
      setPending(false)
    }
  }
  return (
    <div className="ml-auto flex flex-wrap items-center justify-end gap-3">
      <span className="text-sm">{state.user?.full_name}</span>
      <Button variant="outline" disabled={pending} onClick={() => void signOut()}>{pending ? "Signing out…" : "Sign out"}</Button>
      {error && <p role="alert" className="w-full text-right text-sm text-red-700">{error}</p>}
    </div>
  )
}
