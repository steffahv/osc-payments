import { BarChart3, Database, ShieldCheck } from "lucide-react"
import { demoAccounts } from "./demo-data"

export function ModulePage({ module }: { module: "reports" | "master-data" | "administration" }) {
  const content = {
    reports: { title: "Reports", subtitle: "A dedicated space for viewing and reviewing information.", icon: BarChart3,
      items: ["Receipt summaries", "Status breakdowns", "Export reports"] },
    "master-data": { title: "Master Data", subtitle: "The reference records that connect every receipt.", icon: Database,
      items: ["Nodes", "Providers", "Service accounts"] },
    administration: { title: "Administration", subtitle: "Internal accounts and reusable role permissions.", icon: ShieldCheck,
      items: ["User management", "Role permissions", "Module access"] },
  }[module]
  const Icon = content.icon
  return <div className="space-y-6">
    <div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">Workspace foundation</p><h1 className="text-3xl font-semibold tracking-tight">{content.title}</h1><p className="mt-2 text-sm text-muted-foreground">{content.subtitle}</p></div>
    <div className="grid gap-4 md:grid-cols-3">{content.items.map(item => <section key={item} className="rounded-xl border bg-white p-6">
      <Icon className="text-primary" size={24} /><h2 className="mt-5 font-semibold">{item}</h2><p className="mt-2 text-sm text-muted-foreground">UI placeholder · Not connected</p>
    </section>)}</div>
    {module === "master-data" ? <section className="overflow-hidden rounded-xl border bg-white">
      <div className="p-5"><h2 className="font-semibold">Sample service accounts</h2><p className="mt-1 text-xs text-muted-foreground">Demo references used by the receipt entry form</p></div>
      <div className="overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead className="border-y bg-slate-50"><tr>{["Node", "Provider", "Supply ID"].map(title => <th key={title} className="px-5 py-3 font-medium">{title}</th>)}</tr></thead>
        <tbody className="divide-y">{demoAccounts.map(account => <tr key={account.id}><td className="px-5 py-4 font-medium">{account.node}</td><td className="px-5 py-4">{account.provider}</td><td className="px-5 py-4 font-mono">{account.supply_id}</td></tr>)}</tbody></table></div>
    </section> : <section className="rounded-xl border border-dashed bg-white p-8">
      <h2 className="text-lg font-semibold">{module === "reports" ? "Viewing stays separate from data entry." : "Access is controlled by explicit permissions."}</h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">{module === "reports"
        ? "This screen reserves a viewer-facing reporting area. No report generation or exports are implemented in this milestone."
        : "This preview does not create accounts, edit roles, or grant access. Live APIs continue to enforce the existing backend permissions."}</p>
    </section>}
  </div>
}
