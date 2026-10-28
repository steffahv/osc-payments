import { demoAccounts, money } from "./demo-data"
import type { DemoReceipt } from "./demo-data"

export function ReceiptTable({ rows }: { rows: DemoReceipt[] }) {
  return <div className="overflow-x-auto">
    <table className="w-full min-w-[760px] text-left text-sm">
      <caption className="sr-only">Demo receipts. Amounts and statuses are sample data.</caption>
      <thead className="border-y bg-slate-50 text-xs uppercase tracking-wider text-muted-foreground">
        <tr>{["Receipt / Node", "Provider / Supply ID", "Due date", "Amount", "Status", "CRM"].map(title => <th key={title} scope="col" className="px-5 py-3.5 font-medium">{title}</th>)}</tr>
      </thead>
      <tbody className="divide-y">
        {rows.map(row => {
          const account = demoAccounts.find(account => account.id === row.service_account_id)
          return <tr key={row.id} className="hover:bg-slate-50/70">
            <td className="px-5 py-4"><p className="font-semibold">{row.receipt_number ?? "Unnumbered draft"}</p><p className="mt-1 text-xs text-muted-foreground">{account?.node}</p></td>
            <td className="px-5 py-4"><p>{account?.provider}</p><p className="mt-1 font-mono text-xs text-muted-foreground">{account?.supply_id}</p></td>
            <td className="whitespace-nowrap px-5 py-4 text-muted-foreground">{row.due_date ?? "—"}</td>
            <td className="whitespace-nowrap px-5 py-4 font-semibold tabular-nums">{money(row.amount)}</td>
            <td className="px-5 py-4"><span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ${row.status === "paid" ? "bg-emerald-50 text-emerald-800" : row.status === "pending" ? "bg-amber-50 text-amber-800" : "bg-slate-100 text-slate-600"}`}>{row.status}</span></td>
            <td className="px-5 py-4 text-xs capitalize text-muted-foreground">{row.status_crm}</td>
          </tr>
        })}
        {!rows.length && <tr><td colSpan={6} className="p-10 text-center text-muted-foreground">No receipts match your search.</td></tr>}
      </tbody>
    </table>
  </div>
}
