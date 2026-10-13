import { createBrowserRouter, Link } from "react-router"
import { WelcomePage } from "@/features/dashboard/welcome-page"
import { LoginPage } from "@/features/auth/login-page"
import { ProtectedRoute } from "@/features/auth/session-gate"

// Authentication gates navigation; backend permissions must protect future APIs.
export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { element: <ProtectedRoute />, children: [{ path: "/", element: <WelcomePage /> }] },
  {
    path: "*",
    element: (
      <main className="mx-auto max-w-xl p-10">
        <h1 className="text-2xl font-semibold">Page not found</h1>
        <Link className="mt-4 inline-block underline" to="/">Back to home</Link>
      </main>
    ),
  },
])
