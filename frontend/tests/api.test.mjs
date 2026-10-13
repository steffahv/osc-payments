import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import { test, afterEach } from "node:test"
import ts from "typescript"

// Compile the actual transport with the existing TypeScript dependency.
const source = await readFile(new URL("../src/services/api.ts", import.meta.url), "utf8")
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
})
const { apiGet, apiPost, ApiError, sessionEvents } = await import(
  "data:text/javascript;base64," + Buffer.from(outputText).toString("base64")
)
const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch })

test("login sends JSON and includes cookies without persisting tokens", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/v1/auth/login")
    assert.equal(options.credentials, "include")
    assert.equal(options.method, "POST")
    assert.equal(options.cache, "no-store")
    assert.equal(options.headers["Content-Type"], "application/json")
    assert.deepEqual(JSON.parse(options.body), { email: "user@example.com", password: "test" })
    return Response.json({ id: "1", email: "user@example.com", full_name: "Test User" })
  }
  assert.equal((await apiPost("/auth/login", { email: "user@example.com", password: "test" })).id, "1")
})

test("session restoration forwards cancellation and cookies", async () => {
  const controller = new AbortController()
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/v1/auth/me")
    assert.equal(options.credentials, "include")
    controller.abort()
    assert.equal(options.signal.aborted, true)
    return Response.json({ id: "1" })
  }
  assert.deepEqual(await apiGet("/auth/me", controller.signal), { id: "1" })
})

test("logout accepts an empty 204 response", async () => {
  globalThis.fetch = async () => new Response(null, { status: 204 })
  assert.equal(await apiPost("/auth/logout"), undefined)
})

test("401 expires authentication; invalid login does not emit expiration", async () => {
  let expired = 0
  const listener = () => { expired++ }
  sessionEvents.addEventListener("expired", listener)
  try {
    globalThis.fetch = async () => Response.json({}, { status: 401 })
    await assert.rejects(apiPost("/auth/login"), (error) => error instanceof ApiError && error.status === 401)
    assert.equal(expired, 0)
    await assert.rejects(apiGet("/auth/me"), (error) => error.status === 401)
    assert.equal(expired, 1)
  } finally {
    sessionEvents.removeEventListener("expired", listener)
  }
})

test("403 and server failures expose safe messages", async () => {
  for (const status of [403, 500]) {
    globalThis.fetch = async () => Response.json({ detail: "private server information" }, { status })
    await assert.rejects(apiGet("/example"), (error) =>
      error instanceof ApiError && error.status === status && !error.message.includes("private"))
  }
})

test("network errors remain distinguishable from an anonymous session", async () => {
  globalThis.fetch = async () => { throw new TypeError("Network failure") }
  await assert.rejects(apiGet("/auth/me"), TypeError)
})
