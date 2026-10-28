import { useState } from "react"
import type { FormEvent } from "react"
import { Plus, Search, FileText, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useWorkspace } from "@/features/workspace/workspace-context"
import { demoAccounts } from "@/features/workspace/demo-data"
import { ReceiptTable } from "@/features/workspace/receipt-table"

export function ReceiptsPage() {
  const { receipts, addReceipt, can } = useWorkspace()
  const [query, setQuery] = useState("")
  const [status, setStatus] = useState("")
  const [showForm, setShowForm] = useState(false)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const rows = receipts.filter(row => {
    const account = demoAccounts.find(account => account.id === row.service_account_id)
    return (!status || row.status === status) &&
      [row.receipt_number, account?.node, account?.provider, account?.supply_id].some(value => value?.toLowerCase().includes(query.toLowerCase()))
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const value = (name: string) => String(data.get(name) ?? "").trim() || null
    const start = value("period_start"), end = value("period_end")
    if (start && end && end < start) { setError("Period end must be on or after period start."); return }
    const amount = value("amount"), consumption = value("consumption_kwh")
    if (amount && !/^-?\d{1,16}(\.\d{1,2})?$/.test(amount)) { setError("Amount must have at most 16 integer digits and 2 decimal places."); return }
    if (consumption && !/^-?\d{1,11}(\.\d{1,3})?$/.test(consumption)) { setError("Consumption must have at most 11 integer digits and 3 decimal places."); return }
    addReceipt({
      id: crypto.randomUUID(), service_account_id: String(data.get("service_account_id")),
      receipt_number: value("receipt_number"), period_start: start, period_end: end,
      issue_date: value("issue_date"), due_date: value("due_date"), amount,
      currency_code: "PEN", status: "draft", status_crm: "pending",
      electricity_details: consumption === null ? null : { consumption_kwh: consumption },
    })
    setShowForm(false); setError(""); setQuery(""); setStatus("")
    setMessage("Demo draft added to this tab. Nothing was saved to the database.")
  }

  return <div className="space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">Data entry workspace</p>
        <h1 className="text-3xl font-semibold tracking-tight">Receipt Management</h1>
        <p className="mt-2 text-sm text-muted-foreground">Organize receipt records and prepare incomplete drafts.</p></div>
      {can("receipts.create") && <Button onClick={() => { setShowForm(true); setMessage(""); setError("") }}><Plus size={17} />New demo receipt</Button>}
    </div>
    {message && <p role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">{message}</p>}
    {showForm && can("receipts.create") && <section className="rounded-xl border bg-white p-5 shadow-sm sm:p-6" aria-labelledby="entry-title">
      <div className="flex items-start justify-between gap-4"><div><h2 id="entry-title" className="text-lg font-semibold">New demo receipt</h2>
        <p className="mt-1 text-sm text-muted-foreground">Only a service account is required. Other fields can be completed later.</p></div>
        <Button variant="outline" size="sm" aria-label="Close receipt form" onClick={() => setShowForm(false)}><X size={16} /></Button></div>
      <form className="mt-6" onSubmit={submit}>
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          <label className="field-label sm:col-span-2">Service account <span className="text-primary">*</span>
            <select className="workspace-input" name="service_account_id" required defaultValue="">
              <option value="" disabled>Select a sample service account</option>
              {demoAccounts.map(account => <option key={account.id} value={account.id}>{account.node} · Supply {account.supply_id}</option>)}
            </select>
          </label>
          <label className="field-label">Receipt number<input className="workspace-input" name="receipt_number" maxLength={100} placeholder="Optional for a draft" /></label>
          <label className="field-label">Amount (PEN)<input className="workspace-input" type="number" name="amount" step="0.01" placeholder="0.00" /></label>
          <label className="field-label">Consumption (kWh)<input className="workspace-input" type="number" name="consumption_kwh" step="0.001" placeholder="0.000" /></label>
          <div className="rounded-lg bg-slate-50 px-4 py-3 text-xs leading-6 text-muted-foreground">Currency: <strong>PEN</strong><br />New records start as <strong>draft</strong>, with CRM <strong>pending</strong>.</div>
          {(["period_start", "period_end", "issue_date", "due_date"] as const).map((field, index) =>
            <label key={field} className="field-label">{["Period start", "Period end", "Issue date", "Due date"][index]}<input className="workspace-input" type="date" name={field} /></label>)}
        </div>
        {error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t pt-5">
          <p className="text-xs text-muted-foreground">Demo only · No status changes or payment execution.</p>
          <div className="flex gap-3"><Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button><Button type="submit">Add demo draft</Button></div>
        </div>
      </form>
    </section>}
    <section className="overflow-hidden rounded-xl border bg-white shadow-sm">
      <div className="flex flex-wrap items-center gap-4 p-5">
        <div className="flex items-center gap-2 font-semibold"><FileText size={18} className="text-primary" />Receipts <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-muted-foreground">{receipts.length}</span></div>
        <div className="flex w-full flex-wrap gap-3 sm:ml-auto sm:w-auto">
          <label className="relative flex-1 sm:w-72"><span className="sr-only">Search receipts</span><Search className="pointer-events-none absolute left-3 top-3 text-muted-foreground" size={16} />
            <input className="h-10 w-full rounded-md border pl-9 pr-3 text-sm" placeholder="Search receipt, node or supply…" value={query} onChange={event => setQuery(event.target.value)} /></label>
          <label><span className="sr-only">Filter by status</span><select className="h-10 rounded-md border bg-white px-3 text-sm" value={status} onChange={event => setStatus(event.target.value)}>
            <option value="">All statuses</option><option value="draft">Draft</option><option value="pending">Pending</option><option value="paid">Paid</option>
          </select></label>
        </div>
      </div>
      <ReceiptTable rows={rows} />
      <p className="border-t px-5 py-4 text-xs text-muted-foreground">Showing {rows.length} of {receipts.length} demo receipts</p>
    </section>
  </div>
}
