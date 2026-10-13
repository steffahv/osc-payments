// Opt-in browser integration using installed Edge and the running Vite server.
// No browser package or account credentials are required.
import assert from "node:assert/strict"
import { test } from "node:test"
import { spawn } from "node:child_process"
import { mkdtemp, readFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

test("browser authentication flow", { skip: process.env.RUN_BROWSER_TESTS !== "1", timeout: 60000 }, async () => {
  const profile = await mkdtemp(join(tmpdir(), "paym-browser-"))
  const browser = spawn(process.env.EDGE_PATH ?? "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ["--headless=new", "--disable-gpu", "--no-first-run", "--remote-debugging-port=0", "--remote-allow-origins=*",
      "--user-data-dir=" + profile, "about:blank"], { windowsHide: true, stdio: "ignore" })
  let socket
  try {
    let port
    for (let attempt = 0; attempt < 100 && !port; attempt++) {
      try { port = (await readFile(join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0] } catch { await delay(100) }
    }
    assert.ok(port, "Edge debugging port available")
    const targets = await (await fetch("http://127.0.0.1:" + port + "/json")).json()
    socket = new WebSocket(targets.find((target) => target.type === "page").webSocketDebuggerUrl)
    await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject })
    let id = 0
    const pending = new Map()
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      pending.set(++id, { resolve, reject })
      socket.send(JSON.stringify({ id, method, params }))
    })
    let mocked = process.env.REAL_BACKEND !== "1"
    let invalidLogin = true
    let signedIn = false
    let unavailable = false
    let logoutFailure = false
    const user = { id: "browser-fixture", email: "browser@example.com", full_name: "Browser Test User" }
    socket.onmessage = async ({ data }) => {
      const message = JSON.parse(data)
      if (message.id) {
        const task = pending.get(message.id)
        pending.delete(message.id)
        if (message.error) task?.reject(new Error(message.error.message))
        else task?.resolve(message.result)
      } else if (message.method === "Fetch.requestPaused") {
        const { requestId, request } = message.params
        if (!mocked) { await send("Fetch.continueRequest", { requestId }); return }
        let status = 200
        let body = user
        if (unavailable) status = 503
        else if (request.url.endsWith("/login")) {
          if (invalidLogin) status = 401
          else signedIn = true
        }
        else if (request.url.endsWith("/logout")) {
          status = logoutFailure ? 503 : 204
          if (!logoutFailure) signedIn = false
        } else if (!signedIn) status = 401
        await send("Fetch.fulfillRequest", { requestId, responseCode: status,
          responseHeaders: [{ name: "Content-Type", value: "application/json" }],
          body: Buffer.from(status === 204 ? "" : JSON.stringify(body)).toString("base64") })
      }
    }
    const evaluate = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true })).result.value
    const waitFor = async (expression) => {
      for (let attempt = 0; attempt < 100; attempt++) {
        if (await evaluate(expression)) return
        await delay(100)
      }
      assert.fail("Browser condition timed out: " + expression + "\n" +
        await evaluate("location.href + '\\n' + document.body.innerText"))
    }
    const navigate = () => send("Page.navigate", { url: "http://localhost:5173/" })
    const submit = () => evaluate(`document.querySelector('#email').value='browser@example.com';
      document.querySelector('#password').value='invalid-test-password';
      document.querySelector('form').requestSubmit()`)
    const signOut = () => evaluate("Array.from(document.querySelectorAll('button')).find(b=>b.textContent==='Sign out').click()")
    await send("Page.enable")
    await send("Fetch.enable", { patterns: [{ urlPattern: "*/api/v1/auth/*" }] })
    // REAL_BACKEND=1 checks anonymous access and invalid credentials against FastAPI.
    await navigate()
    await waitFor("location.pathname==='/login' && !!document.querySelector('#email')")
    await evaluate(`window.loginFormBeforeFocus = document.querySelector('form');
      document.querySelector('#email').value='browser@example.com';
      document.querySelector('#password').value='draft-password';
      window.dispatchEvent(new Event('blur'));
      window.dispatchEvent(new Event('focus'))`)
    await delay(500)
    assert.equal(await evaluate(`document.querySelector('form') === window.loginFormBeforeFocus &&
      document.querySelector('#email').value === 'browser@example.com' &&
      document.querySelector('#password').value === 'draft-password'`), true,
      "Switching windows preserves the login form and entered values")
    await submit()
    await waitFor("document.body.innerText.includes('Invalid email or password.')")
    // Controlled responses exercise UI state without changing database records.
    mocked = true
    invalidLogin = false
    await submit()
    await waitFor("location.pathname==='/' && document.body.innerText.includes('Browser Test User')")
    await send("Page.reload")
    await waitFor("document.body.innerText.includes('Browser Test User')")
    logoutFailure = true
    await signOut()
    await waitFor("document.body.innerText.includes('Unable to sign out.')")
    logoutFailure = false
    await signOut()
    await waitFor("location.pathname==='/login' && !!document.querySelector('#email')")
    await submit()
    await waitFor("document.body.innerText.includes('Browser Test User')")
    signedIn = false
    await evaluate("window.dispatchEvent(new Event('focus'))")
    await waitFor("location.pathname==='/login' && !!document.querySelector('#email')")
    unavailable = true
    await navigate()
    await waitFor("document.body.innerText.includes('Unable to check your session.')")
    unavailable = false
    await evaluate("document.querySelector('button').click()")
    await waitFor("!!document.querySelector('#email')")
    assert.equal(await evaluate("localStorage.length"), 0)
  } finally {
    socket?.close()
    browser.kill()
  }
})
