import { useState } from "react"
import type { FormEvent } from "react"
import { Navigate } from "react-router"
import { Button } from "@/components/ui/button"
import { ApiError } from "@/services/api"
import { useAuth } from "./auth-context"
import { SessionGate } from "./session-gate"

export function LoginPage() {
  const { state, login } = useAuth()
  const [pending, setPending] = useState(false)
  const [error, setError] = useState("")

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending) return
    const form = event.currentTarget
    const data = new FormData(form)
    setPending(true)
    setError("")
    try {
      await login(String(data.get("email")).trim(), String(data.get("password")))
      form.reset()
    } catch (error) {
      setError(error instanceof ApiError && error.status === 401
        ? "Invalid email or password."
        : error instanceof ApiError ? error.message : "Unable to connect. Please try again.")
    } finally {
      setPending(false)
    }
  }

  return (
    <SessionGate>
      {state.status === "authenticated" ? <Navigate to="/" replace /> : (
        <main className="flex min-h-screen items-center justify-center px-6 py-12">
          <section className="w-full max-w-md rounded-xl border bg-white p-8">
            <p className="font-bold text-primary">WEB-PAYM</p>
            <h1 className="mt-4 text-3xl font-semibold">Sign in</h1>
            <p className="mt-2 text-muted-foreground">Use your account to access the workspace.</p>
            <form className="mt-6 space-y-5" onSubmit={submit} aria-busy={pending}>
              <div>
                <label className="block text-sm font-medium" htmlFor="email">Email</label>
                <input className="mt-2 h-10 w-full rounded-md border px-3 focus-visible:outline-primary" id="email" name="email" type="email" autoComplete="username" required disabled={pending} />
              </div>
              <div>
                <label className="block text-sm font-medium" htmlFor="password">Password</label>
                <input className="mt-2 h-10 w-full rounded-md border px-3 focus-visible:outline-primary" id="password" name="password" type="password" autoComplete="current-password" required disabled={pending} />
              </div>
              {error && <p className="text-sm text-red-700" role="alert">{error}</p>}
              <Button className="w-full" type="submit" disabled={pending}>{pending ? "Signing in…" : "Sign in"}</Button>
            </form>
          </section>
        </main>
      )}
    </SessionGate>
  )
}
