import { createContext, useContext, useState } from "react"
import type { ReactNode } from "react"
import { initialReceipts } from "./demo-data"
import type { DemoReceipt } from "./demo-data"

export const navigation = [
  { path: "/", label: "Dashboard", permissions: ["dashboard.view"] },
  { path: "/receipts", label: "Receipt Management", permissions: ["receipts.view"] },
  { path: "/reports", label: "Reports", permissions: ["reports.view"] },
  { path: "/master-data", label: "Master Data", permissions: ["master_data.view"] },
  { path: "/administration", label: "Administration", permissions: ["admin.users_manage", "admin.roles_manage"] },
]

// These are demo capabilities, never user roles or server authorization.
const previewPermissions = {
  workspace: navigation.flatMap(item => item.permissions).concat("receipts.create"),
  overview: ["dashboard.view", "reports.view"],
}
type Preview = keyof typeof previewPermissions
interface Workspace {
  receipts: DemoReceipt[]
  addReceipt: (receipt: DemoReceipt) => void
  preview: Preview
  setPreview: (preview: Preview) => void
  can: (permission: string) => boolean
}
const Context = createContext<Workspace | null>(null)

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [receipts, setReceipts] = useState(initialReceipts)
  const [preview, setPreview] = useState<Preview>("workspace")
  return <Context.Provider value={{ receipts, addReceipt: receipt => setReceipts(rows => [receipt, ...rows]),
    preview, setPreview, can: permission => previewPermissions[preview].includes(permission) }}>
    {children}
  </Context.Provider>
}

export function useWorkspace() {
  const context = useContext(Context)
  if (!context) throw new Error("WorkspaceProvider is required")
  return context
}
