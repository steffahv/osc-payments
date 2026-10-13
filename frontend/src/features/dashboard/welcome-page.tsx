import { Layers3, ShieldCheck, UsersRound } from "lucide-react"
import { AccountMenu } from "@/features/auth/account-menu"

export function WelcomePage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-6 py-5">
          <span className="flex size-10 items-center justify-center rounded-xl bg-primary text-white"><Layers3 aria-hidden="true" size={22} /></span>
          <div><p className="font-bold tracking-tight">WEB-PAYM</p><p className="text-xs text-muted-foreground">Administrative payment management</p></div>
          <AccountMenu />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-16 sm:py-24">
        <p className="text-sm font-semibold uppercase tracking-widest text-primary">A foundation for working together</p>
        <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">Your payment information,<br />all in one place.</h1>
        <p className="mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground">We are building a workspace to organize team activities and give each person access to the information they need.</p>
        <div className="mt-12 grid gap-5 sm:grid-cols-3">
          {[
            { icon: UsersRound, title: "Connected teamzzzzz2", text: "A shared workspace to organize collaboration." },
            { icon: ShieldCheck, title: "Configurable access", text: "Views and actions based on each person’s responsibilities." },
            { icon: Layers3, title: "Modular growth", text: "New capabilities as processes are defined." },
          ].map(({ icon: Icon, title, text }) => (
            <section key={title} className="rounded-xl border bg-white p-6">
              <Icon aria-hidden="true" className="text-primary" size={24} />
              <h2 className="mt-5 font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{text}</p>
            </section>
          ))}
        </div>
        <p className="mt-10 text-sm text-muted-foreground">Platform under development. Additional modules will be available in future phases.</p>
      </main>
      <footer className="mx-auto max-w-6xl border-t px-6 py-6 text-xs text-muted-foreground">WEB-PAYM · Development environment</footer>
    </div>
  )
}
