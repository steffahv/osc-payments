import { CircleCheck, Clock3, FileText, Wallet } from "lucide-react"
import { ReceiptTable } from "@/features/workspace/receipt-table"
import { money } from "@/features/workspace/demo-data"
import { useWorkspace } from "@/features/workspace/workspace-context"

export function DashboardPage() {
  const { receipts } = useWorkspace()
  const total = receipts.reduce((sum, receipt) => sum + Number(receipt.amount ?? 0), 0)
  const statuses = [
    { label: "Paid", value: receipts.filter(row => row.status === "paid").length, color: "bg-emerald-500" },
    { label: "Pending", value: receipts.filter(row => row.status === "pending").length, color: "bg-amber-400" },
    { label: "Draft", value: receipts.filter(row => row.status === "draft").length, color: "bg-slate-400" },
  ]
  const cards = [
    { title: "Recorded amount", value: money(total), note: "Known amounts · PEN", icon: Wallet },
    { title: "Total receipts", value: receipts.length, note: "Across 3 sample service accounts", icon: FileText },
    { title: "Pending receipts", value: statuses[1].value, note: "Recorded as pending", icon: Clock3 },
    { title: "Paid receipts", value: statuses[0].value, note: "External payment recorded", icon: CircleCheck },
  ]
  return <div className="space-y-7">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">At a glance</p><h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-2 text-sm text-muted-foreground">A clear view of your receipt records and their current status.</p></div>
      <span className="rounded-lg border bg-white px-3 py-2 text-xs text-muted-foreground">Sample portfolio · October 2026</span>
    </div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ title, value, note, icon: Icon }) => <section key={title} className="rounded-xl border bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-3"><h2 className="text-sm text-muted-foreground">{title}</h2><span className="rounded-lg bg-primary/5 p-2 text-primary"><Icon size={19} /></span></div>
        <p className="mt-4 text-3xl font-semibold tracking-tight tabular-nums">{value}</p><p className="mt-2 text-xs text-muted-foreground">{note}</p>
      </section>)}
    </div>
    <div className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
      <section className="rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="font-semibold">Receipt status</h2><p className="mt-1 text-xs text-muted-foreground">Distribution of the sample records shown below</p>
        <div className="mt-7 flex h-5 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
          {statuses.map(status => <div key={status.label} className={status.color} style={{ width: `${status.value / receipts.length * 100}%` }} />)}
        </div>
        <ul className="mt-6 space-y-4">{statuses.map(status => <li key={status.label} className="flex items-center gap-3 text-sm">
          <span className={`size-2.5 rounded-full ${status.color}`} /><span>{status.label}</span><span className="ml-auto font-semibold tabular-nums">{status.value}</span>
          <span className="w-12 text-right text-xs text-muted-foreground">{Math.round(status.value / receipts.length * 100)}%</span>
        </li>)}</ul>
      </section>
      <section className="rounded-xl border bg-[#eaf3f6] p-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-primary">Portfolio snapshot</p><h2 className="mt-4 text-xl font-semibold">Electricity, in one place.</h2>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">Follow receipt and CRM status independently, with each record linked to a service account.</p>
        <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-primary/15 pt-5">
          <div><dt className="text-xs text-muted-foreground">Utility</dt><dd className="mt-1 font-semibold">Electricity</dd></div>
          <div><dt className="text-xs text-muted-foreground">Sample providers</dt><dd className="mt-1 font-semibold">3</dd></div>
        </dl>
      </section>
    </div>
    <section className="overflow-hidden rounded-xl border bg-white shadow-sm">
      <div className="flex items-center justify-between p-5"><div><h2 className="font-semibold">Recent receipts</h2><p className="mt-1 text-xs text-muted-foreground">Sample records · newest entries first</p></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-muted-foreground">Demo</span></div>
      <ReceiptTable rows={receipts.slice(0, 5)} />
    </section>
  </div>
}
