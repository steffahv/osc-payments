import { useEffect, useState } from "react"
import { NavLink, Outlet, useLocation, Link } from "react-router"
import { BarChart3, Database, FileText, LayoutDashboard, Layers3, Menu, ShieldCheck, X, FlaskConical } from "lucide-react"
import { AccountMenu } from "@/features/auth/account-menu"
import { Button } from "@/components/ui/button"
import { navigation, useWorkspace, WorkspaceProvider } from "./workspace-context"

const icons = [LayoutDashboard, FileText, BarChart3, Database, ShieldCheck]

function Shell() {
  const { pathname } = useLocation()
  const { preview, setPreview, can } = useWorkspace()
  const [menuOpen, setMenuOpen] = useState(false)
  const current = navigation.find(item => item.path === pathname)
  useEffect(() => { setMenuOpen(false) }, [pathname])
  useEffect(() => {
    const close = (event: KeyboardEvent) => { if (event.key === "Escape") setMenuOpen(false) }
    window.addEventListener("keydown", close)
    return () => window.removeEventListener("keydown", close)
  }, [])
  const allowed = !current || current.permissions.some(can)

  return <div className="workspace min-h-screen bg-background">
    <a href="#workspace-main" className="sr-only focus:not-sr-only focus:fixed focus:z-50 focus:bg-white focus:p-4">Skip to content</a>
    {menuOpen && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden" onClick={() => setMenuOpen(false)} />}
    <aside id="workspace-navigation" className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-[#112f40] text-white transition-transform lg:translate-x-0 ${menuOpen ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex items-center gap-3 px-6 py-7">
        <div className="rounded-xl bg-white/10 p-2.5"><Layers3 size={25} aria-hidden="true" /></div>
        <div><p className="font-bold tracking-wide">WEB-PAYM</p><p className="text-xs text-slate-300">Payment information workspace</p></div>
        <button className="ml-auto lg:hidden" aria-label="Close menu" onClick={() => setMenuOpen(false)}><X size={20} /></button>
      </div>
      <p className="px-6 pb-3 pt-5 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Workspace</p>
      <nav aria-label="Main navigation" className="space-y-1.5 px-3">
        {navigation.map((item, index) => {
          if (!item.permissions.some(can)) return null
          const Icon = icons[index]
          return <NavLink key={item.path} to={item.path} end={item.path === "/"}
            className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-3 text-sm transition-colors ${isActive ? "bg-[#23627a] font-semibold text-white" : "text-slate-300 hover:bg-white/10 hover:text-white"}`}>
            <Icon size={19} aria-hidden="true" />{item.label}
          </NavLink>
        })}
      </nav>
      <div className="mx-4 mt-auto mb-5 rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-center gap-2 text-sm font-medium"><FlaskConical size={16} />UI preview</div>
        <p className="mt-2 text-xs leading-relaxed text-slate-300">Explore sample records. No live payment or receipt data is shown.</p>
        <Link to="/welcome" className="mt-3 inline-block text-xs text-cyan-200 underline underline-offset-4">About this workspace</Link>
      </div>
    </aside>
    <div className="lg:pl-64">
      <header className="flex flex-wrap items-center gap-3 border-b bg-white px-4 py-4 sm:px-8">
        <Button variant="outline" size="sm" className="lg:hidden" aria-label="Open navigation"
          aria-expanded={menuOpen} aria-controls="workspace-navigation" onClick={() => setMenuOpen(value => !value)}><Menu size={18} /></Button>
        <div className="text-sm text-muted-foreground">Workspace <span className="mx-2 text-slate-300">/</span><span className="font-medium text-foreground">{current?.label ?? "Overview"}</span></div>
        <AccountMenu />
      </header>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-950 sm:px-8">
        <p><strong>Demo data</strong> · Changes stay in this tab and reset on reload. No API writes.</p>
        <label className="flex items-center gap-2">Navigation preview
          <select className="rounded-md border border-amber-300 bg-white px-2 py-1.5 text-xs" value={preview}
            onChange={event => setPreview(event.target.value as typeof preview)}>
            <option value="workspace">All modules</option><option value="overview">Viewer: Dashboard &amp; Reports</option>
          </select>
        </label>
      </div>
      <main id="workspace-main" className="mx-auto max-w-[1500px] px-4 py-7 sm:px-8 sm:py-9">
        {allowed ? <Outlet /> : <section className="rounded-xl border bg-white p-8">
          <h1 className="text-2xl font-semibold">Not included in this preview</h1>
          <p className="mt-3 text-muted-foreground">The viewer preview includes Dashboard and Reports only. Data entry is separate.</p>
          <Button asChild className="mt-5"><Link to="/">Go to Dashboard</Link></Button>
        </section>}
      </main>
      <footer className="px-4 pb-6 text-xs text-muted-foreground sm:px-8">WEB-PAYM · UI foundation · Records and tracks information; does not execute payments.</footer>
    </div>
  </div>
}

export function AppShell() {
  return <WorkspaceProvider><Shell /></WorkspaceProvider>
}
