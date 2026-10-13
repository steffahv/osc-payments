import { createBrowserRouter, Link } from "react-router"
import { WelcomePage } from "@/features/dashboard/welcome-page"

// Only a public welcome page exists. Authenticated routes arrive in Phase D.
export const router = createBrowserRouter([
  { path: "/", element: <WelcomePage /> },
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
