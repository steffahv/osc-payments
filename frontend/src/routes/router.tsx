import { createBrowserRouter, Link } from "react-router"
import { WelcomePage } from "@/features/dashboard/welcome-page"
import { LoginPage } from "@/features/auth/login-page"
import { ProtectedRoute } from "@/features/auth/session-gate"
import { AppShell } from "@/features/workspace/app-shell"
import { DashboardPage } from "@/features/dashboard/dashboard-page"
import { ReceiptsPage } from "@/features/receipts/receipts-page"
import { ModulePage } from "@/features/workspace/module-page"

// Authentication gates navigation; backend permissions must protect future APIs.
export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { element: <ProtectedRoute />, children: [
    { path: "/welcome", element: <WelcomePage /> },
    { element: <AppShell />, children: [
      { path: "/", element: <DashboardPage /> },
      { path: "/receipts", element: <ReceiptsPage /> },
      { path: "/reports", element: <ModulePage module="reports" /> },
      { path: "/master-data", element: <ModulePage module="master-data" /> },
      { path: "/administration", element: <ModulePage module="administration" /> },
    ] },
  ] },
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
