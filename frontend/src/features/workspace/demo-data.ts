/** Fictional fixtures only. No production records or credentials. */
export const demoAccounts = [
  { id: "demo-account-1", node: "T4249_SM_SANTA LUCIA", provider: "Sample Energy North", supply_id: "001234567" },
  { id: "demo-account-2", node: "T1050_LIMA_CENTRO", provider: "Sample Energy Central", supply_id: "000987654" },
  { id: "demo-account-3", node: "T3081_SUR_ESTACION", provider: "Sample Energy South", supply_id: "005678901" },
]

export interface DemoReceipt {
  id: string
  service_account_id: string
  receipt_number: string | null
  period_start: string | null
  period_end: string | null
  issue_date: string | null
  due_date: string | null
  amount: string | null
  currency_code: string
  status: "draft" | "pending" | "paid"
  status_crm: "pending" | "registered"
  electricity_details: { consumption_kwh: string | null } | null
}

export const initialReceipts: DemoReceipt[] = [
  ["demo-1", "demo-account-1", "REC-2026-041", "1245.80", "pending", "registered", "2026-10-30"],
  ["demo-2", "demo-account-2", "REC-2026-042", "860.50", "paid", "registered", "2026-10-22"],
  ["demo-3", "demo-account-3", "REC-2026-043", "2130.00", "pending", "pending", "2026-11-02"],
  ["demo-4", "demo-account-1", null, null, "draft", "pending", null],
  ["demo-5", "demo-account-2", "REC-2026-045", "975.20", "paid", "registered", "2026-10-25"],
  ["demo-6", "demo-account-3", "REC-2026-046", "540.00", "draft", "pending", "2026-11-05"],
].map(([id, account, number, amount, status, crm, due]) => ({
  id: id!, service_account_id: account!, receipt_number: number, amount,
  status: status as DemoReceipt["status"], status_crm: crm as DemoReceipt["status_crm"],
  due_date: due, currency_code: "PEN", period_start: "2026-10-01", period_end: "2026-10-31",
  issue_date: "2026-10-20", electricity_details: null,
}))

export function money(amount: string | number | null) {
  return amount === null ? "—" : new Intl.NumberFormat("en-US", { style: "currency", currency: "PEN" }).format(Number(amount))
}
